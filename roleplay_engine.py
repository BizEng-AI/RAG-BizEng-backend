# roleplay_engine.py
"""
Core roleplay engine: orchestrates RAG retrieval + LLM generation + memory.
This is the "director" that runs each turn.
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from openai import OpenAI, AzureOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from settings import (
    OPENAI_API_KEY,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    EMBED_MODEL,
    CHAT_MODEL,
    USE_AZURE,
    USE_AZURE_EMBEDDINGS,
    AZURE_OPENAI_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_CHAT_DEPLOYMENT,
    AZURE_OPENAI_EMBEDDING_KEY,
    AZURE_OPENAI_EMBEDDING_ENDPOINT,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
)
from roleplay_session import RoleplaySession, save_session, DialogueTurn
from roleplay_scenarios import get_scenario, Stage
from roleplay_referee import referee


# Initialize OpenAI client for chat (Azure Sweden Central or regular OpenAI)
if USE_AZURE:
    oai = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    print(f"[roleplay_engine] ✅ Using Azure OpenAI for Chat (Sweden Central)", flush=True)
else:
    oai = OpenAI(api_key=OPENAI_API_KEY)
    print(f"[roleplay_engine] ✅ Using OpenAI (fallback)", flush=True)

# Initialize separate client for embeddings (Azure UAE North or regular OpenAI)
if USE_AZURE_EMBEDDINGS:
    oai_embed = AzureOpenAI(
        api_key=AZURE_OPENAI_EMBEDDING_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT
    )
    print(f"[roleplay_engine] ✅ Using Azure Embeddings (UAE North)", flush=True)
else:
    oai_embed = OpenAI(api_key=OPENAI_API_KEY)
    print(f"[roleplay_engine] ✅ Using OpenAI Embeddings (fallback)", flush=True)

qdr = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=30,
)


class RoleplayEngine:
    """Main orchestrator for roleplay turns"""

    def __init__(self):
        self.max_context_tokens = 800  # For RAG context

    def process_turn(
        self,
        session: RoleplaySession,
        student_message: str
    ) -> Dict[str, Any]:
        """
        Process a student's message and generate AI response.

        Returns:
        {
            "ai_message": "...",
            "correction": {...} or None,
            "stage_info": {...},
            "stage_advanced": bool,
            "is_completed": bool
        }
        """
        scenario = get_scenario(session.scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {session.scenario_id}")

        if session.current_stage >= len(scenario.stages):
            return {
                "ai_message": scenario.success_message,
                "correction": None,
                "stage_info": None,
                "stage_advanced": False,
                "is_completed": True
            }

        current_stage = scenario.stages[session.current_stage]

        # Step 1: Record student's message
        session.add_turn("student", student_message)
        session.record_stage_attempt(current_stage.name)

        # Step 2: RAG - Retrieve relevant context from books
        rag_context = self._retrieve_context(student_message, current_stage)

        # Step 3: Referee - Analyze for errors
        correction = referee.evaluate_response(
            student_message,
            scenario.context,
            current_stage.objective,
            current_stage.ai_role
        )

        if correction:
            session.add_correction(
                error_type=correction["error_type"],
                original=correction["original"],
                corrected=correction["corrected"],
                explanation=correction["explanation"]
            )

        # Step 4: Check if stage should advance
        should_advance = referee.check_stage_completion(
            student_message,
            current_stage.advance_criteria,
            current_stage.keywords
        )

        stage_advanced = False
        if should_advance:
            session.advance_stage()
            stage_advanced = True
            # Get next stage if available
            if session.current_stage < len(scenario.stages):
                current_stage = scenario.stages[session.current_stage]

        # Step 5: Generate AI response
        ai_message = self._generate_ai_response(
            session,
            scenario,
            current_stage,
            rag_context,
            correction,
            stage_advanced
        )

        # Step 6: Record AI's message
        session.add_turn("ai", ai_message, correction=correction)

        # Step 7: Save session
        save_session(session)

        # Return response - format matches Android expectations
        return {
            "ai_message": ai_message,
            "correction": correction,
            "current_stage": current_stage.name,  # Changed from stage_info to current_stage
            "is_completed": session.is_completed,
            "feedback": None  # Added feedback field for Android compatibility
        }

    def _retrieve_context(self, student_message: str, stage: Stage) -> str:
        """
        Retrieve relevant context from Qdrant using RAG.
        Combines student's message with stage keywords.
        """
        try:
            # Combine student message with stage keywords for better retrieval
            query_text = f"{student_message} {' '.join(stage.keywords)}"

            # Get embedding (use Azure deployment name if Azure is enabled)
            embed_model = AZURE_OPENAI_EMBEDDING_DEPLOYMENT if USE_AZURE_EMBEDDINGS else EMBED_MODEL
            q_emb = oai_embed.embeddings.create(
                model=embed_model,
                input=query_text
            ).data[0].embedding

            # Search Qdrant
            hits = qdr.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=q_emb,
                limit=5,
                with_payload=True
            )

            # Extract text from hits
            context_parts = []
            for hit in hits:
                if hit.payload and "text" in hit.payload:
                    text = hit.payload["text"].strip()
                    if text and len(text) > 50:  # Filter out very short snippets
                        context_parts.append(text[:400])  # Limit each chunk

            context = "\n\n".join(context_parts[:3])  # Use top 3
            return context if context else ""

        except Exception as e:
            print(f"[roleplay_engine] RAG retrieval error: {e}", flush=True)
            return ""

    def _generate_ai_response(
        self,
        session: RoleplaySession,
        scenario,
        current_stage: Stage,
        rag_context: str,
        correction: Optional[Dict[str, Any]],
        stage_advanced: bool
    ) -> str:
        """
        Generate AI's response using LLM with RAG context and memory.
        """
        # Build memory context
        recent_turns = session.get_short_term_memory(window=6)
        memory_context = self._format_memory(recent_turns)

        # Build system prompt
        system_prompt = self._build_system_prompt(
            scenario,
            current_stage,
            rag_context,
            correction,
            stage_advanced
        )

        # Build conversation history for LLM
        messages = [{"role": "system", "content": system_prompt}]

        # Add recent dialogue turns
        for turn in recent_turns[-4:]:  # Last 4 turns (2 exchanges)
            role = "user" if turn.speaker == "student" else "assistant"
            messages.append({"role": role, "content": turn.message})

        # Generate response
        try:
            chat_model = AZURE_OPENAI_CHAT_DEPLOYMENT if USE_AZURE else CHAT_MODEL
            response = oai.chat.completions.create(
                model=chat_model,
                messages=messages,
                max_tokens=250,
                temperature=0.7  # Slightly higher for natural conversation
            )

            ai_message = response.choices[0].message.content.strip()

            # DO NOT append correction to ai_message - it's sent separately
            # The Android app displays correction in its own UI element

            # If stage advanced, acknowledge it
            if stage_advanced and not session.is_completed:
                ai_message += f"\n\n✅ Great! Let's move to the next part."
            elif session.is_completed:
                ai_message = scenario.success_message

            return ai_message

        except Exception as e:
            print(f"[roleplay_engine] LLM generation error: {e}", flush=True)
            return "I see. Please continue."

    def _build_system_prompt(
        self,
        scenario,
        stage: Stage,
        rag_context: str,
        correction: Optional[Dict[str, Any]],
        stage_advanced: bool
    ) -> str:
        """Build the system prompt for the LLM"""

        base_prompt = f"""You are roleplaying as: {stage.ai_role}

