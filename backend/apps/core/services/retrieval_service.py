from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings

from tavily import TavilyClient



@dataclass
class RetrievalPayload:
    context: str | None
    citations: list[dict]
    confidence: float
    source_type: str
    fallback_used: bool


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


def _tavily_sdk_search(question: str, max_results: int, api_key: str) -> list[dict]:
    if TavilyClient is None:
        return []

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=question,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
    except Exception:
        return []

    if isinstance(response, dict):
        results = response.get("results", [])
    else:
        results = getattr(response, "results", [])

    normalized: list[dict] = []
    for item in results[:max_results]:
        normalized.append(
            {
                "title": item.get("title") or "Web Source",
                "snippet": (item.get("content") or item.get("snippet") or "")[:240],
                "url": item.get("url") or "",
                "score": float(item.get("score") or 0.6),
                "source": "web",
            }
        )
    return normalized


def _fetch_web_results(question: str, max_results: int = 3) -> list[dict]:
    if not getattr(settings, "WEB_FALLBACK_ENABLED", False):
        return []

    api_key = getattr(settings, "TAVILY_API_KEY", "")
    if not api_key:
        return []

    sdk_results = _tavily_sdk_search(question, max_results, api_key)
    if sdk_results:
        return sdk_results

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


def retrieve_context(question: str, user: User, force_web: bool = False) -> RetrievalPayload:
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

    return RetrievalPayload(
        context=None,
        citations=[],
        confidence=0.0,
        source_type="none",
        fallback_used=False,
    )
