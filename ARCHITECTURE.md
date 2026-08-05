# Architecture

This document explains how the system is put together and, more
importantly, *why* - the design decisions here are the things worth
talking about in an interview.

## The big picture

```
┌─────────────┐      HTTP/JSON       ┌──────────────────┐
│   Next.js   │◄────────────────────►│     FastAPI       │
│  frontend   │      SSE (chat)      │     backend        │
└─────────────┘                      └─────────┬─────────┘
                                                │
                     ┌──────────────────────────┼──────────────────────────┐
                     │                          │                          │
                     ▼                          ▼                          ▼
            ┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
            │   Postgres       │      │  Live customer    │      │   Groq LLM API    │
            │  (app metadata,  │      │  database(s)       │      │  (free tier, via   │
            │  pgvector for    │      │  (Postgres/MySQL,  │      │  LangChain)        │
            │  embeddings)     │      │  read-only queries) │      │                    │
            └─────────────────┘      └──────────────────┘      └──────────────────┘
```

Two databases matter here, and keeping them conceptually separate is the
whole point of the security model:

1. **The application database** (Postgres + pgvector) stores *our own*
   metadata: tenants, users, encrypted connection credentials, cached
   schema, uploaded document chunks + embeddings, and the full chat/audit
   history. This is the only database the backend has a persistent
   connection pool to.
2. **Live customer databases** (whatever a tenant connects) are only ever
   touched through a short-lived, purpose-built engine created per
   request (`services/database/engine_factory.py`), and only after the
   generated SQL has passed the validator. We never copy a customer's
   business data into our own database.

## Backend layers

```
api/            HTTP routing only - no business logic, just request/response wiring
schemas/        Pydantic request/response contracts
services/       Business logic (auth, database ops, documents, LLM)
repositories/   Data access - every query is tenant-scoped here, in one place
models/         SQLAlchemy ORM models
agents/         The LangGraph orchestration layer (see below)
core/           Cross-cutting concerns: security, encryption, tenant context
```

The rule that keeps this maintainable: **routes never talk to the
database directly, and services never import FastAPI.** A route calls a
service; a service calls one or more repositories. This is also why the
agent nodes in `agents/` are easy to unit-test with a fake LLM (see
`tests/`) - they're plain functions over a state dict, not framework code.

## The Text-to-SQL security model

This is the part most worth understanding in depth, because "let an LLM
write SQL and run it" is exactly the kind of feature that goes wrong in
an interesting way if you don't think through the failure modes.

**Nothing the LLM outputs is trusted.** Every generated query passes
through `services/database/query_validator.py`, which:

1. Parses the SQL into a real AST (via `sqlglot`) - not a regex check.
2. Rejects anything that isn't a single `SELECT` (optionally with CTEs).
   This catches the obvious cases (`DROP`, `DELETE`, ...) but also two
   less obvious ones found and fixed while building this: a **writable
   CTE** (`WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x`, which
   still parses with a top-level key of `"select"`), and `EXPLAIN
   ANALYZE`, which actually *executes* the statement it's supposedly just
   planning.
3. Checks every referenced table against a per-user, per-connection
   allowlist - table names the LLM invents, or system schemas like
   `pg_catalog`/`information_schema`, are rejected before anything runs.
4. Enforces column-level restrictions where they exist, including
   blocking `SELECT *` on a column-restricted table (the wildcard can't
   be checked column-by-column, so it's blocked outright).
5. **Injects row-level filters directly into the query's own AST** - not
   as a wrapper around the result. A filter like "region = 'EG'" is added
   to the `WHERE` clause of whichever scope actually references that
   table, which means it correctly reaches into joins, subqueries, and
   CTEs. The LLM never sees this filter and cannot remove or alter it,
   because it's added *after* generation, not part of the prompt.
6. Adds (or caps) a `LIMIT`, and the query that actually executes is a
   re-serialization of the validated AST - never the LLM's original text.
   This closes the gap between "what we checked" and "what runs."

If validation fails, the agent gets one repair attempt (the error is fed
back to the LLM), then gives up and reports the failure rather than
retrying indefinitely.

28 unit tests in `tests/test_query_validator.py` exercise this directly:
multi-statement injection, writable CTEs, blocked functions, system
schema access, column restrictions, and row-filter injection through
joins - each one was run against the validator for real, not just
asserted in the abstract.

## The agent pipeline (LangGraph)

```
classify → db_agent → rag_agent → merge → answer
   │           │  (only if intent needs it)   │
   └───────────┴──────────────────────────────┘
```

Four intents, four paths through the same graph:

- **general**: `classify → answer` (no data access at all)
- **database**: `classify → db_agent → merge → answer`
- **document**: `classify → rag_agent → merge → answer`
- **hybrid**: `classify → db_agent → rag_agent → merge → answer`

This is a deliberately simple, fully sequential graph - no parallel
fan-out/fan-in. That's a real tradeoff: a hybrid query could run the
database and document lookups concurrently, and would in a system tuned
for latency. Sequential execution is easier to reason about, easier to
test with a mocked LLM (see `tests/`, and the manual pipeline tests run
during development), and the two paths only take single-digit seconds
each - concurrency wasn't worth the added complexity for this project.

Agent nodes only **read**. They never write to the application database.
Persistence (the assistant's message, the `QueryExecution` audit row,
citations) happens once, in `services/chat_service.py`, after the graph
finishes - so a partially-run pipeline never leaves orphaned rows behind.

## Multi-tenancy

Every business table has a `tenant_id` column, and `repositories/base.py`
enforces that every lookup by ID also filters by tenant. There's no
"trusted" code path that skips this - a user's JWT carries their
`tenant_id`, and `core/tenant_context.py` derives the tenant from the
verified token, never from client-supplied input.

## Permissions

A tenant admin can read every table synced for a connection, by default.
A regular member can read nothing until a `table_permissions` row grants
them (or one of their roles) access - see
`services/database/permission_service.py` for the exact rules, including
how column grants and row filters combine when a user has more than one
applicable grant (rows: most restrictive wins; columns: most permissive
wins - documented there with the reasoning).

## What's simplified, and why

This project deliberately trades some of the enterprise version of this
system's scope for something a single developer can actually run, read,
and explain start to finish:

| Full enterprise version | This project | Why |
|---|---|---|
| Celery/Dramatiq worker queue for file processing | Synchronous processing on upload | One fewer moving service; files here are small enough that synchronous processing is still fast. Swapping in a queue later means changing `services/documents/upload_service.py` to enqueue a task instead of calling `process_file()` directly - the rest of the pipeline doesn't change. |
| Qdrant/dedicated vector DB | pgvector inside the same Postgres | One database instead of two; pgvector is genuinely fine at this scale. |
| MinIO/S3 object storage | Local disk volume | No object storage credentials to configure; a Docker volume behaves the same way from the app's point of view (`services/documents/upload_service.py` only knows a "storage path"). |
| Docling (layout-aware PDF parsing) | pypdf/python-docx/openpyxl/pandas | Lighter dependencies, faster Docker builds, no GPU. Loses layout-aware chunking for complex PDFs (tables spanning pages, multi-column layouts) - a real quality tradeoff for genuinely complex documents. |
| Prometheus/Grafana | Structured logs + the `audit_logs` table | Full observability stack is overkill for a single-instance local deployment; the audit trail already answers "what happened" for every query and login. |

None of these are "cut corners" so much as "the right call for this
project's actual scale" - and the seams are clean enough that swapping
any one of them in later is a contained change, not a rewrite.
