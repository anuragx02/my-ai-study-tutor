from __future__ import annotations

from backend.apps.core.models import KnowledgeBase, KnowledgeBaseChunk


def _split_words(text: str) -> list[str]:
    return [word for word in (text or "").split() if word]


def chunk_text(text: str, chunk_size_chars: int = 1200, overlap_chars: int = 200) -> list[str]:
    words = _split_words(text)
    if not words:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(words):
        current_words: list[str] = []
        current_len = 0
        index = start

        while index < len(words):
            word = words[index]
            separator_len = 1 if current_words else 0
            projected = current_len + separator_len + len(word)
            if projected > chunk_size_chars and current_words:
                break
            current_words.append(word)
            current_len = projected
            index += 1

        if not current_words:
            break

        chunk = " ".join(current_words).strip()
        if chunk:
            chunks.append(chunk)

        if index >= len(words):
            break

        if overlap_chars <= 0:
            start = index
            continue

        overlap_len = 0
        back_index = index - 1
        while back_index >= start:
            extra = len(words[back_index]) + (1 if overlap_len else 0)
            if overlap_len + extra > overlap_chars:
                break
            overlap_len += extra
            back_index -= 1
        start = max(back_index + 1, start + 1)

    return chunks


def sync_document_chunks(document: KnowledgeBase, chunk_size_chars: int = 1200, overlap_chars: int = 200) -> int:
    chunks = chunk_text(document.file_text, chunk_size_chars=chunk_size_chars, overlap_chars=overlap_chars)

    KnowledgeBaseChunk.objects.filter(knowledge_base=document).delete()

    if not chunks:
        return 0

    batch = [
        KnowledgeBaseChunk(
            knowledge_base=document,
            chunk_index=index,
            chunk_text=chunk,
            token_count=max(1, len(chunk.split())),
            metadata={},
        )
        for index, chunk in enumerate(chunks)
    ]
    KnowledgeBaseChunk.objects.bulk_create(batch, batch_size=200)
    return len(batch)
