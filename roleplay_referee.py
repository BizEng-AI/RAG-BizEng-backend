# roleplay_referee.py
"""
Evaluates student responses and provides targeted corrections.
Max 1 correction per turn to avoid overwhelming the student.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from services import get_chat_client, get_chat_model_name


class RoleplayReferee:
    """Analyzes student messages and provides feedback."""

    def __init__(self):
        self.error_types = ["grammar", "register", "vocabulary", "pragmatic"]

    def evaluate_response(
        self,
        student_message: str,
        scenario_context: str,
        stage_objective: str,
        ai_role: str,
    ) -> Optional[Dict[str, Any]]:
        if len(student_message.strip()) < 3:
            return {
                "error_type": "pragmatic",
                "original": student_message,
                "corrected": "(Please give a fuller answer)",
                "explanation": "Your answer is too short. Try to express one complete idea.",
                "priority": "high",
            }

        return self._llm_analyze(student_message, scenario_context, stage_objective, ai_role)

    def _llm_analyze(
        self,
        student_message: str,
        scenario_context: str,
        stage_objective: str,
        ai_role: str,
    ) -> Optional[Dict[str, Any]]:
        system_prompt = """You are a supportive English tutor evaluating a student's reply in a guided speaking practice.

Analyze the student's message for errors in these categories (in priority order):
1. Pragmatic - offensive language, totally off-topic replies, or replies that do not answer the task.
2. Register - language that is too informal, awkward, or unsuitable for the situation.
3. Vocabulary - incorrect, unnatural, or weak word choice.
4. Grammar - tense, agreement, article, or sentence-structure mistakes.

Rules:
- Flag only one issue, the most useful one to correct first.
- If the reply is clear and suitable, return NO_ERROR.
- Keep the correction short, natural, and learner-friendly.

Return this exact format:
ERROR_TYPE: [grammar|register|vocabulary|pragmatic|NO_ERROR]
ORIGINAL: [the problematic phrase or word]
CORRECTED: [a better version]
EXPLANATION: [brief explanation in one sentence]
PRIORITY: [high|medium|low]"""

        user_prompt = f"""SCENARIO CONTEXT: {scenario_context}
AI ROLE: {ai_role}
STAGE OBJECTIVE: {stage_objective}

STUDENT MESSAGE: \"{student_message}\"

Analyze this message and provide feedback."""

        try:
            model_name = get_chat_model_name()
            print(f"[referee] analyzing student message model={model_name}", flush=True)
            response = get_chat_client().chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.3,
                timeout=30,
            )
            analysis_text = response.choices[0].message.content.strip()
            print("[referee] analysis complete", flush=True)

            if "NO_ERROR" in analysis_text:
                return None

            error_type_match = re.search(r"ERROR_TYPE:\s*(\w+)", analysis_text, re.IGNORECASE)
            original_match = re.search(r"ORIGINAL:\s*(.+?)(?=\n|CORRECTED:)", analysis_text, re.IGNORECASE | re.DOTALL)
            corrected_match = re.search(r"CORRECTED:\s*(.+?)(?=\n|EXPLANATION:)", analysis_text, re.IGNORECASE | re.DOTALL)
            explanation_match = re.search(r"EXPLANATION:\s*(.+?)(?=\n|PRIORITY:|$)", analysis_text, re.IGNORECASE | re.DOTALL)
            priority_match = re.search(r"PRIORITY:\s*(\w+)", analysis_text, re.IGNORECASE)

            if error_type_match and error_type_match.group(1).lower() != "no_error":
                return {
                    "error_type": error_type_match.group(1).lower(),
                    "original": original_match.group(1).strip() if original_match else student_message,
                    "corrected": corrected_match.group(1).strip() if corrected_match else "",
                    "explanation": explanation_match.group(1).strip() if explanation_match else "Consider this correction.",
                    "priority": priority_match.group(1).lower() if priority_match else "medium",
                }

            return None
        except Exception as exc:
            print(f"[referee] error analyzing message: {exc}", flush=True)
            return None

    def check_stage_completion(
        self,
        student_message: str,
        advance_criteria: str,
        stage_keywords: List[str],
    ) -> bool:
        message_lower = student_message.lower()

        if len(student_message.strip()) < 10:
            return False

        keyword_matches = sum(1 for kw in stage_keywords if kw.lower() in message_lower)
        criteria_lower = advance_criteria.lower()

        if "introduce" in criteria_lower and any(word in message_lower for word in ["my name", "i'm", "i am", "hello", "hi"]):
            return True

        if "question" in criteria_lower and any(word in message_lower for word in ["?", "what", "how", "when", "where", "why", "could you", "can you"]):
            return True

        if ("thanks" in criteria_lower or "thank" in criteria_lower) and any(word in message_lower for word in ["thank", "appreciate", "grateful"]):
            return True

        if ("solution" in criteria_lower or "suggest" in criteria_lower or "advice" in criteria_lower) and any(word in message_lower for word in ["should", "could", "we can", "i can", "try", "suggest", "recommend"]):
            return True

        if len(student_message.split()) >= 15 and keyword_matches >= 1:
            return True

        if len(student_message.split()) >= 20:
            return True

        return False

    def generate_hint(self, stage_hints: List[str], hints_used: int, student_message: str) -> str:
        if hints_used >= len(stage_hints):
            return "Try to answer with one clear idea, one reason, and a short example."
        return stage_hints[hints_used]

    def create_mini_drill(self, error_type: str, original: str, corrected: str) -> str:
        drills = {
            "grammar": f"Quick practice: rewrite this correctly: '{original}'",
            "register": f"Try a more natural version of this sentence: '{original}'",
            "vocabulary": f"Choose a stronger word or phrase than '{original}'.",
            "pragmatic": "Try answering the task directly with one complete sentence.",
        }
        return drills.get(error_type, "Try expressing that idea in a different way.")


referee = RoleplayReferee()
