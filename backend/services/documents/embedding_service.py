"""
Generates embedding vectors locally using fastembed (ONNX runtime under
the hood) - no API key, no GPU, no per-call cost. This is what makes the
"free" requirement possible without also making document chat depend on
whatever the chat LLM provider's rate limits happen to be.

The model is loaded once per process (it's a ~100MB download the first
time a container starts, cached afterwards) and reused for every request.
"""
from functools import lru_cache

from fastembed import TextEmbedding

from app.config import get_settings

settings = get_settings()


@lru_cache
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _model().embed(texts)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
