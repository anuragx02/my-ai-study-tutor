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
    if object_start != -1 and object_end != -1 and object_end > object_start:
        candidate = text[object_start : object_end + 1]
        json.loads(candidate)
        return candidate

    raise ValueError("AI response did not contain valid JSON")


def _complete(messages: list[dict], model: str | None = None, temperature: float = 0.2, **kwargs) -> str:
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=model or settings.GROQ_MODEL,
        temperature=temperature,
        messages=messages,
        **kwargs,
    )
    return (response.choices[0].message.content or "").strip()


def ask_ai(
    question: str,
    topic_context: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    is_academic: bool = True,
) -> AIResponse:
    history = conversation_history or []

    if topic_context == "WEB_MODE_ENABLED":
        answer = _complete(
            [
                {
                    "role": "system",
                    "content": "You are AI Study Tutor. Use clear Markdown with short paragraphs, numbered steps, and LaTeX for math.",
                },
                *history,
                {"role": "user", "content": question},
            ],
            model="groq/compound-mini",
        )
        return AIResponse(answer=answer, examples=[], related_topics=[])

    user_prompt = f"Study context: {topic_context or ''}\nQuestion: {question}".strip()
    answer = _complete(
        [
            {
                "role": "system",
                "content": "You are AI Study Tutor. Provide accurate, step-by-step help for studying and problem solving. Use clear Markdown with short paragraphs, numbered steps, and LaTeX for math.",
            },
            *history,
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return AIResponse(answer=answer, examples=[], related_topics=[])


def generate_quiz(focus: str, difficulty: str = "easy", total_questions: int = 5) -> dict:
    return json.loads(
        _extract_json_payload(
            _complete(
                [
                    {
                        "role": "system",
                        "content": "Generate a quiz as strict JSON only. Schema: topic, difficulty, total_questions, questions. Each question must have question_text, option_a, option_b, option_c, option_d, correct_option.",
                    },
                    {
                        "role": "user",
                        "content": f"Focus: {focus}\nDifficulty: {difficulty}\nQuestion count: {total_questions}",
                    },
                ],
                temperature=0.2,
            )
        )
    )


def generate_answer_explanation(question_text: str, correct_option: str, correct_option_text: str) -> str:
    return _complete(
        [
            {
                "role": "system",
                "content": "You are a study tutor. Explain why the provided correct option is correct in 2-3 concise sentences. Do not use markdown or bullet points.",
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question_text}\n"
                    f"Correct option: {correct_option}\n"
                    f"Correct option text: {correct_option_text}"
                ),
            },
        ],
        temperature=0.2,
    )


def extract_text_from_image(image_url: str, instruction: str = "Extract all text from this image") -> str:
    return _complete(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
    )
