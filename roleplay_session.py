# roleplay_session.py
"""
Manages roleplay sessions with 3-tier memory system:
- Short-term: Last 4-6 dialogue turns
- Mid-term: Episode summaries (compressed every 3-4 turns)
- Long-term: User's common mistakes and corrections
"""
from __future__ import annotations
import uuid
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

from roleplay_scenarios import Scenario, get_scenario


@dataclass
class DialogueTurn:
    """Single turn in the conversation"""
    speaker: str  # "student" or "ai"
    message: str
    timestamp: str
    correction: Optional[Dict[str, str]] = None  # {"type": "grammar", "original": "...", "fixed": "...", "explanation": "..."}


@dataclass
class EpisodeSummary:
    """Compressed summary of 3-4 turns"""
    turn_range: str  # e.g., "1-4"
    key_points: List[str]
    student_performance: str  # brief note on how student is doing
    timestamp: str


@dataclass
class Correction:
    """A correction made during the session"""
    turn_number: int
    error_type: str  # "grammar", "register", "vocabulary", "pragmatic"
    original: str
    corrected: str
    explanation: str
    timestamp: str


@dataclass
class RoleplaySession:
    """Complete session state"""
    session_id: str
    scenario_id: str
    student_name: Optional[str]
    current_stage: int  # index in scenario.stages
    started_at: str
    updated_at: str

    # Memory layers
    dialogue_history: List[DialogueTurn] = field(default_factory=list)
    episode_summaries: List[EpisodeSummary] = field(default_factory=list)
    corrections_log: List[Correction] = field(default_factory=list)

    # State
    is_completed: bool = False
    hints_used: int = 0
    stage_attempts: Dict[str, int] = field(default_factory=dict)  # track attempts per stage

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "scenario_id": self.scenario_id,
            "student_name": self.student_name,
            "current_stage": self.current_stage,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "dialogue_history": [asdict(t) for t in self.dialogue_history],
            "episode_summaries": [asdict(e) for e in self.episode_summaries],
            "corrections_log": [asdict(c) for c in self.corrections_log],
            "is_completed": self.is_completed,
            "hints_used": self.hints_used,
            "stage_attempts": self.stage_attempts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RoleplaySession:
        """Create session from dictionary"""
        return cls(
            session_id=data["session_id"],
            scenario_id=data["scenario_id"],
            student_name=data.get("student_name"),
            current_stage=data["current_stage"],
            started_at=data["started_at"],
            updated_at=data["updated_at"],
            dialogue_history=[DialogueTurn(**t) for t in data.get("dialogue_history", [])],
            episode_summaries=[EpisodeSummary(**e) for e in data.get("episode_summaries", [])],
            corrections_log=[Correction(**c) for c in data.get("corrections_log", [])],
            is_completed=data.get("is_completed", False),
            hints_used=data.get("hints_used", 0),
            stage_attempts=data.get("stage_attempts", {})
        )

    def get_short_term_memory(self, window: int = 6) -> List[DialogueTurn]:
        """Get last N turns for immediate context"""
        return self.dialogue_history[-window:] if self.dialogue_history else []

    def get_recent_corrections(self, limit: int = 3) -> List[Correction]:
        """Get most recent corrections"""
        return self.corrections_log[-limit:] if self.corrections_log else []

    def add_turn(self, speaker: str, message: str, correction: Optional[Dict[str, str]] = None):
        """Add a dialogue turn"""
        turn = DialogueTurn(
            speaker=speaker,
            message=message,
            timestamp=datetime.utcnow().isoformat(),
            correction=correction
        )
        self.dialogue_history.append(turn)
        self.updated_at = datetime.utcnow().isoformat()

        # Check if we should create an episode summary
        if len(self.dialogue_history) % 8 == 0:  # Every 8 turns (4 exchanges)
            self._create_episode_summary()

    def add_correction(self, error_type: str, original: str, corrected: str, explanation: str):
        """Log a correction"""
        correction = Correction(
            turn_number=len(self.dialogue_history),
            error_type=error_type,
            original=original,
            corrected=corrected,
            explanation=explanation,
            timestamp=datetime.utcnow().isoformat()
        )
        self.corrections_log.append(correction)

    def _create_episode_summary(self):
        """Create a compressed summary of recent turns"""
        # Get the last unsummarized turns
        last_summary_end = 0
        if self.episode_summaries:
            last_range = self.episode_summaries[-1].turn_range
            last_summary_end = int(last_range.split("-")[1])

        start_idx = last_summary_end
        end_idx = len(self.dialogue_history)

        if end_idx - start_idx < 4:  # Need at least 4 turns to summarize
            return

        turns_to_summarize = self.dialogue_history[start_idx:end_idx]

        # Extract key points (simple extraction for now)
        key_points = []
        for turn in turns_to_summarize:
            if turn.speaker == "student":
                snippet = turn.message[:100] + "..." if len(turn.message) > 100 else turn.message
                key_points.append(f"Student: {snippet}")

        # Performance note based on corrections
        recent_corrections = [c for c in self.corrections_log if c.turn_number >= start_idx]
        if len(recent_corrections) == 0:
            performance = "Good - no major errors"
        elif len(recent_corrections) <= 2:
            performance = "Fair - minor issues corrected"
        else:
            performance = "Needs improvement - several corrections needed"

        summary = EpisodeSummary(
            turn_range=f"{start_idx + 1}-{end_idx}",
            key_points=key_points[:3],  # Keep top 3
            student_performance=performance,
            timestamp=datetime.utcnow().isoformat()
        )
        self.episode_summaries.append(summary)

    def advance_stage(self):
        """Move to next stage"""
        scenario = get_scenario(self.scenario_id)
        if scenario and self.current_stage < len(scenario.stages) - 1:
            self.current_stage += 1
            self.updated_at = datetime.utcnow().isoformat()
            return True
        elif scenario and self.current_stage == len(scenario.stages) - 1:
            # Last stage completed
            self.is_completed = True
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def record_stage_attempt(self, stage_name: str):
        """Track how many attempts at current stage"""
        if stage_name not in self.stage_attempts:
            self.stage_attempts[stage_name] = 0
        self.stage_attempts[stage_name] += 1

    def get_current_stage_info(self) -> Optional[Dict[str, Any]]:
        """Get info about current stage"""
        scenario = get_scenario(self.scenario_id)
        if not scenario or self.current_stage >= len(scenario.stages):
            return None

        stage = scenario.stages[self.current_stage]
        return {
            "stage_number": self.current_stage + 1,
            "total_stages": len(scenario.stages),
            "stage_name": stage.name,
            "objective": stage.objective,
            "attempts": self.stage_attempts.get(stage.name, 0)
        }


