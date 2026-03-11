# roleplay_scenarios.py
"""
Defines semester-two English roleplay scenarios with multi-stage progression.
Each scenario is tied to the second-semester syllabus topics.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Stage:
    """A stage within a scenario"""
    name: str
    objective: str
    ai_role: str
    keywords: List[str]
    advance_criteria: str
    hints: List[str]


@dataclass
class Scenario:
    """A complete roleplay scenario"""
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


SCENARIOS["modern_zoo"] = Scenario(
    id="modern_zoo",
    title="Modern Zoo",
    description="Discuss how modern zoos should care for animals and teach visitors.",
    difficulty="intermediate",
    context="You are discussing modern zoos with a classmate after reading about animal protection and public education.",
    student_role="Student sharing an opinion",
    ai_role="Classmate",
    stages=[
        Stage(
            name="opening_opinion",
            objective="Share your first opinion about whether modern zoos are useful.",
            ai_role="Curious classmate asking what you think",
            keywords=["zoo", "animals", "protect", "visitors", "education"],
            advance_criteria="Student gives an opinion about zoos and mentions at least one reason.",
            hints=[
                "Start with a clear opinion such as 'I think modern zoos can...'",
                "Mention one advantage or one concern.",
                "Use simple linking words like because, but, and so."
            ]
        ),
        Stage(
            name="supporting_reasons",
            objective="Explain one benefit and one possible problem.",
            ai_role="Classmate asking for more detail",
            keywords=["endangered", "habitat", "learning", "care", "problems"],
            advance_criteria="Student explains a benefit or concern with a short example.",
            hints=[
                "You can mention endangered animals, education, or animal welfare.",
                "Try using 'for example' to add detail.",
                "Keep your answer balanced and clear."
            ]
        ),
        Stage(
            name="final_view",
            objective="Suggest how zoos could improve in the future.",
            ai_role="Classmate asking for your final conclusion",
            keywords=["improve", "better", "care", "programs", "future"],
            advance_criteria="Student suggests at least one improvement or gives a final conclusion.",
            hints=[
                "Use 'They should...' or 'It would be better if...'.",
                "Focus on animal care or education for visitors.",
                "End with a short conclusion."
            ]
        )
    ],
    success_message="Nice work. You discussed the topic clearly and supported your opinion with useful ideas."
)

SCENARIOS["education_systems"] = Scenario(
    id="education_systems",
    title="Education Systems",
    description="Compare school systems, subjects, and learning methods in clear English.",
    difficulty="intermediate",
    context="You are talking with an exchange student about how education systems work in different countries.",
    student_role="Student comparing systems",
    ai_role="Exchange student",
    stages=[
        Stage(
            name="describe_system",
            objective="Describe the main structure of your education system.",
            ai_role="Exchange student asking how school works in your country",
            keywords=["school", "education", "subjects", "students", "system"],
            advance_criteria="Student describes the system with at least one concrete detail.",
            hints=[
                "Mention school stages, subjects, or exams.",
                "Use present simple for facts.",
                "Keep it organized with two or three points."
            ]
        ),
        Stage(
            name="compare_features",
            objective="Compare one strength and one weakness.",
            ai_role="Exchange student comparing your answer with another country",
            keywords=["better", "different", "advantages", "problems", "compare"],
            advance_criteria="Student compares two ideas and explains one strength or weakness.",
            hints=[
                "Use compare words like more, less, better, similar, different.",
                "Explain why you think something is useful or difficult.",
                "One short example is enough."
            ]
        ),
        Stage(
            name="suggest_change",
            objective="Suggest one improvement for the system.",
            ai_role="Exchange student asking what should change",
            keywords=["improve", "change", "students", "teachers", "skills"],
            advance_criteria="Student suggests at least one realistic improvement.",
            hints=[
                "Start with 'I would improve...' or 'Schools should...'.",
                "Focus on students, teachers, or practical skills.",
                "Keep the suggestion realistic."
            ]
        )
    ],
    success_message="Great job. You compared education systems clearly and suggested thoughtful improvements."
)

SCENARIOS["university_life"] = Scenario(
    id="university_life",
    title="University Life",
    description="Talk about routines, study habits, and challenges in university life.",
    difficulty="beginner",
    context="You are speaking with a first-year student who wants advice about university life.",
    student_role="Experienced student",
    ai_role="First-year student",
    stages=[
        Stage(
            name="daily_routine",
            objective="Describe your university routine and responsibilities.",
            ai_role="New student asking what a normal week looks like",
            keywords=["classes", "study", "schedule", "campus", "routine"],
            advance_criteria="Student describes a routine with at least two activities.",
            hints=[
                "Mention classes, homework, clubs, or commuting.",
                "Use time phrases like every day, usually, after class.",
                "Speak in simple present tense."
            ]
        ),
        Stage(
            name="common_challenges",
            objective="Explain one common challenge and how you handle it.",
            ai_role="New student asking what is difficult",
            keywords=["time", "stress", "deadlines", "friends", "balance"],
            advance_criteria="Student names one challenge and explains how they handle it.",
            hints=[
                "Examples: time management, deadlines, stress, making friends.",
                "Use 'It can be hard to...' and 'I usually...'.",
                "Give one practical strategy."
            ]
        ),
        Stage(
            name="advice",
            objective="Give clear advice to a new student.",
            ai_role="New student asking for final advice",
            keywords=["advice", "should", "helpful", "success", "plan"],
            advance_criteria="Student gives at least one clear piece of advice.",
            hints=[
                "Use should, try to, or it helps to.",
                "Keep the advice friendly and practical.",
                "A short list is fine."
            ]
        )
    ],
    success_message="Well done. You explained university life clearly and gave supportive advice."
)

SCENARIOS["english_learning_games"] = Scenario(
    id="english_learning_games",
    title="Learning English",
    description="Discuss games, videos, podcasts, and authentic materials for English learning.",
    difficulty="beginner",
    context="You are talking with a classmate about useful ways to improve English outside the classroom.",
    student_role="Student sharing study ideas",
    ai_role="Classmate",
    stages=[
        Stage(
            name="favorite_tools",
            objective="Name one learning tool you like and explain why.",
            ai_role="Classmate asking what helps you learn best",
            keywords=["games", "podcasts", "videos", "articles", "practice"],
            advance_criteria="Student names one learning tool and gives a reason.",
            hints=[
                "You can mention games, podcasts, videos, or articles.",
                "Use 'I like...' or 'I prefer...' plus a reason.",
                "Keep the explanation short and clear."
            ]
        ),
        Stage(
            name="authentic_materials",
            objective="Explain how real English materials can help.",
            ai_role="Classmate asking about authentic materials",
            keywords=["authentic", "real English", "listening", "reading", "context"],
            advance_criteria="Student explains at least one benefit of authentic materials.",
            hints=[
                "Think about real accents, natural vocabulary, or cultural context.",
                "Use simple cause-and-effect language.",
                "One example is enough."
            ]
        ),
        Stage(
            name="study_plan",
            objective="Suggest a simple study plan.",
            ai_role="Classmate asking what routine they should follow",
            keywords=["plan", "weekly", "practice", "habit", "routine"],
            advance_criteria="Student suggests a short study plan or weekly habit.",
            hints=[
                "Use words like every day, twice a week, after class.",
                "Mix speaking, listening, or reading.",
                "Keep the plan realistic."
            ]
        )
    ],
    success_message="Great. You shared useful English-learning ideas and built a practical study routine."
)

SCENARIOS["festivals_and_traditions"] = Scenario(
    id="festivals_and_traditions",
    title="Festivals",
    description="Describe traditions, celebrations, and what they mean to people.",
    difficulty="intermediate",
    context="You are discussing local and international festivals, including Chinese festivals, with a classmate.",
    student_role="Student describing traditions",
    ai_role="Classmate interested in culture",
    stages=[
        Stage(
            name="introduce_festival",
            objective="Introduce a festival or tradition you know well.",
            ai_role="Classmate asking about a celebration in your culture",
            keywords=["festival", "tradition", "celebrate", "family", "culture"],
            advance_criteria="Student introduces a festival and gives basic context.",
            hints=[
                "Mention when it happens and who celebrates it.",
                "Use present simple if it happens every year.",
                "Give one or two clear details."
            ]
        ),
        Stage(
            name="activities_and_meaning",
            objective="Describe what people do and why it matters.",
            ai_role="Classmate asking what people usually do",
            keywords=["food", "activities", "meaning", "community", "family"],
            advance_criteria="Student describes activities and explains cultural meaning.",
            hints=[
                "You can mention food, clothes, music, visits, or ceremonies.",
                "Explain why the festival is important.",
                "Use linking words like also, because, and usually."
            ]
        ),
        Stage(
            name="comparison",
            objective="Compare two festivals or traditions briefly.",
            ai_role="Classmate asking how it compares with another festival",
            keywords=["similar", "different", "compare", "Chinese", "local"],
            advance_criteria="Student compares two traditions using at least one comparison word.",
            hints=[
                "Use similar, different, more, less, both, or unlike.",
                "Keep the comparison short and clear.",
                "One similarity and one difference are enough."
            ]
        )
    ],
    success_message="Excellent. You described the festival clearly and compared traditions in natural English."
)

SCENARIOS["personal_finance"] = Scenario(
    id="personal_finance",
    title="Personal Finance",
    description="Practice everyday English for budgeting, spending, and saving.",
    difficulty="intermediate",
    context="You are talking with a friend who wants help making a simple monthly budget.",
    student_role="Student giving money advice",
    ai_role="Friend",
    stages=[
        Stage(
            name="expenses",
            objective="Identify common monthly expenses.",
            ai_role="Friend asking where their money usually goes",
            keywords=["rent", "food", "transport", "study", "expenses"],
            advance_criteria="Student names at least two common expenses.",
            hints=[
                "Think about transport, food, rent, or study materials.",
                "Use simple lists or short sentences.",
                "Group similar expenses together."
            ]
        ),
        Stage(
            name="budgeting_tips",
            objective="Give one or two useful budgeting tips.",
            ai_role="Friend asking how to manage money better",
            keywords=["budget", "save", "plan", "spending", "priority"],
            advance_criteria="Student suggests at least one budgeting tip.",
            hints=[
                "Use should, can, or try to.",
                "Mention saving, planning, or setting limits.",
                "Keep the advice practical."
            ]
        ),
        Stage(
            name="simple_plan",
            objective="Agree on a short action plan.",
            ai_role="Friend asking what to do next",
            keywords=["next step", "plan", "week", "month", "goal"],
            advance_criteria="Student proposes a simple next step or goal.",
            hints=[
                "Use 'This month...' or 'Next week...'.",
                "Set one realistic goal.",
                "End with a positive summary."
            ]
        )
    ],
    success_message="Strong work. You used clear English to explain spending and build a realistic budget plan."
)

SCENARIOS["trade_and_markets"] = Scenario(
    id="trade_and_markets",
    title="Trade and Markets",
    description="Explain prices, buying, selling, supply, and demand in simple English.",
    difficulty="intermediate",
    context="You are discussing a market situation with a classmate after studying trade, prices, and demand.",
    student_role="Student explaining market changes",
    ai_role="Classmate",
    stages=[
        Stage(
            name="market_change",
            objective="Describe what changed in the market.",
            ai_role="Classmate asking what happened to prices or sales",
            keywords=["price", "market", "buy", "sell", "change"],
            advance_criteria="Student describes a change in price, demand, or sales.",
            hints=[
                "Start with 'Prices went up...' or 'Demand fell...'.",
                "Mention one clear change.",
                "Use past or present clearly."
            ]
        ),
        Stage(
            name="explain_reason",
            objective="Explain the change using supply or demand.",
            ai_role="Classmate asking why the change happened",
            keywords=["supply", "demand", "shortage", "more buyers", "fewer goods"],
            advance_criteria="Student explains the reason with supply or demand language.",
            hints=[
                "Use because, so, or when.",
                "Mention more buyers, fewer goods, or lower demand.",
                "Keep the explanation simple."
            ]
        ),
        Stage(
            name="advice_or_prediction",
            objective="Give advice or predict what may happen next.",
            ai_role="Classmate asking what people should expect next",
            keywords=["should", "could", "next", "future", "predict"],
            advance_criteria="Student gives advice or a simple prediction.",
            hints=[
                "You can use may, might, could, or should.",
                "Focus on buyers, sellers, or prices.",
                "End with one clear idea."
            ]
        )
    ],
    success_message="Nicely done. You explained trade and market ideas in clear, understandable English."
)


def get_scenario(scenario_id: str) -> Optional[Scenario]:
    return SCENARIOS.get(scenario_id)


def list_scenarios(difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
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
