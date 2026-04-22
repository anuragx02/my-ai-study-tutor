from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings


@dataclass
class RetrievalPayload:
    context: str | None
    citations: list[dict]
    confidence: float
    source_type: str
    fallback_used: bool


def _web_mode_unavailable_reason() -> str | None:
    if not getattr(settings, "WEB_FALLBACK_ENABLED", False):
        return "web mode is disabled in backend settings"
    return None


def retrieve_context(question: str, user, force_web: bool = False) -> RetrievalPayload:
    if force_web:
        unavailable_reason = _web_mode_unavailable_reason()
        if unavailable_reason:
            return RetrievalPayload(
                context=(
                    f"Live web data is required for this question, but {unavailable_reason}. "
                    "Tell the user to configure backend env/redeploy and retry."
                ),
                citations=[],
                confidence=0.0,
                source_type="web",
                fallback_used=False,
            )

        # Web mode flag consumed by ask_ai to switch to the retrieval-capable model path.
        return RetrievalPayload(
            context="WEB_MODE_ENABLED",
            citations=[],
            confidence=1.0,
            source_type="web",
            fallback_used=False,
        )

    return RetrievalPayload(
        context=None,
        citations=[],
        confidence=0.0,
        source_type="none",
        fallback_used=False,
    )