# ============================================================================
# SESSION PERSISTENCE
# ============================================================================

SESSIONS_DIR = Path(__file__).parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


def create_session(scenario_id: str, student_name: Optional[str] = None) -> RoleplaySession:
    """Create a new roleplay session"""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    session = RoleplaySession(
        session_id=str(uuid.uuid4()),
        scenario_id=scenario_id,
        student_name=student_name,
        current_stage=0,
        started_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )

    save_session(session)
    return session


def save_session(session: RoleplaySession):
    """Save session to disk"""
    filepath = SESSIONS_DIR / f"{session.session_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)


def load_session(session_id: str) -> Optional[RoleplaySession]:
    """Load session from disk"""
    filepath = SESSIONS_DIR / f"{session_id}.json"
    if not filepath.exists():
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return RoleplaySession.from_dict(data)


def delete_session(session_id: str):
    """Delete a session"""
    filepath = SESSIONS_DIR / f"{session_id}.json"
    if filepath.exists():
        filepath.unlink()


def list_user_sessions(student_name: Optional[str] = None, active_only: bool = False) -> List[Dict[str, Any]]:
    """List all sessions, optionally filtered"""
    sessions = []
    for filepath in SESSIONS_DIR.glob("*.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Apply filters
        if student_name and data.get("student_name") != student_name:
            continue
        if active_only and data.get("is_completed"):
            continue

        scenario = get_scenario(data["scenario_id"])
        sessions.append({
            "session_id": data["session_id"],
            "scenario_id": data["scenario_id"],
            "scenario_title": scenario.title if scenario else "Unknown",
            "student_name": data.get("student_name"),
            "current_stage": data["current_stage"],
            "started_at": data["started_at"],
            "updated_at": data["updated_at"],
            "is_completed": data.get("is_completed", False),
            "turns": len(data.get("dialogue_history", []))
        })

    # Sort by most recent
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions

