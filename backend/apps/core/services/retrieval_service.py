from __future__ import annotations

from dataclasses import dataclass
import re

import requests
from django.conf import settings

from backend.apps.core.models import KnowledgeBase, KnowledgeBaseChunk, User
from backend.apps.core.services.chunk_service import sync_document_chunks


@dataclass
class RetrievalPayload:
    context: str | None
    citations: list[dict]
    confidence: float
    source_type: str
    fallback_used: bool


def _question_terms(question: str) -> list[str]:
    stop_terms = {
        "the", "and", "for", "with", "from", "that", "this", "what", "where", "when", "which", "how", "are",
        "hey", "hello", "hi", "tutor", "please", "thanks", "thank", "can", "could", "would", "you", "about",
    }
    terms = []
    for token in question.split():
        cleaned = token.strip(".,:;!?()[]{}\"'").lower()
        if len(cleaned) < 3:
            continue
        if cleaned in stop_terms:
            continue
        terms.append(cleaned)
    return terms


def _is_probably_academic(question: str, terms: list[str]) -> bool:
    if not question or not question.strip():
        return False

    lowered = question.lower().strip()
    greeting_patterns = [
        r"^(hey|hi|hello)\b",
        r"^(hey|hi|hello)\s+tutor\b",
        r"^how are you\b",
        r"^what's up\b|^whats up\b",
    ]
    if any(re.search(pattern, lowered) for pattern in greeting_patterns):
        return False

    if len(terms) == 0:
        return False

    return True


def _is_live_info_query(question: str) -> bool:
    lowered = (question or "").lower()
    live_markers = {
        "today", "now", "current", "latest", "breaking", "news", "headline", "score", "match",
        "won", "price", "weather", "date", "time", "rate", "result", "update",
    }
    return any(marker in lowered for marker in live_markers)


def _tavily_request(url: str, payload: dict, api_key: str) -> list[dict]:
    request_variants = [
        {
            "headers": {"Content-Type": "application/json"},
            "json": {**payload, "api_key": api_key},
        },
        {
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            "json": payload,
        },
        {
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
            "json": payload,
        },
    ]

    for variant in request_variants:
        try:
            response = requests.post(
                url,
                json=variant["json"],
                headers=variant["headers"],
                timeout=(5, 10),
            )
            if response.status_code >= 400:
                continue
            data = response.json() or {}
            return data.get("results", [])
        except requests.RequestException:
            continue
        except ValueError:
            continue

    return []


def _score_chunk(chunk_text: str, terms: list[str]) -> float:
    if not terms:
        return 0.0

    lowered = chunk_text.lower()
    matched = sum(1 for term in terms if term in lowered)
    return matched / len(terms)


def _fetch_web_results(question: str, max_results: int = 3) -> list[dict]:
    if not getattr(settings, "WEB_FALLBACK_ENABLED", False):
        return []

    api_key = getattr(settings, "TAVILY_API_KEY", "")
    if not api_key:
        return []

    base_url = getattr(settings, "TAVILY_API_BASE", "https://api.tavily.com")
    url = f"{base_url.rstrip('/')}/search"

    try:
        payload = {
            "query": question,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }
        results = _tavily_request(url, payload, api_key)
        normalized: list[dict] = []
        for item in results[:max_results]:
            normalized.append(
                {
                    "title": item.get("title") or "Web Source",
                    "snippet": (item.get("content") or "")[:240],
                    "url": item.get("url") or "",
                    "score": float(item.get("score") or 0.6),
                    "source": "web",
                }
            )
        return normalized
    except Exception:
        return []


def _web_fallback_unavailable_reason() -> str | None:
    if not getattr(settings, "WEB_FALLBACK_ENABLED", False):
        return "web fallback is disabled in backend settings"

    api_key = getattr(settings, "TAVILY_API_KEY", "")
    if not api_key:
        return "Tavily API key is missing in the running backend environment"

    return None


def _ensure_user_chunks(user: User) -> None:
    if KnowledgeBaseChunk.objects.filter(knowledge_base__user=user).exists():
        return

    for document in KnowledgeBase.objects.filter(user=user):
        sync_document_chunks(
            document,
            chunk_size_chars=getattr(settings, "KB_CHUNK_SIZE_CHARS", 1200),
            overlap_chars=getattr(settings, "KB_CHUNK_OVERLAP_CHARS", 200),
        )


def retrieve_context(question: str, user: User) -> RetrievalPayload:
    terms = _question_terms(question)
    force_web = _is_live_info_query(question)

    if force_web:
        unavailable_reason = _web_fallback_unavailable_reason()
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

        web_citations = _fetch_web_results(question, max_results=3)
        if web_citations:
            web_context = "\n\n".join(
                f"[WEB:{item['title']}] {item['snippet']}"
                for item in web_citations
            )
            return RetrievalPayload(
                context=web_context,
                citations=web_citations,
                confidence=0.8,
                source_type="web",
                fallback_used=True,
            )

        return RetrievalPayload(
            context=(
                "Live web data is required for this question, but web sources were not available at the moment. "
                "Respond clearly that current information could not be retrieved and ask the user to retry."
            ),
            citations=[],
            confidence=0.0,
            source_type="web",
            fallback_used=False,
        )

    if not _is_probably_academic(question, terms):
        return RetrievalPayload(
            context=None,
            citations=[],
            confidence=0.0,
            source_type="none",
            fallback_used=False,
        )

    _ensure_user_chunks(user)

    top_k = getattr(settings, "KB_TOP_K", 4)
    threshold = getattr(settings, "KB_CONFIDENCE_THRESHOLD", 0.45)

    scored_chunks: list[tuple[KnowledgeBaseChunk, float]] = []
    chunks = KnowledgeBaseChunk.objects.filter(knowledge_base__user=user).select_related("knowledge_base")

    for chunk in chunks:
        score = _score_chunk(chunk.chunk_text, terms)
        if score > 0:
            scored_chunks.append((chunk, score))

    scored_chunks.sort(key=lambda item: item[1], reverse=True)
    selected = scored_chunks[:top_k]

    kb_citations = [
        {
            "source": "kb",
            "document_id": chunk.knowledge_base_id,
            "document_title": chunk.knowledge_base.title,
            "chunk_index": chunk.chunk_index,
            "snippet": chunk.chunk_text[:240],
            "score": round(score, 4),
        }
        for chunk, score in selected
    ]

    kb_context = "\n\n".join(
        f"[{chunk.knowledge_base.title}#{chunk.chunk_index}] {chunk.chunk_text[:650]}"
        for chunk, _ in selected
    )

    confidence = round(sum(score for _, score in selected) / len(selected), 4) if selected else 0.0

    fallback_used = False
    web_citations: list[dict] = []
    web_context = ""
    if force_web or confidence < threshold:
        web_citations = _fetch_web_results(question, max_results=3)
        fallback_used = bool(web_citations)
        web_context = "\n\n".join(
            f"[WEB:{item['title']}] {item['snippet']}"
            for item in web_citations
        )

    citations = kb_citations + web_citations

    if kb_citations and web_citations:
        source_type = "mixed"
    elif kb_citations:
        source_type = "kb"
    elif web_citations:
        source_type = "web"
    else:
        source_type = "none"

    context_parts = [part for part in [kb_context, web_context] if part]
    context = "\n\n".join(context_parts) if context_parts else None

    return RetrievalPayload(
        context=context,
        citations=citations,
        confidence=confidence,
        source_type=source_type,
        fallback_used=fallback_used,
    )
