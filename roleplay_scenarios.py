# roleplay_scenarios.py
"""
Defines business-first roleplay scenarios for BizEng Chatbot.
General English support is still welcome, but the situations stay grounded in
business communication, logistics, meetings, and economics.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Stage:
    """A stage within a scenario."""

    name: str
    objective: str
    ai_role: str
    keywords: List[str]
    advance_criteria: str
    hints: List[str]


@dataclass
class Scenario:
    """A complete roleplay scenario."""

    id: str
    title: str
    description: str
    difficulty: str
    context: str
    student_role: str
    ai_role: str
    stages: List[Stage]
    success_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


SCENARIOS: Dict[str, Scenario] = {}


SCENARIOS["corporate_travel_planning"] = Scenario(
    id="corporate_travel_planning",
    title="Corporate Travel Planning",
    description="Plan a short business trip with transport, hotel, budget, and company policy in mind.",
    difficulty="A2-B1",
    context="You are planning a 3-day business trip for your company. You need to explain the travel, hotel, and budget choices.",
    student_role="Corporate travel coordinator",
    ai_role="Finance manager",
    stages=[
        Stage(
            name="trip_scope",
            objective="Explain the trip purpose and first travel option.",
            ai_role="Finance manager asking why the trip is needed",
            keywords=["trip", "purpose", "destination", "meeting", "travel"],
            advance_criteria="Student explains the purpose and suggests an initial travel plan.",
            hints=[
                "State the business purpose clearly.",
                "Mention destination and timing.",
                "Suggest one travel option with a reason.",
            ],
        ),
        Stage(
            name="budget_review",
            objective="Explain or change the budget with a clear reason.",
            ai_role="Finance manager challenging high costs",
            keywords=["budget", "cost", "policy", "hotel", "expense"],
            advance_criteria="Student justifies costs or revises the plan to match policy.",
            hints=[
                "Use simple business language such as cheaper or within budget.",
                "Mention company policy if relevant.",
                "Offer a change if needed.",
            ],
        ),
        Stage(
            name="final_summary",
            objective="Summarize the final travel plan and next step.",
            ai_role="Finance manager asking for a final decision",
            keywords=["summary", "approve", "booking", "schedule", "final"],
            advance_criteria="Student summarizes the plan and states a next action.",
            hints=[
                "Keep the summary short.",
                "Mention transport, stay, and budget.",
                "End with booking or approval as the next step.",
            ],
        ),
    ],
    success_message="Great work. You explained the plan, policy, and budget in clear English.",
)

SCENARIOS["trans_siberian_route"] = Scenario(
    id="trans_siberian_route",
    title="Trans-Siberian Route Plan",
    description="Plan a rail-based export route and discuss timing, cost, and risks.",
    difficulty="A2-B1",
    context="You are discussing an export shipment from Uzbekistan to Europe using the Trans-Siberian route.",
    student_role="Logistics coordinator",
    ai_role="Client operations manager",
    stages=[
        Stage(
            name="route_summary",
            objective="Present the route and its main advantages.",
            ai_role="Client asking for a route overview",
            keywords=["route", "rail", "time", "customs", "plan"],
            advance_criteria="Student explains the route and gives at least one advantage.",
            hints=[
                "Start with origin and destination.",
                "Mention speed, reliability, or cost.",
                "Keep the overview short.",
            ],
        ),
        Stage(
            name="risk_discussion",
            objective="Name one likely risk and suggest one solution.",
            ai_role="Client asking what could go wrong",
            keywords=["risk", "delay", "border", "documents", "solution"],
            advance_criteria="Student names one risk and one solution.",
            hints=[
                "Think about customs, weather, or paperwork.",
                "Use we can reduce this risk by...",
                "Offer one clear step.",
            ],
        ),
        Stage(
            name="final_recommendation",
            objective="Give a final recommendation and next step.",
            ai_role="Client asking for a decision",
            keywords=["recommend", "next step", "confirm", "plan", "delivery"],
            advance_criteria="Student gives a recommendation and a clear next action.",
            hints=[
                "Use I recommend... for a clear close.",
                "Mention booking, confirmation, or documents.",
                "End with a confident summary.",
            ],
        ),
    ],
    success_message="Great work. You presented the route clearly, handled risks, and gave a practical recommendation.",
)

SCENARIOS["transport_mode_comparison"] = Scenario(
    id="transport_mode_comparison",
    title="Transport Mode Comparison",
    description="Compare rail, sea, and air shipping for a business delivery.",
    difficulty="A2-B1",
    context="You are advising a client which transport mode is best for a time-sensitive shipment.",
    student_role="Logistics advisor",
    ai_role="Client representative",
    stages=[
        Stage(
            name="compare_options",
            objective="Compare at least two transport options.",
            ai_role="Client asking for options",
            keywords=["rail", "sea", "air", "cost", "speed"],
            advance_criteria="Student compares options with one clear tradeoff.",
            hints=[
                "Use words like faster, cheaper, or more reliable.",
                "Mention cost and delivery time.",
                "Keep the comparison simple.",
            ],
        ),
        Stage(
            name="choose_mode",
            objective="Choose one mode and justify the choice.",
            ai_role="Client asking for your recommendation",
            keywords=["recommend", "deadline", "budget", "risk", "choose"],
            advance_criteria="Student recommends one option tied to business needs.",
            hints=[
                "Connect your choice to deadline or budget.",
                "Use I recommend ... because ...",
                "Add one risk note if needed.",
            ],
        ),
        Stage(
            name="client_confirmation",
            objective="Confirm decision and next operational step.",
            ai_role="Client asking what happens next",
            keywords=["confirm", "book", "documents", "schedule", "next"],
            advance_criteria="Student confirms the choice and names one next action.",
            hints=[
                "Say what action comes next today.",
                "Mention documents, booking, or scheduling.",
                "Close politely.",
            ],
        ),
    ],
    success_message="Excellent. You compared options clearly and guided the client to a practical transport decision.",
)

SCENARIOS["delivery_delay_handling"] = Scenario(
    id="delivery_delay_handling",
    title="Delivery Delay Handling",
    description="Tell a client about a delay in a clear and polite way.",
    difficulty="A2-B1",
    context="A shipment is delayed and the client is worried about business impact.",
    student_role="Account manager",
    ai_role="Concerned client",
    stages=[
        Stage(
            name="acknowledge_delay",
            objective="Acknowledge delay and communicate with empathy.",
            ai_role="Client asking what happened",
            keywords=["delay", "apology", "update", "impact", "reason"],
            advance_criteria="Student acknowledges the delay and gives a clear update.",
            hints=[
                "Start with a polite apology.",
                "Give one factual update.",
                "Avoid blaming language.",
            ],
        ),
        Stage(
            name="recovery_plan",
            objective="Offer a realistic recovery plan.",
            ai_role="Client asking how the issue will be fixed",
            keywords=["recovery", "plan", "partial", "priority", "timeline"],
            advance_criteria="Student proposes one concrete recovery action and timeline.",
            hints=[
                "Offer a specific action, not a vague promise.",
                "Include when the client can expect progress.",
                "Show ownership.",
            ],
        ),
        Stage(
            name="confidence_close",
            objective="Close with confidence and next communication step.",
            ai_role="Client asking for final assurance",
            keywords=["assurance", "monitor", "daily", "contact", "follow-up"],
            advance_criteria="Student closes with reassurance and a follow-up commitment.",
            hints=[
                "Say how you will keep the client informed.",
                "Use confident but realistic language.",
                "End with a polite close.",
            ],
        ),
    ],
    success_message="Well done. You explained the delay clearly and politely.",
)

SCENARIOS["customs_risk_briefing"] = Scenario(
    id="customs_risk_briefing",
    title="Customs Risk Briefing",
    description="Explain customs, documents, and route risks before a shipment is approved.",
    difficulty="A2-B1",
    context="A client wants approval for an export route and needs a short note about customs and document risks.",
    student_role="Logistics specialist",
    ai_role="Client procurement manager",
    stages=[
        Stage(
            name="risk_overview",
            objective="Name the main customs or paperwork risks.",
            ai_role="Manager asking for a short risk overview",
            keywords=["customs", "documents", "border", "risk", "clearance"],
            advance_criteria="Student names at least one customs or document risk.",
            hints=[
                "Think about missing paperwork, delays, or inspections.",
                "Use clear and direct language.",
                "Mention the business effect briefly.",
            ],
        ),
        Stage(
            name="risk_control",
            objective="Suggest preventive actions before shipment.",
            ai_role="Manager asking how to reduce the risk",
            keywords=["checklist", "verify", "control", "prevent", "review"],
            advance_criteria="Student suggests at least one preventive action.",
            hints=[
                "Mention document review or early verification.",
                "Use we can reduce this by...",
                "Keep the action practical.",
            ],
        ),
        Stage(
            name="decision_support",
            objective="Give a recommendation on approval and timing buffer.",
            ai_role="Manager asking for your final recommendation",
            keywords=["approve", "buffer", "timeline", "recommend", "final"],
            advance_criteria="Student gives a recommendation with a timing or planning note.",
            hints=[
                "Say whether the route should move forward.",
                "Mention a buffer or control point.",
                "End with a calm, confident recommendation.",
            ],
        ),
    ],
    success_message="Strong briefing. You explained customs risk clearly and supported the shipment decision well.",
)

SCENARIOS["international_business_meeting"] = Scenario(
    id="international_business_meeting",
    title="International Business Meeting",
    description="Open and guide a cross-border business meeting with clarity.",
    difficulty="A2-B1",
    context="You are leading a short international business meeting with stakeholders from different regions.",
    student_role="Meeting facilitator",
    ai_role="International partner",
    stages=[
        Stage(
            name="meeting_opening",
            objective="Open the meeting and confirm the agenda.",
            ai_role="Partner waiting for the kickoff",
            keywords=["agenda", "objective", "welcome", "participants", "timeline"],
            advance_criteria="Student opens the meeting and confirms the agenda clearly.",
            hints=[
                "Start with a brief welcome.",
                "State the goal and agenda order.",
                "Mention time awareness.",
            ],
        ),
        Stage(
            name="alignment_discussion",
            objective="Align priorities and ask for confirmation.",
            ai_role="Partner discussing priorities",
            keywords=["priority", "align", "confirm", "scope", "responsibility"],
            advance_criteria="Student aligns priorities and asks for confirmation.",
            hints=[
                "Use polite confirmation language.",
                "Clarify responsibility or scope.",
                "Summarize the key point before moving on.",
            ],
        ),
        Stage(
            name="meeting_wrap",
            objective="Summarize decisions and next actions.",
            ai_role="Partner asking for a close summary",
            keywords=["summary", "action", "owner", "deadline", "follow-up"],
            advance_criteria="Student summarizes decisions and assigns next steps.",
            hints=[
                "List action owners and deadlines briefly.",
                "Use clear and direct wording.",
                "Close with a follow-up plan.",
            ],
        ),
    ],
    success_message="Good work. You opened and closed the meeting in clear English.",
)

SCENARIOS["contract_negotiation"] = Scenario(
    id="contract_negotiation",
    title="Contract Negotiation",
    description="Negotiate pricing and terms while keeping a cooperative tone.",
    difficulty="A2-B1",
    context="You are negotiating a distribution contract with an international partner.",
    student_role="Negotiator",
    ai_role="Supplier representative",
    stages=[
        Stage(
            name="initial_offer",
            objective="Respond to the first offer politely and set your position.",
            ai_role="Supplier presenting an initial offer",
            keywords=["offer", "price", "term", "position", "proposal"],
            advance_criteria="Student responds politely and states a clear negotiation position.",
            hints=[
                "Acknowledge the offer first.",
                "State what needs adjustment.",
                "Stay collaborative.",
            ],
        ),
        Stage(
            name="new_offer",
            objective="Suggest a realistic new offer with a reason.",
            ai_role="Supplier asking for your new offer",
            keywords=["offer", "price", "timeline", "amount", "discount"],
            advance_criteria="Student gives a specific new offer and reason.",
            hints=[
                "Use numbers or clear terms when possible.",
                "Explain the business reason for your request.",
                "Mention what you can give in return.",
            ],
        ),
        Stage(
            name="agreement_close",
            objective="Move toward agreement and confirm the next legal step.",
            ai_role="Supplier asking to finalize terms",
            keywords=["agreement", "finalize", "draft", "review", "sign"],
            advance_criteria="Student confirms near-final terms and the next contract step.",
            hints=[
                "Summarize the agreed points briefly.",
                "Mention legal or document review.",
                "Close positively.",
            ],
        ),
    ],
    success_message="Great work. You stayed polite, made a clear offer, and moved toward agreement.",
)

SCENARIOS["follow_up_email_summary"] = Scenario(
    id="follow_up_email_summary",
    title="Follow-Up Summary",
    description="Summarize meeting decisions, action owners, and next steps after a business meeting.",
    difficulty="A2-B1",
    context="A meeting has just ended and you need to summarize the main points before sending a follow-up email.",
    student_role="Project coordinator",
    ai_role="Senior colleague",
    stages=[
        Stage(
            name="meeting_purpose",
            objective="State the meeting purpose and key topics.",
            ai_role="Senior colleague asking what should go in the summary",
            keywords=["purpose", "discussion", "agenda", "topic", "summary"],
            advance_criteria="Student states the purpose and mentions at least one key topic.",
            hints=[
                "Open with why the meeting happened.",
                "Mention the main topic or decision area.",
                "Keep it short.",
            ],
        ),
        Stage(
            name="agreement_points",
            objective="Summarize the decisions and agreed terms.",
            ai_role="Senior colleague asking what was agreed",
            keywords=["agreed", "decision", "price", "timeline", "terms"],
            advance_criteria="Student lists at least one clear agreed point.",
            hints=[
                "Focus on what is final or nearly final.",
                "Use clear business wording.",
                "Avoid unnecessary detail.",
            ],
        ),
        Stage(
            name="next_actions",
            objective="Assign next steps and owners.",
            ai_role="Senior colleague asking what happens next",
            keywords=["action", "owner", "deadline", "next", "follow-up"],
            advance_criteria="Student names next actions and who is responsible.",
            hints=[
                "Name at least one owner and one action.",
                "Mention a time frame if possible.",
                "Close politely.",
            ],
        ),
    ],
    success_message="Excellent. You turned the meeting into a clear and useful follow-up summary.",
)

SCENARIOS["business_and_work"] = Scenario(
    id="business_and_work",
    title="Business and Work",
    description="Talk about work tasks, skills, and good work habits in clear English.",
    difficulty="A2-B1",
    context="You are discussing everyday business and work expectations with a new colleague.",
    student_role="Team member",
    ai_role="New colleague",
    stages=[
        Stage(
            name="role_description",
            objective="Describe your role or a typical work responsibility.",
            ai_role="Colleague asking what your work involves",
            keywords=["role", "task", "responsibility", "team", "work"],
            advance_criteria="Student describes a role or responsibility clearly.",
            hints=[
                "Mention one regular task.",
                "Use simple present tense.",
                "Explain why the work matters.",
            ],
        ),
        Stage(
            name="key_skills",
            objective="Explain which work skills matter most.",
            ai_role="Colleague asking what skills are important",
            keywords=["skill", "communication", "time management", "teamwork", "work"],
            advance_criteria="Student names at least one skill and explains why it matters.",
            hints=[
                "Choose one or two useful skills.",
                "Give a short reason or example.",
                "Keep the explanation practical.",
            ],
        ),
        Stage(
            name="workplace_advice",
            objective="Give one practical workplace tip.",
            ai_role="Colleague asking for advice",
            keywords=["advice", "habit", "improve", "work", "tip"],
            advance_criteria="Student gives one clear workplace tip.",
            hints=[
                "Use should or it helps to.",
                "Keep the advice realistic.",
                "End positively.",
            ],
        ),
    ],
    success_message="Well done. You explained business and work habits clearly and usefully.",
)

SCENARIOS["entrepreneur_pitch"] = Scenario(
    id="entrepreneur_pitch",
    title="Entrepreneur Pitch",
    description="Discuss a business idea, its value, and its risks in a short business pitch.",
    difficulty="A2-B1",
    context="You are giving a brief pitch for a new business idea to a potential mentor or investor.",
    student_role="Entrepreneur",
    ai_role="Mentor",
    stages=[
        Stage(
            name="idea_intro",
            objective="Introduce the idea and the customer problem it solves.",
            ai_role="Mentor asking what the idea is",
            keywords=["idea", "customer", "problem", "solution", "market"],
            advance_criteria="Student introduces the idea and the customer problem clearly.",
            hints=[
                "Say what the product or service does.",
                "Mention the customer need.",
                "Keep it simple and direct.",
            ],
        ),
        Stage(
            name="value_and_risk",
            objective="Explain the value and one main risk.",
            ai_role="Mentor asking why the idea could work",
            keywords=["value", "benefit", "risk", "budget", "competition"],
            advance_criteria="Student explains one value point and one realistic risk.",
            hints=[
                "State why customers may want it.",
                "Mention one challenge such as budget or competition.",
                "Stay balanced and realistic.",
            ],
        ),
        Stage(
            name="next_step",
            objective="Suggest the next business step.",
            ai_role="Mentor asking what happens next",
            keywords=["pilot", "test", "launch", "research", "next"],
            advance_criteria="Student gives a practical next step for the idea.",
            hints=[
                "Think about research, testing, or a pilot launch.",
                "Keep the next step small and practical.",
                "End confidently.",
            ],
        ),
    ],
    success_message="Nice pitch. You explained the idea clearly, balanced value with risk, and proposed a sensible next step.",
)

SCENARIOS["customer_complaint_response"] = Scenario(
    id="customer_complaint_response",
    title="Customer Complaint Response",
    description="Answer a customer complaint with empathy, a solution, and a clear next step.",
    difficulty="A2-B1",
    context="A customer is unhappy because an order arrived late and one item is missing.",
    student_role="Customer support representative",
    ai_role="Unhappy customer",
    stages=[
        Stage(
            name="empathy_opening",
            objective="Thank the customer and show empathy.",
            ai_role="Customer explaining the complaint",
            keywords=["sorry", "understand", "problem", "order", "late"],
            advance_criteria="Student acknowledges the complaint politely and clearly.",
            hints=[
                "Start with thank you or I am sorry.",
                "Show that you understand the problem.",
                "Keep the tone calm and helpful.",
            ],
        ),
        Stage(
            name="solution_offer",
            objective="Offer one practical solution.",
            ai_role="Customer asking what you will do now",
            keywords=["replace", "refund", "check", "solution", "update"],
            advance_criteria="Student offers a clear solution or action.",
            hints=[
                "Give one specific action.",
                "Use can or will for a clear promise.",
                "Mention timing if possible.",
            ],
        ),
        Stage(
            name="follow_up_close",
            objective="Confirm the next follow-up step.",
            ai_role="Customer asking when they will hear back",
            keywords=["tomorrow", "follow up", "confirm", "email", "next"],
            advance_criteria="Student confirms when and how they will follow up.",
            hints=[
                "Say when you will contact the customer.",
                "Mention email, phone, or status update.",
                "Close politely.",
            ],
        ),
    ],
    success_message="Good support response. You showed empathy, offered a solution, and confirmed the next step.",
)

SCENARIOS["team_task_update"] = Scenario(
    id="team_task_update",
    title="Team Task Update",
    description="Give a short progress update about a task, blocker, and next action.",
    difficulty="A2-B1",
    context="Your team leader asks for a quick update on a task during a short stand-up meeting.",
    student_role="Team member",
    ai_role="Team leader",
    stages=[
        Stage(
            name="progress_status",
            objective="Say what is finished and what is still in progress.",
            ai_role="Team leader asking for your update",
            keywords=["finished", "progress", "task", "done", "working"],
            advance_criteria="Student gives a clear status update.",
            hints=[
                "Start with what is done.",
                "Use still working on for unfinished work.",
                "Keep it brief.",
            ],
        ),
        Stage(
            name="blocker",
            objective="Name one blocker or risk.",
            ai_role="Team leader asking if anything is blocking you",
            keywords=["blocker", "risk", "need", "waiting", "problem"],
            advance_criteria="Student identifies a blocker or says there is no blocker.",
            hints=[
                "Use I am waiting for... if needed.",
                "Name one problem clearly.",
                "Ask for help if you need it.",
            ],
        ),
        Stage(
            name="next_action",
            objective="Confirm the next action and timing.",
            ai_role="Team leader asking what you will do next",
            keywords=["next", "today", "deadline", "finish", "confirm"],
            advance_criteria="Student gives a next action and timing.",
            hints=[
                "Use I will... for the next action.",
                "Mention today, tomorrow, or Friday.",
                "End with a clear commitment.",
            ],
        ),
    ],
    success_message="Clear update. You explained progress, the blocker, and the next action well.",
)

SCENARIOS["basic_economic_concepts"] = Scenario(
    id="basic_economic_concepts",
    title="Basic Economic Concepts",
    description="Explain goods, services, inflation, and simple economic choices.",
    difficulty="A2-B1",
    context="You are helping a classmate understand a basic economic concept in simple English.",
    student_role="Student explaining economics",
    ai_role="Classmate",
    stages=[
        Stage(
            name="concept_choice",
            objective="Choose one concept and define it simply.",
            ai_role="Classmate asking for a simple explanation",
            keywords=["goods", "services", "inflation", "choice", "economics"],
            advance_criteria="Student defines one concept in simple language.",
            hints=[
                "Use one short definition.",
                "Avoid very technical vocabulary.",
                "Choose a concept you can explain clearly.",
            ],
        ),
        Stage(
            name="practical_example",
            objective="Give one real-life example.",
            ai_role="Classmate asking for an example",
            keywords=["example", "price", "salary", "shopping", "service"],
            advance_criteria="Student gives one real-life example linked to the concept.",
            hints=[
                "Use a familiar example such as shopping or transport.",
                "Connect the example back to the concept.",
                "Keep it short.",
            ],
        ),
        Stage(
            name="useful_takeaway",
            objective="State why the concept matters in everyday decisions.",
            ai_role="Classmate asking why it matters",
            keywords=["matter", "decision", "budget", "everyday", "understand"],
            advance_criteria="Student explains why the concept matters for simple decisions.",
            hints=[
                "Mention budgeting, prices, or choices.",
                "Use clear cause-and-effect language.",
                "End with one takeaway.",
            ],
        ),
    ],
    success_message="Good job. You explained the concept clearly and connected it to everyday decisions.",
)

SCENARIOS["supply_and_demand"] = Scenario(
    id="supply_and_demand",
    title="Supply and Demand",
    description="Explain price changes using supply, demand, and shortage language.",
    difficulty="A2-B1",
    context="You are explaining a market change after a lesson on supply and demand.",
    student_role="Student explaining market movement",
    ai_role="Classmate",
    stages=[
        Stage(
            name="market_change",
            objective="Describe what changed in the market.",
            ai_role="Classmate asking what happened",
            keywords=["price", "market", "change", "buyers", "goods"],
            advance_criteria="Student describes a clear market change.",
            hints=[
                "Start with prices went up or demand fell.",
                "Mention one clear change.",
                "Use simple language.",
            ],
        ),
        Stage(
            name="reasoning",
            objective="Explain the change using supply and demand.",
            ai_role="Classmate asking why the change happened",
            keywords=["supply", "demand", "shortage", "availability", "reason"],
            advance_criteria="Student explains the reason with supply or demand language.",
            hints=[
                "Use because, so, or when.",
                "Mention shortage or stronger demand.",
                "Keep it short and direct.",
            ],
        ),
        Stage(
            name="prediction",
            objective="Give a simple market prediction.",
            ai_role="Classmate asking what may happen next",
            keywords=["next", "future", "predict", "stabilize", "price"],
            advance_criteria="Student gives one prediction or piece of advice.",
            hints=[
                "Use may, might, or could.",
                "Focus on future price or supply changes.",
                "End with one clear idea.",
            ],
        ),
    ],
    success_message="Nicely done. You explained supply and demand in clear, practical English.",
)

SCENARIOS["personal_finance"] = Scenario(
    id="personal_finance",
    title="Personal Finance",
    description="Practice budgeting, salary talk, saving, and spending decisions.",
    difficulty="A2-B1",
    context="You are helping a classmate make a simple monthly budget for study and daily life.",
    student_role="Student giving money advice",
    ai_role="Classmate",
    stages=[
        Stage(
            name="expenses",
            objective="Identify common monthly expenses.",
            ai_role="Classmate asking where money usually goes",
            keywords=["rent", "food", "transport", "salary", "expenses"],
            advance_criteria="Student names at least two common expenses.",
            hints=[
                "Think about transport, food, rent, or study costs.",
                "Use simple lists or short sentences.",
                "Group similar expenses together.",
            ],
        ),
        Stage(
            name="budgeting_tips",
            objective="Give one or two useful budgeting tips.",
            ai_role="Classmate asking how to manage money better",
            keywords=["budget", "save", "plan", "spending", "priority"],
            advance_criteria="Student suggests at least one budgeting tip.",
            hints=[
                "Use should, can, or try to.",
                "Mention saving, planning, or limits.",
                "Keep the advice practical.",
            ],
        ),
        Stage(
            name="simple_plan",
            objective="Agree on a short action plan.",
            ai_role="Classmate asking what to do next",
            keywords=["next step", "plan", "week", "month", "goal"],
            advance_criteria="Student proposes a simple next step or goal.",
            hints=[
                "Use this month or next week.",
                "Set one realistic goal.",
                "End with a positive summary.",
            ],
        ),
    ],
    success_message="Strong work. You used clear English to explain spending and build a realistic budget plan.",
)

SCENARIOS["trade_and_markets"] = Scenario(
    id="trade_and_markets",
    title="Trade and Markets",
    description="Talk about buying, selling, shortages, and market changes.",
    difficulty="A2-B1",
    context="You are discussing trade and market conditions after reading about buying, selling, and shortages.",
    student_role="Student explaining trade patterns",
    ai_role="Classmate",
    stages=[
        Stage(
            name="trade_activity",
            objective="Describe a simple trade or market situation.",
            ai_role="Classmate asking what is happening in the market",
            keywords=["trade", "market", "buyer", "seller", "goods"],
            advance_criteria="Student describes a market or trade situation clearly.",
            hints=[
                "Mention buyers, sellers, or product movement.",
                "Keep the situation concrete.",
                "Use simple present or past clearly.",
            ],
        ),
        Stage(
            name="business_effect",
            objective="Explain one business effect of the situation.",
            ai_role="Classmate asking why it matters for business",
            keywords=["effect", "price", "profit", "shortage", "opportunity"],
            advance_criteria="Student explains one business effect.",
            hints=[
                "Think about prices, supply, or customer demand.",
                "Use because to explain impact.",
                "Keep the answer practical.",
            ],
        ),
        Stage(
            name="recommendation",
            objective="Give one practical recommendation.",
            ai_role="Classmate asking what a business should do next",
            keywords=["recommend", "adjust", "buy", "sell", "plan"],
            advance_criteria="Student gives one business recommendation.",
            hints=[
                "Suggest a clear action.",
                "Connect it to the market condition.",
                "End decisively.",
            ],
        ),
    ],
    success_message="Excellent. You connected market language with practical business decisions.",
)


def get_scenario(scenario_id: str) -> Optional[Scenario]:
    return SCENARIOS.get(scenario_id)


def list_scenarios(difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    scenarios = SCENARIOS.values()
    if difficulty:
        scenarios = [scenario for scenario in scenarios if scenario.difficulty == difficulty]
    return [
        {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "difficulty": scenario.difficulty,
            "stages": len(scenario.stages),
        }
        for scenario in scenarios
    ]
