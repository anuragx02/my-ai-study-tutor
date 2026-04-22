from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievalPayload:
    context: str | None
    citations: list[dict]
    confidence: float
    source_type: str


def retrieve_context(question: str, user, force_web: bool = False) -> RetrievalPayload:
    if force_web:
        # Web mode flag consumed by ask_ai to switch to the retrieval-capable model path.
        return RetrievalPayload(
            context="WEB_MODE_ENABLED",
            citations=[],
            confidence=1.0,
            source_type="web",
        )

    return RetrievalPayload(
        context=None,
        citations=[],
        confidence=0.0,
        source_type="none",
    )
