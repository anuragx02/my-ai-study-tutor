import json
from dataclasses import dataclass

from django.conf import settings
from groq import Groq


@dataclass
class AIResponse:
    answer: str
    examples: list[str]
    related_topics: list[str]


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
            [*history, {"role": "user", "content": question}],
            model="groq/compound-mini",
        )
        return AIResponse(answer=answer, examples=[], related_topics=[])

    user_prompt = (
        f"Topic context: {topic_context or ''}\n"
        f"Question: {question}\n"
        "Return JSON only."
    )
    payload = json.loads(
        _complete(
            [
                {
                    "role": "system",
                    "content": "You are AI Study Tutor. Provide accurate, step-by-step help for studying and problem solving. Focus on accuracy, clarity, and helpful guidance.",
                },
                *history,
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
    )
    return AIResponse(
        answer=str(payload.get("answer", "")).strip(),
        examples=list(payload.get("examples", []))[:5],
        related_topics=list(payload.get("related_topics", []))[:5],
    )


def generate_quiz(topic: str, difficulty: str = "easy", total_questions: int = 5) -> dict:
    return json.loads(
        _complete(
            [
                {
                    "role": "system",
                    "content": "Generate a quiz as strict JSON only. Schema: topic, difficulty, total_questions, questions. Each question must have question_text, option_a, option_b, option_c, option_d, correct_option.",
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}\nDifficulty: {difficulty}\nQuestion count: {total_questions}",
                },
            ],
            temperature=0.2,
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


def extract_equation_to_latex(image_url: str) -> str:
    return _complete(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract the mathematical equation from this image and convert it to LaTeX format. Return ONLY the LaTeX code (wrapped in $ for inline or $$ for block math). Do not include any explanation or markdown formatting, just the LaTeX equation itself.",
                    },
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.3,
        max_completion_tokens=512,
        top_p=1,
        stream=False,
    )
