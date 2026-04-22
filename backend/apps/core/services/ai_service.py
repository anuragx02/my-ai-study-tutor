import json
from dataclasses import dataclass

from django.conf import settings

from groq import Groq


@dataclass
class AIResponse:
    answer: str
    examples: list[str]
    related_topics: list[str]


def ask_ai(
    question: str,
    topic_context: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    is_academic: bool = True,
) -> AIResponse:
    prompt_context = topic_context or ""
    history = conversation_history or []

    if topic_context == "WEB_MODE_ENABLED":
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="groq/compound-mini",
            messages=[
                *history,
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )
        answer = (response.choices[0].message.content or "").strip()
        return AIResponse(answer=answer, examples=[], related_topics=[])

    client = Groq(api_key=settings.GROQ_API_KEY)
    system_prompt = (
        "You are AI Study Tutor. Provide accurate, step-by-step help for studying and problem solving. "
        "Focus on accuracy, clarity, and helpful guidance."
    )
    user_prompt = (
        f"Topic context: {prompt_context}\n"
        f"Question: {question}\n"
        "Return JSON only."
    )

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            *history,
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )
    content = response.choices[0].message.content or ""
    payload = json.loads(content.strip())

    parsed = AIResponse(
        answer=str(payload.get("answer", "")).strip(),
        examples=list(payload.get("examples", []))[:5],
        related_topics=list(payload.get("related_topics", []))[:5],
    )

    return parsed


def generate_quiz(topic: str, difficulty: str = "easy", total_questions: int = 5) -> dict:
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate a quiz as JSON only. Schema: topic, difficulty, total_questions, questions. "
                    "Each question must have question_text, option_a, option_b, option_c, option_d, correct_option, explanation. "
                    "The explanation must be 1-2 concise sentences describing why the correct option is right."
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {topic}\nDifficulty: {difficulty}\nQuestion count: {total_questions}",
            },
        ],
    )
    content = (response.choices[0].message.content or "").strip()
    return json.loads(content)
