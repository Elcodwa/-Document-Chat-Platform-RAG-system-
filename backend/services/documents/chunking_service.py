"""
Splits extracted document text into overlapking chunks suitable for
embedding + retrieval.

This is a small, dependency-free re-implementation of the common
"recursive character splitter" pattern: try to break on paragraph
boundaries first, then lines, then sentences, then words, only falling
back to a hard character cut if nothing else fits. Overlap between
consecutive chunks helps avoid losing context at a chunk boundary (e.g. a
sentence that starts a fact in one chunk and finishes it in the next).

Token counts are approximated as ~4 characters per token, which is close
enough for chunk-sizing purposes without pulling in a full tokenizer.
"""
from dataclasses import dataclass

_CHARS_PER_TOKEN = 4
_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    index: int
    content: str
    page_number: int | None


def chunk_pages(pages: list[tuple[int | None, str]], *, chunk_size_tokens: int, chunk_overlap_tokens: int) -> list[Chunk]:
    """
    `pages` is a list of (page_number, text). Each page is chunked
    independently so a page_number can always be attached to a chunk for
    citations - text never gets merged across a page boundary.
    """
    chunk_size_chars = max(chunk_size_tokens * _CHARS_PER_TOKEN, 200)
    overlap_chars = min(chunk_overlap_tokens * _CHARS_PER_TOKEN, chunk_size_chars // 2)

    chunks: list[Chunk] = []
    index = 0
    for page_number, text in pages:
        text = text.strip()
        if not text:
            continue
        for piece in _split_text(text, chunk_size_chars, overlap_chars):
            piece = piece.strip()
            if piece:
                chunks.append(Chunk(index=index, content=piece, page_number=page_number))
                index += 1
    return chunks


def _split_text(text: str, chunk_size_chars: int, overlap_chars: int) -> list[str]:
    if len(text) <= chunk_size_chars:
        return [text]

    pieces = _recursive_split(text, _SEPARATORS, chunk_size_chars)
    return _merge_with_overlap(pieces, chunk_size_chars, overlap_chars)


def _recursive_split(text: str, separators: list[str], chunk_size_chars: int) -> list[str]:
    if len(text) <= chunk_size_chars:
        return [text]

    if not separators:
        # Last resort: hard character cut.
        return [text[i : i + chunk_size_chars] for i in range(0, len(text), chunk_size_chars)]

    sep, *rest = separators
    parts = text.split(sep)
    if len(parts) == 1:
        return _recursive_split(text, rest, chunk_size_chars)

    result: list[str] = []
    for part in parts:
        if len(part) > chunk_size_chars:
            result.extend(_recursive_split(part, rest, chunk_size_chars))
        else:
            result.append(part)
    return result


def _merge_with_overlap(pieces: list[str], chunk_size_chars: int, overlap_chars: int) -> list[str]:
    """Greedily pack small pieces back together up to chunk_size_chars,
    carrying `overlap_chars` of trailing text into the next chunk."""
    merged: list[str] = []
    current = ""

    for piece in pieces:
        candidate = f"{current} {piece}".strip() if current else piece
        if len(candidate) <= chunk_size_chars:
            current = candidate
            continue

        if current:
            merged.append(current)
            tail = current[-overlap_chars:] if overlap_chars else ""
            current = f"{tail} {piece}".strip() if tail else piece
        else:
            # A single piece is already too big (shouldn't normally happen
            # after recursive splitting, but guard anyway).
            merged.append(piece[:chunk_size_chars])
            current = piece[chunk_size_chars - overlap_chars :] if overlap_chars else ""

    if current:
        merged.append(current)

    return merged
