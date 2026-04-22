import json
import re
from dataclasses import dataclass

from django.conf import settings

from groq import Groq


@dataclass
class AIResponse:
    answer: str
    examples: list[str]
    related_topics: list[str]


def _extract_json_payload(content: str) -> str:
    text = (content or "").strip()
    if not text:
        raise ValueError("Empty AI response")

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    object_start = text.find("{")
    object_end = text.rfind("}")
    array_start = text.find("[")
    array_end = text.rfind("]")

    candidates = []
    if object_start != -1 and object_end != -1 and object_end > object_start:
        candidates.append(text[object_start : object_end + 1])
    if array_start != -1 and array_end != -1 and array_end > array_start:
        candidates.append(text[array_start : array_end + 1])

    for candidate in candidates:
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            continue

    raise ValueError("AI response did not contain valid JSON")


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
    payload = json.loads(_extract_json_payload(content))

    parsed = AIResponse(
        answer=str(payload.get("answer", "")).strip(),
        examples=list(payload.get("examples", []))[:5],
        related_topics=list(payload.get("related_topics", []))[:5],
    )

    return parsed


def generate_quiz(topic: str, difficulty: str = "easy", total_questions: int = 5) -> dict:
    client = Groq(api_key=settings.GROQ_API_KEY)
    messages = [
        {
            "role": "system",
            "content": (
                "Generate a quiz as strict JSON only. Do not wrap the response in markdown fences or add any extra text. "
                "Schema: topic, difficulty, total_questions, questions. "
                "Each question must have question_text, option_a, option_b, option_c, option_d, correct_option."
            ),
        },
        {
            "role": "user",
            "content": f"Topic: {topic}\nDifficulty: {difficulty}\nQuestion count: {total_questions}",
        },
    ]

    last_error = None
    for attempt in range(2):
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            temperature=0.1 if attempt else 0.4,
            messages=messages,
        )
        content = response.choices[0].message.content or ""
        try:
            return json.loads(_extract_json_payload(content))
        except ValueError as error:
            last_error = error
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You must respond with valid JSON only. No markdown, no code fences, no commentary. "
                        "Return a single JSON object matching the required quiz schema."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Fix this invalid response into valid JSON for a quiz about {topic} at {difficulty} difficulty with {total_questions} questions. "
                        f"Invalid response:\n{content}"
                    ),
                },
            ]

    raise ValueError("AI returned invalid JSON") from last_error
