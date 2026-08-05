# DataChat — Text-to-SQL & Document Chat Platform

Ask questions about your live databases and your documents, in plain
English, in one chat interface. Type "How many orders came from Egypt
last month?" and it writes, security-checks, and runs the SQL for you.
Type "What does the refund policy say?" and it searches your uploaded
PDFs. Ask something that needs both, and it combines them.

This is a full-stack, multi-tenant application: FastAPI + PostgreSQL +
pgvector on the backend, a LangGraph-orchestrated agent pipeline for the
AI part, and a Next.js frontend - all wired together with Docker Compose
so it runs the same way on any machine.

**No AWS, no cloud account, no credit card.** Everything runs locally in
Docker. The only external thing you need is a free Groq API key (no
credit card required) for the language model.

If you're new to some of these tools, don't worry - the steps below spell
out literally every command. This should take about 15 minutes the first
time.

---

## What you get

- **Multi-tenant accounts** - register an organization, invite users, with
  admin vs member roles.
- **Live database connections** (PostgreSQL and MySQL) - connect a real
  database, and the app introspects its schema safely (never copies your
  data).
- **Text-to-SQL with real security controls** - every AI-generated query
  is parsed into a real SQL syntax tree and checked against a strict
  allowlist before it's ever executed: no writes, no schema changes, no
  system tables, row-level and column-level permission enforcement, and a
  hard row limit. See [ARCHITECTURE.md](./ARCHITECTURE.md) for exactly
  what this blocks and why.
- **Document chat (RAG)** - upload PDFs, Word docs, spreadsheets, or text
  files; the app chunks, embeds (locally, for free), and lets you ask
  questions with page-level citations.
- **Hybrid answers** - one question can pull from both a database and a
  document at once.
- **A full audit trail** - every query that ran, whether it passed or was
  blocked, and why, is stored and viewable per message.
- **A clean, professional chat UI** built with Next.js and Tailwind.

---

## Prerequisites (what to install)

You only need two things - not Python, not Node.js, not a database client.
Docker runs all of that for you in containers.

### 1. Docker Desktop

This is the only "app" you need to install.

