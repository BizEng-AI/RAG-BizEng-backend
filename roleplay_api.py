# roleplay_api.py
"""
FastAPI endpoints for the roleplay feature.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from roleplay_session import (
    create_session, load_session, save_session, delete_session, list_user_sessions
)
from roleplay_scenarios import list_scenarios, get_scenario
from roleplay_engine import engine
from tracking import track
from deps import get_optional_user
from db import get_db


router = APIRouter(prefix="/roleplay", tags=["roleplay"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class StartSessionRequest(BaseModel):
    scenario_id: str
    student_name: Optional[str] = None


class StartSessionResponse(BaseModel):
    session_id: str
    scenario_title: str
    scenario_description: str
    context: str
    student_role: str
    ai_role: str
    current_stage: str  # Android expects "current_stage" not "stage_info"
    initial_message: str


class TurnRequest(BaseModel):
    session_id: str
    message: str


class TurnResponse(BaseModel):
    ai_message: str
    correction: Optional[Dict[str, Any]]
    current_stage: str  # Android expects "current_stage" not "stage_info"
    is_completed: bool
    feedback: Optional[str] = None  # Android expects "feedback" field


class HintRequest(BaseModel):
    session_id: str


class HintResponse(BaseModel):
    hint: str
    hints_used: int


class SessionInfoResponse(BaseModel):
    session_id: str
    scenario_id: str
    scenario_title: str
    student_name: Optional[str]
    current_stage: int
    total_stages: int
    started_at: str
    updated_at: str
    is_completed: bool
    dialogue_history: List[Dict[str, Any]]
    corrections_count: int
    hints_used: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/scenarios")
def get_scenarios(difficulty: Optional[str] = None):
    """
    List all available roleplay scenarios.
    Optional filter by difficulty: beginner, intermediate, advanced
    """
    try:
        scenarios = list_scenarios(difficulty=difficulty)
        return {"scenarios": scenarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenarios: {str(e)}")


@router.get("/scenarios/{scenario_id}")
def get_scenario_details(scenario_id: str):
    """Get detailed information about a specific scenario"""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    return {
        "id": scenario.id,
        "title": scenario.title,
        "description": scenario.description,
        "difficulty": scenario.difficulty,
        "context": scenario.context,
        "student_role": scenario.student_role,
        "ai_role": scenario.ai_role,
        "stages": [
            {
                "name": stage.name,
                "objective": stage.objective,
                "hints_available": len(stage.hints)
            }
            for stage in scenario.stages
        ]
    }


@router.post("/start", response_model=StartSessionResponse)
def start_roleplay(req: StartSessionRequest, user = Depends(get_optional_user), db = Depends(get_db)):
    """
    Start a new roleplay session.
    Returns session info and AI's opening message.
    """
    from routers.tracking import create_attempt_internal
    from datetime import datetime

    try:
        scenario = get_scenario(req.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {req.scenario_id}")

        # Create session
        session = create_session(req.scenario_id, req.student_name)

        # Create attempt record
        if user:
            try:
                attempt = create_attempt_internal(
                    db=db,
                    user_id=user.id,
                    exercise_type="roleplay",
                    exercise_id=session.session_id,
                    extra_metadata={
                        "scenario_id": req.scenario_id,
                        "scenario_title": scenario.title
                    }
                )
                session.attempt_id = attempt.id  # Store for later
                print(f"[roleplay] Created attempt ID: {attempt.id} for session {session.session_id}", flush=True)
            except Exception as e:
                print(f"[roleplay] Warning: Failed to create attempt: {e}", flush=True)

        # Generate opening message from AI
        first_stage = scenario.stages[0]
        initial_message = _generate_opening_message(scenario, first_stage)

        # Save AI's opening message to session
        session.add_turn("ai", initial_message)
        save_session(session)

        # Instrument: roleplay started
        try:
            uid = user.id if user else None
            track(uid, "started_roleplay", feature="roleplay", scenario_id=req.scenario_id)
        except Exception:
            pass

        return StartSessionResponse(
            session_id=session.session_id,
            scenario_title=scenario.title,
            scenario_description=scenario.description,
            context=scenario.context,
            student_role=scenario.student_role,
            ai_role=scenario.ai_role,
            current_stage=first_stage.name,  # Return stage name (string) not index (int)
            initial_message=initial_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/turn", response_model=TurnResponse)
def submit_turn(req: TurnRequest, user = Depends(get_optional_user), db = Depends(get_db)):
    """
    Submit student's message and get AI's response with feedback.
    """
    from routers.tracking import finish_attempt_internal
    from datetime import datetime

    # Log request details for debugging
    user_info = f"user_id={user.id}" if user else "anonymous"
    print(f"[roleplay/turn] Request from {user_info}, session={req.session_id}", flush=True)

    try:
        # Load session with detailed logging
        print(f"[roleplay/turn] Loading session {req.session_id}...", flush=True)
        session = load_session(req.session_id)

        if not session:
            print(f"[roleplay/turn] âŒ Session not found: {req.session_id}", flush=True)
            raise HTTPException(status_code=404, detail=f"Session not found: {req.session_id}")

        print(f"[roleplay/turn] âœ“ Session loaded (scenario: {session.scenario_id})", flush=True)

        if session.is_completed:
            print(f"[roleplay/turn] Session already completed", flush=True)
            return TurnResponse(
                ai_message="This roleplay session has been completed. Great job!",
                correction=None,
                current_stage=session.current_stage,
                is_completed=True
            )

        # Validate message
        if not req.message or len(req.message.strip()) < 2:
            raise HTTPException(status_code=400, detail="Message is too short")

        print(f"[roleplay/turn] Processing message: '{req.message[:50]}...'", flush=True)

        # Instrument: student sent a message
        try:
            uid = user.id if user else None
            track(uid, "roleplay_turn_submitted", feature="roleplay", session_id=req.session_id, message_length=len(req.message))
        except Exception as e:
            print(f"[roleplay/turn] Warning: track() failed: {e}", flush=True)

        # Process turn through engine (this calls Azure - may timeout)
        try:
            print(f"[roleplay/turn] Calling roleplay engine...", flush=True)
            result = engine.process_turn(session, req.message)
            print(f"[roleplay/turn] âœ“ Engine returned response", flush=True)
        except Exception as e:
            print(f"[roleplay/turn] âŒ Engine error: {type(e).__name__}: {e}", flush=True)
            raise HTTPException(status_code=500, detail=f"Roleplay engine error: {str(e)}")

        # If session just completed, finish the attempt
        if result["is_completed"] and user and hasattr(session, 'attempt_id'):
            try:
                # Parse started_at from ISO string to datetime
                from datetime import datetime
                if isinstance(session.started_at, str):
                    started = datetime.fromisoformat(session.started_at.replace('Z', '+00:00'))
                else:
                    started = session.started_at
                duration = int((datetime.utcnow() - started).total_seconds())

                finish_attempt_internal(
                    db=db,
                    attempt_id=session.attempt_id,
                    duration_seconds=duration,
                    score=None,  # Could calculate based on corrections in future
                    passed=True,  # Completed the roleplay
                    extra_metadata={
                        "total_turns": len(session.dialogue_history),
                        "corrections_count": len(session.corrections_log) if hasattr(session, 'corrections_log') else 0
                    }
                )
                print(f"[roleplay] âœ… Attempt {session.attempt_id} finished - Duration: {duration}s, Turns: {len(session.dialogue_history)}", flush=True)
            except Exception as e:
                print(f"[roleplay] Warning: Failed to finish attempt: {e}", flush=True)

        # Convert correction format from OLD to NEW format for Android
        correction = result["correction"]
        if correction:
            # OLD format from referee: {error_type, original, corrected, explanation, priority}
            # NEW format for Android: {has_errors: true, errors: [{type, incorrect, correct, explanation}], feedback}
            converted_correction = {
                "has_errors": True,
                "errors": [{
                    "type": correction.get("error_type", "grammar"),
                    "incorrect": correction.get("original", ""),
                    "correct": correction.get("corrected", ""),
                    "explanation": correction.get("explanation", "")
                }],
                "feedback": f"Priority: {correction.get('priority', 'medium')}. Keep practicing!"
            }
        else:
            converted_correction = {
                "has_errors": False,
                "errors": [],
                "feedback": "Great job! Your response was appropriate."
            }

        # Instrument: AI replied
        try:
            uid = user.id if user else None
            track(uid, "roleplay_ai_response", feature="roleplay", session_id=req.session_id, ai_message_length=len(result.get('ai_message','')))
        except Exception:
            pass

        return TurnResponse(
            ai_message=result["ai_message"],
            correction=converted_correction,
            current_stage=result["current_stage"],  # Changed from stage_info to current_stage
            is_completed=result["is_completed"],
            feedback=result.get("feedback")  # Added feedback field
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process turn: {str(e)}")


@router.post("/hint", response_model=HintResponse)
def get_hint(req: HintRequest):
    """
    Get a hint for the current stage without advancing.
    """
    try:
        session = load_session(req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {req.session_id}")

        if session.is_completed:
            return HintResponse(
                hint="You've completed this roleplay. Well done!",
                hints_used=session.hints_used
            )

        hint = engine.get_hint(session)

        return HintResponse(
            hint=hint,
            hints_used=session.hints_used
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hint: {str(e)}")


@router.get("/session/{session_id}", response_model=SessionInfoResponse)
def get_session_info(session_id: str):
    """
    Get detailed information about a session.
    """
    try:
        session = load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        scenario = get_scenario(session.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

        return SessionInfoResponse(
            session_id=session.session_id,
            scenario_id=session.scenario_id,
            scenario_title=scenario.title,
            student_name=session.student_name,
            current_stage=session.current_stage,
            total_stages=len(scenario.stages),
            started_at=session.started_at,
            updated_at=session.updated_at,
            is_completed=session.is_completed,
            dialogue_history=[
                {
                    "speaker": turn.speaker,
                    "message": turn.message,
                    "timestamp": turn.timestamp,
                    "correction": turn.correction
                }
                for turn in session.dialogue_history
            ],
            corrections_count=len(session.corrections_log),
            hints_used=session.hints_used
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


@router.delete("/session/{session_id}")
def delete_session_endpoint(session_id: str):
    """Delete a roleplay session"""
    try:
        session = load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        delete_session(session_id)
        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get("/sessions")
def list_sessions(student_name: Optional[str] = None, active_only: bool = False):
    """
    List all sessions, optionally filtered by student name or active status.
    """
    try:
        sessions = list_user_sessions(student_name=student_name, active_only=active_only)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_opening_message(scenario, first_stage) -> str:
    """Generate the AI's opening message for the roleplay"""

    openings = {
        "modern_zoo": "Hi. We have been reading about modern zoos in class. Do you think zoos still have an important role today?",
        "education_systems": "Hello. I am curious about your education system. Could you tell me how it works and what students usually study?",
        "university_life": "Hi. I have just started university and everything feels new. What is university life really like for you?",
        "english_learning_games": "Hello. I want to improve my English outside class. What kinds of games, videos, or other materials actually help?",
        "festivals_and_traditions": "Hi. I would love to hear about a festival or tradition that is important in your culture. Which one would you choose?",
        "personal_finance": "Hello. I am trying to manage my monthly budget better. Where should I start if I want to control my spending?",
        "trade_and_markets": "Hi. We studied supply and demand today, but I still want practice explaining it. Can you describe a simple market change for me?"
    }

    return openings.get(scenario.id, f"Hello. Let's begin the {scenario.title} practice together.")

