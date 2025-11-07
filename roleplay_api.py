# roleplay_api.py
"""
FastAPI endpoints for the roleplay feature.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from roleplay_session import (
    create_session, load_session, save_session, delete_session, list_user_sessions
)
from roleplay_scenarios import list_scenarios, get_scenario
from roleplay_engine import engine


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
def start_roleplay(req: StartSessionRequest):
    """
    Start a new roleplay session.
    Returns session info and AI's opening message.
    """
    try:
        scenario = get_scenario(req.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Scenario not found: {req.scenario_id}")

        # Create session
        session = create_session(req.scenario_id, req.student_name)

        # Generate opening message from AI
        first_stage = scenario.stages[0]
        initial_message = _generate_opening_message(scenario, first_stage)

        # Save AI's opening message to session
        session.add_turn("ai", initial_message)
        save_session(session)

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
def submit_turn(req: TurnRequest):
    """
    Submit student's message and get AI's response with feedback.
    """
    try:
        # Load session
        session = load_session(req.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {req.session_id}")

        if session.is_completed:
            return TurnResponse(
                ai_message="This roleplay session has been completed. Great job!",
                correction=None,
                current_stage=session.current_stage,  # Changed from stage_info to current_stage
                is_completed=True
            )

        # Validate message
        if not req.message or len(req.message.strip()) < 2:
            raise HTTPException(status_code=400, detail="Message is too short")

        # Process turn through engine
        result = engine.process_turn(session, req.message)

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
        "job_interview": "Good morning! Thank you for coming in today. Please, have a seat. I'm looking forward to learning more about you and your experience. Shall we get started?",
        "client_meeting": "Hello! Thank you for taking the time to meet with me today. I appreciate the opportunity to discuss how we might work together. How has your day been so far?",
        "customer_complaint": "*phone rings* Hello, thank you for calling Customer Service. My name is Sarah. I understand you're calling about an issue with your order. I'm here to help. Could you tell me what happened?",
        "team_meeting": "Good morning, everyone. Thanks for making time for this meeting. As you know, we're here to discuss our project timeline. I'd like to start by reviewing where we are and then hear your thoughts. Sound good?",
        "business_call": "Good morning, this is Tech Supplies, Maria speaking. How may I help you today?"
    }

    return openings.get(scenario.id, f"Hello! I'm ready to begin this {scenario.title} roleplay with you. Let's get started!")