- **Windows or Mac**: download and install [Docker
  Desktop](https://www.docker.com/products/docker-desktop/). Open it once
  after installing so it finishes setting up, and leave it running in the
  background - you'll see a whale icon in your system tray/menu bar when
  it's ready.
- **Linux**: install [Docker Engine](https://docs.docker.com/engine/install/)
  and the [Compose plugin](https://docs.docker.com/compose/install/linux/)
  (most distros: `sudo apt install docker.io docker-compose-v2` or
  equivalent for your package manager).

Verify it worked by opening a terminal (Command Prompt/PowerShell on
Windows, Terminal on Mac/Linux) and running:

```bash
docker --version
docker compose version
```

Both should print a version number. If either command isn't found,
Docker Desktop isn't installed correctly or isn't running yet.

### 2. A free Groq API key

Groq hosts open-source language models and gives free API access with no
credit card required. This is what powers the chat.

1. Go to **https://console.groq.com/keys**
2. Sign up (or log in) - email or Google/GitHub login works.
3. Click **"Create API Key"**, give it any name, and copy the key it
   shows you (it starts with `gsk_...`). You won't be able to see it
   again after you close the dialog, so copy it somewhere safe now.

That's genuinely everything you need to install or sign up for.

---

## Step-by-step setup

### 1. Get the project onto your machine

Unzip the project folder you downloaded, or if you have git:

```bash
git clone <your-repo-url> textsql-platform
cd textsql-platform
```

Either way, open a terminal **inside the project's root folder** (the
one containing `docker-compose.yml`) for every command below.

### 2. Create your `.env` file

This file holds your Groq key and two generated secrets. Copy the
template:

```bash
cp .env.example .env
```

Now open `.env` in any text editor and fill in three values:

**``** - paste the key you copied above.

**`JWT_SECRET_KEY`** - any long random string works. Generate one:

```bash
# If you have Python installed locally:
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# If you don't have Python installed, Docker can run it for you:
docker run --rm python:3.12-slim python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the output into `.env` after `JWT_SECRET_KEY=`.

**`ENCRYPTION_KEY`** - this one has to be generated with this *exact*
command (it encrypts database passwords at rest, and needs a specific
format - a random string won't work here):

```bash
# If you have Python installed locally:
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# If you don't have Python installed:
docker run --rm python:3.12-slim bash -c "pip install cryptography -q && python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
```

Copy the output into `.env` after `ENCRYPTION_KEY=`.

Your `.env` should now look like:

```
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=llama-3.3-70b-versatile
JWT_SECRET_KEY=some-long-random-string-here
ENCRYPTION_KEY=a-generated-fernet-key-here=
```

### 3. Start everything

```bash
docker compose up --build
```

The first run will take a few minutes - it's downloading Postgres,
MySQL, and building the backend and frontend images (including
pre-caching the free local embedding model, so later uploads are fast).
Subsequent runs take a few seconds.

Leave this terminal window open; it's showing you the live logs of all
four services. You'll know it's ready when you see the backend log
settle down with lines like `Application startup complete` and the
frontend log show `Ready in ...`.

> Open a **second terminal** for the remaining commands - keep this one
> running.

### 4. (Recommended) Load demo data

This creates a ready-to-use account and two pre-configured connections
(one Postgres, one MySQL) pointing at realistic sample business data, so
you have something to try immediately:

```bash
docker compose exec backend python scripts/seed_demo_data.py
```

This prints a demo login at the end:

```
email:    demo@example.com
password: demo12345
```

Safe to re-run any time - it won't create duplicates.

### 5. Open the app

Go to **http://localhost:3000** in your browser. Log in with the demo
account above, or click "Create one" to register your own organization.

The backend's interactive API docs are at **http://localhost:8000/docs**
if you want to explore the API directly.

---

## Taking it for a spin

1. **Chat tab** → "New conversation" → both demo connections should
   already be checked → "Start chatting."
2. Try: *"How many customers are from Egypt?"* or *"What are the top 3
   most expensive products?"* - watch the status line show it
   classifying, querying, and answering, then expand the query trace
   under the answer to see the exact SQL that ran and its validation
   status.
3. Go to **Knowledge bases** → create one → upload a PDF or text file →
   go back to Chat, select it as a source in a conversation, and ask a
   question about its contents.
4. Try a question that needs both at once, e.g. *"Do our top customers
   match who the contract says gets priority support?"* (if you've
   uploaded a relevant document).

---

## Connecting your own database

The demo connections point at sample containers seeded by this project.
To connect a database of your own:

- **A database also running in Docker on your machine**: use its
  container name as the host (same pattern as `postgres`/`mysql` above).
- **A database running directly on your host machine** (not in Docker):
  use `host.docker.internal` as the host, *not* `localhost` - the backend
  runs inside a container, so `localhost` from its point of view is the
  container itself, not your machine. This project's `docker-compose.yml`
  is already configured to make `host.docker.internal` work on Linux too,
  not just Mac/Windows.
- **A remote/cloud database**: use its real hostname, and make sure its
  firewall allows inbound connections from your machine.

Add it from the **Connections** page, click **Test**, then **Sync
schema** once it succeeds.

---

## How it works

Short version: your question goes through a small pipeline (classify
intent → query the database and/or search documents → merge → generate
an answer), and every generated SQL query is parsed into a real syntax
tree and checked against a strict allowlist before it's ever executed -
no writes, no schema changes, tenant- and permission-scoped, with a hard
row limit.

For the full explanation - including three real bugs this validator
caught during development (a disguised `DELETE` hidden in a writable CTE,
an `EXPLAIN ANALYZE` side-channel, and a blocked-function detection
mismatch) and why several things are deliberately simplified from a
"full enterprise" version - see **[ARCHITECTURE.md](./ARCHITECTURE.md)**.

---

## Project structure

```
textsql-platform/
├── docker-compose.yml       # The entire stack, one command to run it
├── .env.example             # Copy to .env and fill in your keys
├── schema.sql                # Reference copy of the database schema
├── ARCHITECTURE.md           # Design decisions, in depth
├── backend/
│   ├── app/                  # FastAPI app, config, startup
│   ├── api/routes/           # HTTP endpoints (thin - no business logic)
│   ├── services/             # Business logic
│   │   ├── database/         # Connection mgmt, schema sync, SQL validator/executor
│   │   ├── documents/        # Parsing, chunking, embeddings, retrieval
│   │   └── llm/               # LLM client + prompts
│   ├── agents/                # LangGraph pipeline (classify/db/rag/merge/answer)
│   ├── models/                 # SQLAlchemy models
│   ├── repositories/           # Tenant-scoped data access
│   ├── migrations/             # Alembic database migrations
│   ├── tests/                  # Pytest suite (28+ tests on the SQL validator alone)
│   └── scripts/seed_demo_data.py
├── frontend/
│   ├── app/                    # Next.js pages (App Router)
│   ├── components/             # UI components
│   └── lib/                    # API client, auth, types
└── infra/
    ├── postgres/init/          # Demo Postgres data (auto-loaded on first run)
    └── mysql/init/             # Demo MySQL data (auto-loaded on first run)
```

---

## Running the tests

```bash
docker compose exec backend python -m pytest -v
```

This includes 28 tests specifically on the SQL security validator -
injection attempts, writable CTEs, permission enforcement, row-filter
injection through joins - plus tests on encryption and permission
resolution.

---

## Troubleshooting

**"Port is already allocated" when running `docker compose up`**
Something on your machine is already using port 3000, 8000, 5432, or
3306. Stop that other program, or edit the left-hand side of the `ports:`
lines in `docker-compose.yml` (e.g. change `"3000:3000"` to
`"3001:3000"` and visit `http://localhost:3001` instead).

**Chat says it can't reach the language model provider**
Your `GROQ_API_KEY` is missing or invalid. Double-check `.env`, then
restart just the backend: `docker compose restart backend`.

**"ENCRYPTION_KEY ... is not a valid Fernet key" in the backend logs**
You need to generate it with the exact command in step 2 above - a
random string won't work, it needs to be a genuine Fernet key.

**File upload gets stuck on "Processing"**
The first file you upload after a fresh build can take a little longer
the very first time as the embedding model finishes initializing. If it's
still stuck after a minute, check `docker compose logs backend` for the
actual error.

**Docker build fails partway through with a network error**
Building requires internet access to download Python/Node packages, the
local embedding model, and web fonts. If you're behind a restrictive
corporate proxy/firewall, some of these may be blocked - try from a
regular home/office network.

**I want to start completely fresh**
This deletes all data (the app database, uploaded files, demo data) and
rebuilds from scratch:

```bash
docker compose down -v
docker compose up --build
```

---

## License

MIT - see [LICENSE](./LICENSE). Built as a learning/portfolio project;
see ARCHITECTURE.md for the security model before pointing it at a real
production database.
