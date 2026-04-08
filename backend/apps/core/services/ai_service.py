import json
from dataclasses import dataclass

from django.conf import settings

from groq import Groq


@dataclass
class AIResponse:
    answer: str
    examples: list[str]
    related_topics: list[str]


def _parse_response(content: str) -> AIResponse:
    content = _strip_markdown_json(content)
    payload = json.loads(content)
    return AIResponse(
        answer=payload["answer"],
        examples=list(payload.get("examples", []))[:5],
        related_topics=list(payload.get("related_topics", []))[:5],
    )


def _strip_markdown_json(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n", 1)
        if len(lines) > 1:
            content = lines[1]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def ask_ai(question: str, topic_context: str | None = None) -> AIResponse:
    prompt_context = topic_context or "general academic support"
    client = Groq(api_key=settings.GROQ_API_KEY)

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic tutor. Return only valid JSON with keys answer, examples, related_topics. "
                    "Make the answer concise, clear, and useful."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Topic context: {prompt_context}\n"
                    f"Question: {question}\n"
                    "Return JSON only."
                ),
            },
        ],
    )
    content = response.choices[0].message.content or ""
    return _parse_response(content)


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
                    "Each question must have question_text, option_a, option_b, option_c, option_d, correct_option."
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {topic}\nDifficulty: {difficulty}\nQuestion count: {total_questions}",
            },
        ],
    )
    content = response.choices[0].message.content or ""
    content = _strip_markdown_json(content)
    return json.loads(content)
