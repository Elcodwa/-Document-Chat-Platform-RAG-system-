-- Runs automatically the first time the postgres container starts (empty
-- data directory only). Connects to the app database (POSTGRES_DB, set via
-- docker-compose.yml) and enables the pgvector extension the app's
-- document_chunks.embedding column needs.
CREATE EXTENSION IF NOT EXISTS vector;
