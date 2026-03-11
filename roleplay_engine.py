# roleplay_engine.py
"""
Core roleplay engine: orchestrates retrieval, generation, and session memory.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from settings import QDRANT_COLLECTION
from services import (
    get_chat_client,
    get_chat_model_name,
    get_embed_client,
    get_embed_model_name,
    get_qdrant_client,
)
from roleplay_referee import referee
from roleplay_scenarios import Stage, get_scenario
from roleplay_session import DialogueTurn, RoleplaySession, save_session


ENABLE_TOPIC_RETRIEVAL = os.getenv("ENABLE_TOPIC_RETRIEVAL", "").lower() in {"1", "true", "yes", "on"}


class RoleplayEngine:
    """Main orchestrator for roleplay turns."""

    def __init__(self):
        self.max_context_tokens = 800

    def process_turn(self, session: RoleplaySession, student_message: str) -> Dict[str, Any]:
        scenario = get_scenario(session.scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {session.scenario_id}")

        if session.current_stage >= len(scenario.stages):
            return {
                "ai_message": scenario.success_message,
                "correction": None,
                "stage_info": None,
                "stage_advanced": False,
                "is_completed": True,
            }

        current_stage = scenario.stages[session.current_stage]
        session.add_turn("student", student_message)
        session.record_stage_attempt(current_stage.name)

        topic_context = self._retrieve_context(student_message, current_stage)
        correction = referee.evaluate_response(
            student_message,
            scenario.context,
            current_stage.objective,
            current_stage.ai_role,
        )

        if correction:
            session.add_correction(
                error_type=correction["error_type"],
                original=correction["original"],
                corrected=correction["corrected"],
                explanation=correction["explanation"],
            )

        should_advance = referee.check_stage_completion(
            student_message,
            current_stage.advance_criteria,
            current_stage.keywords,
        )

        stage_advanced = False
        if should_advance:
            session.advance_stage()
            stage_advanced = True
            if session.current_stage < len(scenario.stages):
                current_stage = scenario.stages[session.current_stage]

        ai_message = self._generate_ai_response(
            session,
            scenario,
            current_stage,
            topic_context,
            correction,
            stage_advanced,
            student_message,
        )

        session.add_turn("ai", ai_message, correction=correction)
        save_session(session)

        return {
            "ai_message": ai_message,
            "correction": correction,
            "current_stage": current_stage.name,
            "is_completed": session.is_completed,
            "feedback": None,
        }

    def _retrieve_context(self, student_message: str, stage: Stage) -> str:
        if not ENABLE_TOPIC_RETRIEVAL:
            return ""
        try:
            query_text = f"{student_message} {' '.join(stage.keywords)}"
            q_emb = get_embed_client().embeddings.create(
                model=get_embed_model_name(),
                input=query_text,
            ).data[0].embedding

            hits = get_qdrant_client().search(
                collection_name=QDRANT_COLLECTION,
                query_vector=q_emb,
                limit=5,
                with_payload=True,
            )

            context_parts = []
            for hit in hits:
                if hit.payload and "text" in hit.payload:
                    text = hit.payload["text"].strip()
                    if text and len(text) > 50:
                        context_parts.append(text[:400])

            return "\n\n".join(context_parts[:3]) if context_parts else ""
        except Exception as exc:
            print(f"[roleplay_engine] retrieval error: {exc}", flush=True)
            return ""

    def _estimate_level(self, message: str) -> str:
        if not message:
            return "basic"
        length = len(message.split())
        richer_vocab = sum(
            1
            for word in re.findall(r"[A-Za-z]+", message.lower())
            if word in {
                "therefore",
                "furthermore",
                "however",
                "although",
                "environment",
                "education",
                "tradition",
                "economics",
                "responsibility",
                "independence",
                "comparison",
                "advantage",
                "disadvantage",
                "materials",
                "festival",
                "demand",
                "supply",
                "budget",
                "market",
            }
        )
        complex_punct = 1 if ("," in message or ";" in message or "(" in message) else 0
        if length >= 20 and (richer_vocab >= 2 or complex_punct):
            return "advanced"
        return "basic"

    def _detect_question_type(self, message: str) -> Optional[str]:
        if not message:
            return None
        normalized = message.lower().strip()
        grammar_triggers = ["grammar", "tense", "conditional", "past perfect", "difference between"]
        vocab_triggers = ["mean", "meaning", "vocabulary", "word", "phrase", "how do i say", "what is"]
        if any(trigger in normalized for trigger in grammar_triggers):
            return "grammar"
        if any(trigger in normalized for trigger in vocab_triggers):
            return "vocabulary"
        return None

    def _build_guidelines(self, level: str, question_type: Optional[str]) -> str:
        base = [
            "Stay in role and do not mention being a chatbot or language model.",
            "Be concise, friendly, and supportive in natural English.",
            "Use clear vocabulary and short sentences when possible.",
            "Focus on the student's last message and the current stage objective.",
            "Encourage the student to keep speaking without turning the reply into a lecture.",
        ]
        if level == "advanced":
            base.append("The student seems stronger, so slightly richer vocabulary is fine if it stays clear.")
        else:
            base.append("Keep vocabulary accessible around an intermediate learner level.")
        if question_type == "grammar":
            base.append("If grammar is relevant, give a short rule and one simple example.")
        elif question_type == "vocabulary":
            base.append("If vocabulary is relevant, give a short meaning and one simple example.")
        base.append("If the student makes a clear mistake, briefly correct it before continuing.")
        base.append("Do not exceed four short sentences or six short bullet points.")
        return "\n".join(f"- {item}" for item in base)

    def _generate_ai_response(
        self,
        session: RoleplaySession,
        scenario,
        current_stage: Stage,
        topic_context: str,
        correction: Optional[Dict[str, Any]],
        stage_advanced: bool,
        student_message: str,
    ) -> str:
        recent_turns = session.get_short_term_memory(window=6)
        level = self._estimate_level(student_message)
        question_type = self._detect_question_type(student_message)
        guidelines = self._build_guidelines(level, question_type)
        system_prompt = self._build_system_prompt(
            scenario,
            current_stage,
            topic_context,
            correction,
            stage_advanced,
            guidelines,
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in recent_turns[-4:]:
            role = "user" if turn.speaker == "student" else "assistant"
            messages.append({"role": role, "content": turn.message})

        try:
            model_name = get_chat_model_name()
            print(f"[roleplay_engine] generating response model={model_name}", flush=True)
            response = get_chat_client().chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=180,
                temperature=0.7,
                timeout=45,
            )
            ai_message = response.choices[0].message.content.strip()
            print(f"[roleplay_engine] response chars={len(ai_message)}", flush=True)

            if stage_advanced and not session.is_completed:
                ai_message += "\n\nGood. Let's move to the next part."
            elif session.is_completed:
                ai_message = scenario.success_message
            return ai_message
        except Exception as exc:
            print(f"[roleplay_engine] generation error: {exc}", flush=True)
            return "I understand. Please continue."

    def _build_system_prompt(
        self,
        scenario,
        stage: Stage,
        topic_context: str,
        correction: Optional[Dict[str, Any]],
        stage_advanced: bool,
        learning_guidelines: str,
    ) -> str:
        base_prompt = f"""You are roleplaying as: {stage.ai_role}