SCENARIO: {scenario.context}
YOUR CHARACTER: {scenario.ai_role}
STUDENT'S ROLE: {scenario.student_role}

CURRENT STAGE: {stage.name}
STAGE OBJECTIVE (for student): {stage.objective}

YOUR BEHAVIOR:
- Stay in character as {stage.ai_role}
- Be natural and conversational, but professional
- Guide the conversation toward the stage objective
- React appropriately to what the student says
- Keep responses concise (2-4 sentences typically)
- If student seems stuck, give subtle hints
- Show realistic business communication

"""

        # Add RAG context if available
        if rag_context:
            base_prompt += f"""
REFERENCE MATERIALS (use for inspiration on phrasing and vocabulary):
{rag_context[:600]}

Use these materials to inform your responses with appropriate business vocabulary and phrasing.

"""

        # Add guidance based on stage advancement
        if stage_advanced:
            base_prompt += "\nThe student has completed this stage successfully. Acknowledge their success and transition naturally to the next stage.\n"

        return base_prompt

    def _format_memory(self, turns: List[DialogueTurn]) -> str:
        """Format recent turns into readable context"""
        if not turns:
            return ""

        formatted = []
        for turn in turns[-6:]:
            speaker = "Student" if turn.speaker == "student" else "AI"
            formatted.append(f"{speaker}: {turn.message}")

        return "\n".join(formatted)

    def get_hint(self, session: RoleplaySession) -> str:
        """Generate a hint for the student"""
        scenario = get_scenario(session.scenario_id)
        if not scenario or session.current_stage >= len(scenario.stages):
            return "You're doing great! Just continue the conversation naturally."

        current_stage = scenario.stages[session.current_stage]
        hint = referee.generate_hint(
            current_stage.hints,
            session.hints_used,
            ""
        )

        session.hints_used += 1
        save_session(session)

        return hint


# Singleton instance
engine = RoleplayEngine()
