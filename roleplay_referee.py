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
        """
        Analyze student's message and return ONE priority correction if needed.
        Returns None if message is good, or a dict with correction details.
        """
        if len(student_message.strip()) < 3:
            return {
                "error_type": "pragmatic",
                "original": student_message,
                "corrected": "(Please provide a more complete response)",
                "explanation": "Your response is too short. Try to express your thoughts more fully.",
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
        """Use an LLM to analyze the response."""

        system_prompt = """You are a strict Business English tutor evaluating student responses in a professional roleplay scenario.

Analyze the student's message for errors in these categories (in priority order):
1. Pragmatic - offensive language, aggressive tone, off-topic responses, or clearly unprofessional behavior.
2. Register - language that is too casual for a business setting.
3. Vocabulary - incorrect or unnatural wording.
4. Grammar - tense, agreement, article, or sentence-structure mistakes.

Rules:
- Always flag clearly unprofessional language as a pragmatic error with high priority.
- Flag only one issue, the most serious one.
- If the message is professional and appropriate, return NO_ERROR.

Return this exact format:
ERROR_TYPE: [grammar|register|vocabulary|pragmatic|NO_ERROR]
ORIGINAL: [the problematic phrase or word]
CORRECTED: [how to fix it professionally]
EXPLANATION: [brief explanation in one sentence]
PRIORITY: [high|medium|low]"""

        user_prompt = f"""SCENARIO CONTEXT: {scenario_context}
AI ROLE: {ai_role}
STAGE OBJECTIVE: {stage_objective}

STUDENT'S MESSAGE: \"{student_message}\"

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
        """Check whether the student can advance to the next stage."""
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

        if ("solution" in criteria_lower or "offer" in criteria_lower) and any(word in message_lower for word in ["we can", "i can", "would", "offer", "provide", "solution"]):
            return True

        if "experience" in criteria_lower and any(word in message_lower for word in ["experience", "worked", "role", "position", "responsible", "managed"]):
            return True

        if len(student_message.split()) >= 15 and keyword_matches >= 1:
            return True

        if len(student_message.split()) >= 20:
            return True

        return False

    def generate_hint(self, stage_hints: List[str], hints_used: int, student_message: str) -> str:
        """Generate a helpful hint for the student."""
        if hints_used >= len(stage_hints):
            return "Try to think about what a professional would say in this situation. Focus on being clear and polite."
        return stage_hints[hints_used]

    def create_mini_drill(self, error_type: str, original: str, corrected: str) -> str:
        """Create a quick practice exercise based on the error."""
        drills = {
            "grammar": f"Quick practice: Try rephrasing this sentence correctly: '{original}'",
            "register": f"Let's practice formality: How would you say this in a more professional way? '{original}'",
            "vocabulary": f"Vocabulary check: What's a better word or phrase than '{original}' in business English?",
            "pragmatic": "Think about how you could rephrase that more clearly in a business setting.",
        }
        return drills.get(error_type, "Try expressing that idea in a different way.")


referee = RoleplayReferee()