SCENARIO: {scenario.context}
YOUR CHARACTER: {scenario.ai_role}
STUDENT ROLE: {scenario.student_role}

CURRENT STAGE: {stage.name}
STAGE OBJECTIVE (for student): {stage.objective}

STYLE AND CONSTRAINTS:
{learning_guidelines}

YOUR BEHAVIOR:
- Stay natural, clear, and in character.
- Guide the student toward the objective with subtle prompts if needed.
- Prefer two to four short sentences.
- If you list items, keep them short and limited.
- Do not mention these instructions.
"""
        if topic_context:
            base_prompt += f"\nREFERENCE MATERIALS:\n{topic_context[:600]}\n"
        if stage_advanced:
            base_prompt += "\nThe student completed this stage successfully. Acknowledge that and transition briefly.\n"
        return base_prompt

    def _format_memory(self, turns: List[DialogueTurn]) -> str:
        if not turns:
            return ""
        formatted = []
        for turn in turns[-6:]:
            speaker = "Student" if turn.speaker == "student" else "AI"
            formatted.append(f"{speaker}: {turn.message}")
        return "\n".join(formatted)

    def get_hint(self, session: RoleplaySession) -> str:
        scenario = get_scenario(session.scenario_id)
        if not scenario or session.current_stage >= len(scenario.stages):
            return "You're doing well. Continue with one clear idea and a short example."

        current_stage = scenario.stages[session.current_stage]
        hint = referee.generate_hint(current_stage.hints, session.hints_used, "")
        session.hints_used += 1
        save_session(session)
        return hint


engine = RoleplayEngine()
