# roleplay_scenarios.py
"""
Defines business roleplay scenarios with multi-stage progression.
Each scenario has stages, objectives, and success criteria.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Stage:
    """A stage within a scenario"""
    name: str
    objective: str  # What student should accomplish
    ai_role: str  # AI's behavior/personality in this stage
    keywords: List[str]  # RAG search terms for this stage
    advance_criteria: str  # What triggers moving to next stage
    hints: List[str]  # Hints available if student struggles


@dataclass
class Scenario:
    """A complete roleplay scenario"""
    id: str
    title: str
    description: str
    difficulty: str  # "beginner" | "intermediate" | "advanced"
    context: str  # Background situation
    student_role: str
    ai_role: str
    stages: List[Stage]
    success_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# SCENARIO DEFINITIONS
# ============================================================================

SCENARIOS: Dict[str, Scenario] = {}

# --- Job Interview ---
SCENARIOS["job_interview"] = Scenario(
    id="job_interview",
    title="Job Interview",
    description="Practice interviewing for a business position",
    difficulty="intermediate",
    context="You are interviewing for a Marketing Manager position at a tech company.",
    student_role="Job Candidate",
    ai_role="HR Manager / Interviewer",
    stages=[
        Stage(
            name="greeting",
            objective="Introduce yourself professionally and make a good first impression",
            ai_role="Friendly but professional interviewer",
            keywords=["job interview greeting", "professional introduction", "first impression"],
            advance_criteria="Student introduces themselves with name and expresses interest",
            hints=[
                "Start with a greeting like 'Good morning' or 'Hello'",
                "Mention your name clearly",
                "Express enthusiasm about the opportunity"
            ]
        ),
        Stage(
            name="experience_discussion",
            objective="Discuss your relevant work experience and skills",
            ai_role="Interviewer asking about background and qualifications",
            keywords=["work experience", "qualifications", "skills", "achievements"],
            advance_criteria="Student describes at least one relevant experience or skill",
            hints=[
                "Use phrases like 'In my previous role...' or 'I have experience in...'",
                "Mention specific achievements or results",
                "Connect your experience to the job requirements"
            ]
        ),
        Stage(
            name="behavioral_question",
            objective="Answer a behavioral question using the STAR method",
            ai_role="Interviewer asking about past challenges",
            keywords=["teamwork", "problem solving", "conflict resolution", "leadership"],
            advance_criteria="Student provides a structured answer with situation and outcome",
            hints=[
                "Describe the Situation, Task, Action, and Result",
                "Use specific examples from your experience",
                "Focus on what YOU did and learned"
            ]
        ),
        Stage(
            name="closing",
            objective="Ask questions and close professionally",
            ai_role="Interviewer wrapping up and inviting questions",
            keywords=["interview questions", "company culture", "next steps"],
            advance_criteria="Student asks at least one question or expresses thanks",
            hints=[
                "Ask about the company culture, team, or role expectations",
                "Thank the interviewer for their time",
                "Express continued interest in the position"
            ]
        )
    ],
    success_message="Excellent job! You handled the interview professionally and demonstrated strong communication skills."
)

# --- Client Meeting ---
SCENARIOS["client_meeting"] = Scenario(
    id="client_meeting",
    title="Client Meeting",
    description="Present a proposal to a potential client",
    difficulty="advanced",
    context="You are meeting with a potential client to present your company's marketing services.",
    student_role="Account Manager",
    ai_role="Potential Client / Business Owner",
    stages=[
        Stage(
            name="opening",
            objective="Build rapport and set the meeting agenda",
            ai_role="Busy client who wants to see value quickly",
            keywords=["meeting agenda", "small talk", "business relationship"],
            advance_criteria="Student acknowledges client, sets agenda or asks about needs",
            hints=[
                "Thank them for their time",
                "Ask about their current challenges or goals",
                "Outline what you'll cover in the meeting"
            ]
        ),
        Stage(
            name="needs_assessment",
            objective="Ask questions to understand client's needs",
            ai_role="Client with specific pain points",
            keywords=["client needs", "questions", "discovery", "pain points"],
            advance_criteria="Student asks at least one open-ended question",
            hints=[
                "Use open-ended questions like 'What are your main challenges?'",
                "Listen actively and show understanding",
                "Ask follow-up questions to dig deeper"
            ]
        ),
        Stage(
            name="presentation",
            objective="Present your solution and its benefits",
            ai_role="Interested but skeptical client",
            keywords=["proposal", "benefits", "features", "value proposition"],
            advance_criteria="Student presents at least one benefit or solution",
            hints=[
                "Focus on benefits, not just features",
                "Use phrases like 'This would help you...'",
                "Provide specific examples or case studies"
            ]
        ),
        Stage(
            name="handling_objection",
            objective="Address client concerns professionally",
            ai_role="Client raising budget or timeline concerns",
            keywords=["objections", "concerns", "pricing", "negotiation"],
            advance_criteria="Student acknowledges concern and provides response",
            hints=[
                "Acknowledge their concern first",
                "Provide evidence or alternatives",
                "Ask if there are other concerns"
            ]
        ),
        Stage(
            name="closing",
            objective="Close the meeting with clear next steps",
            ai_role="Client considering the proposal",
            keywords=["next steps", "follow up", "closing"],
            advance_criteria="Student proposes next steps or asks for commitment",
            hints=[
                "Summarize key points discussed",
                "Suggest specific next steps",
                "Confirm timeline for follow-up"
            ]
        )
    ],
    success_message="Outstanding! You conducted a professional client meeting and handled objections effectively."
)

# --- Handling Complaint ---
SCENARIOS["customer_complaint"] = Scenario(
    id="customer_complaint",
    title="Customer Complaint",
    description="Handle an unhappy customer professionally",
    difficulty="beginner",
    context="A customer is upset about receiving a defective product. You need to resolve the issue.",
    student_role="Customer Service Representative",
    ai_role="Frustrated Customer",
    stages=[
        Stage(
            name="acknowledgment",
            objective="Listen and acknowledge the customer's frustration",
            ai_role="Angry customer venting about the problem",
            keywords=["apology", "empathy", "acknowledgment", "listening"],
            advance_criteria="Student acknowledges the problem and shows empathy",
            hints=[
                "Apologize for the inconvenience",
                "Show understanding: 'I understand how frustrating this must be'",
                "Don't make excuses or blame others"
            ]
        ),
        Stage(
            name="investigation",
            objective="Gather information about the issue",
            ai_role="Customer explaining the problem in detail",
            keywords=["questions", "problem details", "investigation"],
            advance_criteria="Student asks at least one question to understand the issue",
            hints=[
                "Ask specific questions about the issue",
                "Confirm details: order number, date, product",
                "Take notes and show you're listening"
            ]
        ),
        Stage(
            name="solution",
            objective="Offer a clear solution or resolution",
            ai_role="Customer waiting for a solution",
            keywords=["refund", "replacement", "compensation", "solution"],
            advance_criteria="Student offers a specific solution",
            hints=[
                "Offer concrete options: refund, replacement, discount",
                "Be specific about timeline",
                "Ask if the solution is acceptable"
            ]
        ),
        Stage(
            name="follow_up",
            objective="Ensure satisfaction and close positively",
            ai_role="Customer calming down",
            keywords=["follow up", "satisfaction", "thank you"],
            advance_criteria="Student confirms solution and thanks customer",
            hints=[
                "Confirm the next steps",
                "Thank them for their patience",
                "Offer additional assistance if needed"
            ]
        )
    ],
    success_message="Well done! You handled the complaint professionally and turned a negative situation into a positive one."
)

# --- Team Meeting ---
SCENARIOS["team_meeting"] = Scenario(
    id="team_meeting",
    title="Team Meeting",
    description="Lead a team meeting and address performance issues",
    difficulty="advanced",
    context="You're leading a team meeting to discuss a project that's behind schedule.",
    student_role="Team Leader / Manager",
    ai_role="Team Member",
    stages=[
        Stage(
            name="opening",
            objective="Start the meeting and state the purpose",
            ai_role="Team member waiting to hear the agenda",
            keywords=["meeting opening", "agenda", "team meeting"],
            advance_criteria="Student opens meeting and states purpose",
            hints=[
                "Thank everyone for attending",
                "State the meeting's purpose clearly",
                "Set expectations for the discussion"
            ]
        ),
        Stage(
            name="problem_discussion",
            objective="Discuss the issue without blaming",
            ai_role="Defensive team member",
            keywords=["problem discussion", "feedback", "constructive criticism"],
            advance_criteria="Student addresses issue without blaming individuals",
            hints=[
                "Focus on the situation, not the person",
                "Use 'we' instead of 'you'",
                "Ask for input: 'What challenges are we facing?'"
            ]
        ),
        Stage(
            name="solution_brainstorm",
            objective="Facilitate discussion to find solutions",
            ai_role="Team member with ideas",
            keywords=["brainstorming", "solutions", "collaboration"],
            advance_criteria="Student asks for ideas or suggests a solution",
            hints=[
                "Ask open-ended questions",
                "Encourage participation from the team",
                "Build on others' ideas positively"
            ]
        ),
        Stage(
            name="action_items",
            objective="Assign clear action items and deadlines",
            ai_role="Team member ready to take action",
            keywords=["action items", "responsibilities", "deadlines"],
            advance_criteria="Student assigns at least one action item",
            hints=[
                "Be specific about who does what",
                "Set clear deadlines",
                "Confirm understanding and commitment"
            ]
        )
    ],
    success_message="Excellent leadership! You handled a difficult situation diplomatically and motivated your team."
)

# --- Phone Call (Beginner) ---
SCENARIOS["business_call"] = Scenario(
    id="business_call",
    title="Business Phone Call",
    description="Make a professional phone call to a supplier",
    difficulty="beginner",
    context="You need to call a supplier to inquire about a delayed shipment.",
    student_role="Purchasing Officer",
    ai_role="Supplier Representative",
    stages=[
        Stage(
            name="introduction",
            objective="Introduce yourself and state the purpose of your call",
            ai_role="Receptionist or supplier representative",
            keywords=["phone greeting", "introduction", "purpose of call"],
            advance_criteria="Student introduces themselves and states reason for calling",
            hints=[
                "State your name and company",
                "Ask if it's a good time to talk",
                "Clearly state why you're calling"
            ]
        ),
        Stage(
            name="inquiry",
            objective="Ask about the delayed shipment professionally",
            ai_role="Supplier checking the order status",
            keywords=["inquiry", "order status", "shipping delay"],
            advance_criteria="Student asks about shipment with order details",
            hints=[
                "Provide order number or reference",
                "Ask specific questions about the delay",
                "Remain polite even if frustrated"
            ]
        ),
        Stage(
            name="resolution",
            objective="Confirm the resolution and next steps",
            ai_role="Supplier providing information",
            keywords=["confirmation", "next steps", "follow up"],
            advance_criteria="Student confirms details and thanks the representative",
            hints=[
                "Summarize what you understood",
                "Confirm the new delivery date",
                "Ask for confirmation in writing if needed"
            ]
        )
    ],
    success_message="Great job! You handled the business call professionally and got the information you needed."
)


def get_scenario(scenario_id: str) -> Optional[Scenario]:
    """Get a scenario by ID"""
    return SCENARIOS.get(scenario_id)


def list_scenarios(difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all available scenarios, optionally filtered by difficulty"""
    scenarios = SCENARIOS.values()
    if difficulty:
        scenarios = [s for s in scenarios if s.difficulty == difficulty]
    return [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "difficulty": s.difficulty,
            "stages": len(s.stages)
        }
        for s in scenarios
    ]

