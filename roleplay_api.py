# roleplay_api.py
"""
FastAPI endpoints for the roleplay feature.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from roleplay_session import (
    create_session, load_session, save_session, delete_session, list_user_sessions
)
from roleplay_scenarios import list_scenarios, get_scenario
from roleplay_engine import engine
from tracking import track
from deps import require_student
from db import get_db
from models import ExerciseAttempt
from usage_limits import consume_ai_units


router = APIRouter(prefix="/roleplay", tags=["roleplay"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class StartSessionRequest(BaseModel):
    scenario_id: str
    student_name: Optional[str] = None
    use_rag: Optional[bool] = True


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


def _allow_or_verify_session_access(session, user, adopt_if_authenticated: bool = False):
    if session.owner_user_id is None:
        if adopt_if_authenticated and user is not None:
            session.owner_user_id = user.id
            save_session(session)
        return session

    if user is None or session.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this session")

    return session


def _count_words(text: str) -> int:
    return len([part for part in text.strip().split() if part])


def _session_duration_seconds(session) -> int:
    try:
        started = datetime.fromisoformat(str(session.started_at).replace("Z", "+00:00"))
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        return max(1, int((datetime.now(timezone.utc) - started).total_seconds()))
    except Exception:
        return 1


def _update_roleplay_attempt(db, session, scenario=None, status: str = "in_progress") -> None:
    attempt_id = getattr(session, "attempt_id", None)
    if not attempt_id:
        return

    attempt = db.get(ExerciseAttempt, attempt_id)
    if not attempt:
        return

    student_turns = [turn for turn in session.dialogue_history if turn.speaker == "student"]
    metadata = attempt.extra_metadata or {}
    metadata.update(
        {
            "status": "completed" if session.is_completed else status,
            "scenario_id": session.scenario_id,
            "scenario_title": scenario.title if scenario else metadata.get("scenario_title"),
            "message_count": len(student_turns),
            "word_count": sum(_count_words(turn.message) for turn in student_turns),
            "total_turns": len(session.dialogue_history),
            "hints_used": session.hints_used,
            "corrections_count": len(session.corrections_log),
            "last_activity_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    attempt.duration_seconds = _session_duration_seconds(session)
    attempt.extra_metadata = metadata
    if session.is_completed and attempt.finished_at is None:
        attempt.finished_at = datetime.now(timezone.utc)
        attempt.passed = True
    db.commit()


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
def start_roleplay(req: StartSessionRequest, user = Depends(require_student), db = Depends(get_db)):
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
        session = create_session(
            req.scenario_id,
            req.student_name,
            use_rag=bool(req.use_rag),
            owner_user_id=user.id,
        )

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
                        "scenario_title": scenario.title,
                        "use_rag": bool(req.use_rag),
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
            track(user.id, "started_roleplay", feature="roleplay", scenario_id=req.scenario_id)
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
def submit_turn(req: TurnRequest, user = Depends(require_student), db = Depends(get_db)):
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
            print(f"[roleplay/turn] FAIL Session not found: {req.session_id}", flush=True)
            raise HTTPException(status_code=404, detail=f"Session not found: {req.session_id}")

        session = _allow_or_verify_session_access(session, user, adopt_if_authenticated=True)
        print(f"[roleplay/turn] OK Session loaded (scenario: {session.scenario_id})", flush=True)

        if session.is_completed:
            print(f"[roleplay/turn] Session already completed", flush=True)
            # Resolve stage name from the scenario for the response
            from roleplay_scenarios import get_scenario as _get_scenario
            _sc = _get_scenario(session.scenario_id)
            _stage_name = "completed"
            if _sc and _sc.stages:
                _stage_name = _sc.stages[-1].name
            return TurnResponse(
                ai_message="This roleplay session has been completed. Great job!",
                correction=None,
                current_stage=_stage_name,
                is_completed=True,
                feedback="Session already completed.",
            )

        # Validate message
        if not req.message or len(req.message.strip()) < 2:
            raise HTTPException(status_code=400, detail="Message is too short")

        print(f"[roleplay/turn] Processing message_length={len(req.message)}", flush=True)
        consume_ai_units(
            db,
            user_id=user.id,
            route="roleplay_turn",
            extra_metadata={"session_id": req.session_id, "message_length": len(req.message)},
        )

        # Instrument: student sent a message
        try:
            track(user.id, "roleplay_turn_submitted", feature="roleplay", session_id=req.session_id, message_length=len(req.message))
        except Exception as e:
            print(f"[roleplay/turn] Warning: track() failed: {e}", flush=True)

        # Process turn through engine (this calls Azure - may timeout)
        try:
            print(f"[roleplay/turn] Calling roleplay engine...", flush=True)
            result = engine.process_turn(session, req.message)
            print(f"[roleplay/turn] OK Engine returned response", flush=True)
        except Exception as e:
            print(f"[roleplay/turn] FAIL Engine error: {type(e).__name__}: {e}", flush=True)
            raise HTTPException(status_code=500, detail=f"Roleplay engine error: {str(e)}")

        scenario = get_scenario(session.scenario_id)
        try:
            _update_roleplay_attempt(db, session, scenario=scenario)
        except Exception as e:
            print(f"[roleplay] Warning: Failed to update attempt stats: {e}", flush=True)

        # If session just completed, finish the attempt
        if result["is_completed"] and user and getattr(session, "attempt_id", None):
            try:
                # Parse started_at from ISO string to datetime
                from datetime import datetime, timezone
                if isinstance(session.started_at, str):
                    started = datetime.fromisoformat(session.started_at.replace('Z', '+00:00'))
                else:
                    started = session.started_at
                duration = int((datetime.now(timezone.utc) - started).total_seconds())

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
                print(f"[roleplay] OK Attempt {session.attempt_id} finished - Duration: {duration}s, Turns: {len(session.dialogue_history)}", flush=True)
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
                "feedback": "Use the corrected phrasing and keep your sentence clear.",
                "severity": correction.get("priority", "medium"),
            }
        else:
            converted_correction = {
                "has_errors": False,
                "errors": [],
                "feedback": None
            }

        # Instrument: AI replied
        try:
            track(user.id, "roleplay_ai_response", feature="roleplay", session_id=req.session_id, ai_message_length=len(result.get('ai_message','')))
        except Exception:
            pass

        return TurnResponse(
            ai_message=result["ai_message"],
            correction=converted_correction,
            current_stage=result["current_stage"],
            is_completed=result["is_completed"],
            feedback=converted_correction.get("feedback"),
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process turn: {str(e)}")


@router.post("/hint", response_model=HintResponse)
def get_hint(req: HintRequest, user = Depends(require_student), db = Depends(get_db)):
    """
    Get a hint for the current stage without advancing.
    """
    try:
        session = load_session(req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {req.session_id}")

        session = _allow_or_verify_session_access(session, user, adopt_if_authenticated=True)
        if session.is_completed:
            return HintResponse(
                hint="You've completed this roleplay. Well done!",
                hints_used=session.hints_used
            )

        consume_ai_units(
            db,
            user_id=user.id,
            route="roleplay_hint",
            extra_metadata={"session_id": req.session_id},
        )
        hint = engine.get_hint(session)
        scenario = get_scenario(session.scenario_id)
        try:
            _update_roleplay_attempt(db, session, scenario=scenario, status="hint_used")
            track(user.id, "roleplay_hint_used", feature="roleplay", session_id=req.session_id, scenario_id=session.scenario_id)
        except Exception:
            pass

        return HintResponse(
            hint=hint,
            hints_used=session.hints_used
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hint: {str(e)}")


@router.get("/session/{session_id}", response_model=SessionInfoResponse)
def get_session_info(session_id: str, user = Depends(require_student)):
    """
    Get detailed information about a session.
    """
    try:
        session = load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        session = _allow_or_verify_session_access(session, user, adopt_if_authenticated=True)
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
def delete_session_endpoint(session_id: str, user = Depends(require_student)):
    """Delete a roleplay session"""
    try:
        session = load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        _allow_or_verify_session_access(session, user, adopt_if_authenticated=True)
        delete_session(session_id)
        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get("/sessions")
def list_sessions(student_name: Optional[str] = None, active_only: bool = False, user = Depends(require_student)):
    """
    List all sessions, optionally filtered by student name or active status.
    """
    try:
        sessions = list_user_sessions(
            student_name=student_name,
            active_only=active_only,
            owner_user_id=user.id
        )
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_opening_message(scenario, first_stage) -> str:
    """Generate the AI's opening message for the roleplay"""

    openings = {
        "corporate_travel_planning": "Hello. We need to plan a 3-day business trip and stay within the company budget. Which option would you start with?",
        "personal_finance": "Hello. I am trying to manage my monthly budget better. Where should I start if I want to control my spending?",
        "basic_economic_concepts": "Hi. Let us explain an economic idea clearly. How would you describe inflation or consumer choice in simple English?",
        "supply_and_demand": "Hello. We studied supply and demand today. What usually happens when demand rises but supply stays low?",
        "trade_and_markets": "Hi. We studied supply and demand today, but I still want practice explaining it. Can you describe a simple market change for me?",
        "trans_siberian_route": "Hello. Let's plan an export shipment using the Trans-Siberian route. What should we check first?",
        "transport_mode_comparison": "Hi. We need to choose between rail, sea, and air freight. Which option fits this delivery best?",
        "delivery_delay_handling": "Hello. A shipment is delayed and the client is worried. How would you give this update politely?",
        "customs_risk_briefing": "Hello. Before we approve this shipment, could you tell me the main customs and document risks?",
        "international_business_meeting": "Hi everyone. Before we start, could you open this meeting and confirm the agenda?",
        "contract_negotiation": "Hello. We are close to an agreement, but price and timeline still need negotiation. What would you propose?",
        "follow_up_email_summary": "Hello. The meeting has ended. How would you summarize the main decisions and next steps in a follow-up message?",
        "business_and_work": "Hi. Let us talk about business and work. Which workplace skill do you think matters most and why?",
        "entrepreneur_pitch": "Hello. Please introduce your business idea briefly. What problem does it solve for the customer?",
        "customer_complaint_response": "Hello. I am unhappy because my order arrived late and one item is missing. What can you do about this?",
        "team_task_update": "Hi. Could you give me a quick update on your task? What is finished, and what is still blocked?"
    }

    return openings.get(scenario.id, f"Hello. Let's begin the {scenario.title} practice together.")

