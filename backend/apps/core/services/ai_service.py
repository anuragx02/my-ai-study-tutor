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


def _is_math_question(question: str) -> bool:
    text = (question or "").lower().strip()
    if not text:
        return False

    keyword_markers = {
        "math",
        "mathematics",
        "algebra",
        "geometry",
        "trigonometry",
        "calculus",
        "differentiate",
        "derivative",
        "integrate",
        "integral",
        "equation",
        "simplify",
        "solve",
        "factor",
        "quadratic",
        "probability",
        "statistics",
        "matrix",
    }
    if any(marker in text for marker in keyword_markers):
        return True

    symbol_patterns = [
        r"\d+\s*[+\-*/^=]\s*\d+",
        r"\bx\b|\by\b|\bz\b",
        r"\b(sin|cos|tan|log|ln)\b",
        r"\b\d+\s*%\b",
    ]
    return any(re.search(pattern, text) for pattern in symbol_patterns)


def _parse_response(content: str) -> AIResponse:
    content = _strip_markdown_json(content)
    payload = json.loads(content)
    return AIResponse(
        answer=str(payload.get("answer", "")).strip(),
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


def ask_ai(question: str, topic_context: str | None = None, is_academic: bool = True) -> AIResponse:
    prompt_context = topic_context or "general academic support"
    is_math = _is_math_question(question)

    if topic_context and "Live web data is required" in topic_context:
        return AIResponse(
            answer=(
                "I could not fetch live web data right now for that current-events query. "
                "Please retry in a moment, and I will check the latest sources."
            ),
            examples=[],
            related_topics=[],
        )

    client = Groq(api_key=settings.GROQ_API_KEY)

    if is_academic:
        if is_math:
            system_prompt = (
                "You are an academic math tutor. Return only valid JSON with keys answer, examples, related_topics. "
                "Give a clear step-by-step solution using numbered steps. "
                "Explain each transformation briefly and include the final result on a new line starting with 'Final answer:'. "
                "Use examples and related_topics only when genuinely useful. Keep them empty arrays when not needed."
            )
        else:
            system_prompt = (
                "You are an academic tutor. Return only valid JSON with keys answer, examples, related_topics. "
                "Use examples and related_topics only when genuinely useful. Keep them empty arrays when not needed. "
                "Keep the answer concise, clear, and practical."
            )
        user_prompt = (
            f"Topic context: {prompt_context}\n"
            f"Question: {question}\n"
            "Return JSON only."
        )
    else:
        system_prompt = (
            "You are a friendly study tutor. Return only valid JSON with keys answer, examples, related_topics. "
            "For non-academic questions, reply naturally in 1-3 sentences and gently steer the user back to study topics in the final sentence. "
            "Always return examples as [] and related_topics as [] for non-academic questions."
        )
        user_prompt = (
            f"User message: {question}\n"
            "This is non-academic. Reply conversationally and add a gentle study redirection. Return JSON only."
        )

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )
    content = response.choices[0].message.content or ""
    parsed = _parse_response(content)
    if not parsed.answer:
        fallback_answer = "I can help with that. If you want, share a study topic or question and I will guide you step by step."
        return AIResponse(answer=fallback_answer, examples=[], related_topics=[])
    return parsed


def generate_chat_title(question: str) -> str:
    default_title = "New Chat"
    question = (question or "").strip()
    if not question:
        return default_title

    fallback = question[:36].strip() or default_title
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a short chat title. Return plain text only, no quotes, no punctuation at the end, "
                        "2 to 5 words maximum."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}",
                },
            ],
        )
        content = (response.choices[0].message.content or "").strip().strip('"').strip("'")
        if not content:
            return fallback

        words = content.split()
        if len(words) > 5:
            content = " ".join(words[:5])

        return content[:48].strip() or fallback
    except Exception:
        return fallback


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
