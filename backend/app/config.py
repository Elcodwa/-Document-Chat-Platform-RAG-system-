"""
Central application configuration.

Every setting is read from environment variables (see .env.example at the
project root). Nothing here is a secret by itself - the real secrets live
only in your local .env file, which is never committed to git.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- General ---
    app_name: str = "Text-to-SQL & Document Chat Platform"
    environment: str = "development"
    debug: bool = True

    # --- Application database (stores tenants, users, metadata, chat history) ---
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/textsql_app"
    )

    # --- Auth ---
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # --- Credential encryption (Fernet key, 32 url-safe base64 bytes) ---
    encryption_key: str = "change-me-please-generate-a-real-fernet-key=="

    # --- LLM provider (Groq free tier by default) ---
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.0

    # --- Embeddings (local, free, CPU-only) ---
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimensions: int = 384

    # --- File storage ---
    storage_path: str = "/app/storage"
    max_upload_size_mb: int = 25

    # --- SQL execution safety limits ---
    sql_max_rows: int = 500
    sql_statement_timeout_seconds: int = 10
    sql_max_query_chars: int = 4000

    # --- Chunking ---
    chunk_size_tokens: int = 400
    chunk_overlap_tokens: int = 60

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
