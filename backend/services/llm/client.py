"""
A small seam around the LLM provider. Everything else in the codebase
calls `chat()` and never imports langchain_groq or groq directly - if you
later want to swap in a different provider (OpenAI, a local Ollama model,
etc.) this is the only file that needs to change.

Provider: Groq (https://console.groq.com) was chosen because it has a
genuinely free API tier with no credit card required, and is fast enough
for a responsive chat experience. See the root README for how to get a
free key.
"""
from dataclasses import dataclass

from langchain_groq import ChatGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.exceptions import LLMProviderError

settings = get_settings()


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


def _client(temperature: float | None = None) -> ChatGroq:
    if not settings.groq_api_key:
        raise LLMProviderError(
            "No GROQ_API_KEY is configured. Get a free key at https://console.groq.com/keys and set it in your .env file."
        )
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=temperature if temperature is not None else settings.llm_temperature,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def chat(messages: list[ChatMessage], *, temperature: float | None = None) -> str:
    """Single non-streaming call. Retries on transient provider errors
    (rate limits, momentary network issues) with exponential backoff."""
    try:
        client = _client(temperature)
        lc_messages = [(m.role, m.content) for m in messages]
        response = client.invoke(lc_messages)
        return response.content
    except LLMProviderError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise LLMProviderError(f"The language model provider returned an error: {exc}") from exc
