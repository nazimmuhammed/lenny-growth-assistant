# architecture.md --- Lenny Growth Assistant

## System overview

``` text
                    HTTP/JSON
┌──────────────────┐              ┌──────────────────┐
│                  │              │                  │
│    Frontend      │ ───────────► │     FastAPI      │
│   (static        │              │     backend      │
│    index.html)   │ ◄─────────── │                  │
│                  │              │                  │
└──────────────────┘              └────────┬─────────┘
                                           │
                         ┌─────────────────┼─────────────────┐
                         ▼                 ▼                 ▼
                   ┌────────────┐   ┌──────────────┐   ┌────────────┐
                   │ PostgreSQL │   │ Anthropic API│   │   Ollama   │
                   │  (local)   │   │  + pgvector  │   │            │
                   │            │   │  (cloud,     │   │ chat +     │
                   │ embeddings │   │   opt-in)     │   │ embeddings │
                   └────────────┘   │ sessions/    │   └────────────┘
                                    │ messages/     │
                                    │ artifacts/    │
                                    │ chunks        │
                                    └──────────────┘
```

The frontend is a static file, not containerized --- it calls the
backend directly over `http://localhost:8000` with CORS fully open for
local development.

## Database schema

-   **sessions**: `id` (UUID, PK), `created_at`
-   **messages**: `id` (PK), `session_id` (FK → sessions), `role`
    (`user`/`assistant`), `content`, `sources` (JSON --- episode
    titles + URLs used for grounding, empty for user messages),
    `sufficient_context` (bool, nullable), `model_used`, `created_at`
-   **artifacts**: `id` (PK), `session_id` (FK → sessions), `type`
    (`markdown`/`html`), `content`, `created_at`
-   **chunks**: `id` (PK), `episode_title`, `source_url`, `chunk_text`,
    `embedding` (`vector(768)`, pgvector extension)

Tables are created via SQLAlchemy `create_all()` on backend startup
rather than Alembic migrations --- a deliberate time trade-off for a
short-lived evaluation deployment. A production rollout would require
migrations for safe schema evolution.

## API endpoints

  ---------------------------------------------------------------------------
  Method                  Path                        Purpose
  ----------------------- --------------------------- -----------------------
  `GET`                   `/health`                   Liveness check

  `GET`                   `/config`                   Returns active
                                                      `LLM_PROVIDER` and
                                                      model, consumed by the
                                                      frontend badge

  `POST`                  `/sessions/`                Creates a new session,
                                                      returns `session_id`

  `GET`                   `/sessions/{id}/messages`   Returns persisted
                                                      message history for a
                                                      session

  `POST`                  `/chat`                     Core grounded Q&A
                                                      endpoint (see flow
                                                      below)

  `POST`                  `/artifacts`                Generates a
                                                      Markdown/HTML artifact
                                                      from conversation
                                                      context
  ---------------------------------------------------------------------------

All endpoints return structured JSON errors (not raw tracebacks) on
failure, with an appropriate HTTP status (`502` for upstream LLM/Ollama
failures, `500` for unexpected internal errors, `4xx` for validation
failures).

## Ingestion / retrieval flow

1.  **Ingestion** (`app/rag/ingest.py`, run manually/on-demand, not
    automatic on startup):
    -   Reads `.md` files from `data/transcripts/selected/`
    -   Strips YAML frontmatter
    -   Chunks by word count (`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`,
        both configurable via `.env`)
    -   Embeds each chunk via Ollama's `/api/embeddings`
        (`nomic-embed-text`, 768-dim)
    -   Inserts into `chunks` with `episode_title` and a `source_url`
        pointing back to the canonical transcript on GitHub, preserving
        traceability to the original source
2.  **Retrieval** (`app/rag/retriever.py`):
    -   Embeds the incoming query the same way
    -   Runs a cosine similarity search via pgvector's `<=>` operator,
        `top_k=5`
    -   Applies a `similarity_threshold=0.3`; if no chunk clears it,
        returns `sufficient=False` alongside whatever was found, so the
        calling code can instruct the model to acknowledge insufficient
        grounding rather than answer freely

## Agent routing

Routing is intentionally simple and explicit rather than a
general-purpose agent loop, since the brief calls for "clear skill
boundaries":

-   **Default path:** retrieval → grounded system prompt → LLM call →
    persist → return with sources
-   **Ship 30/30 path:** triggered by keyword match (e.g. message starts
    with `ship30:` or contains "turn this into an essay") → routes to
    `app/agent/skills/ship30.py`, which uses a dedicated system prompt
    encoding the Ship 30/30 format (hook, \~1,250 words,
    headings/bullets/bold, specific takeaway) applied to the same
    retrieved, grounded chunks
-   **Artifact path:** separate `/artifacts` endpoint, not part of
    `/chat` routing --- takes explicit `type` (`markdown`/`html`) and
    `instructions`, generates via the active LLM provider, persists to
    the `artifacts` table

This keyword-based router is a deliberate simplification, documented as
a scope choice: a more robust version would use intent classification
rather than string matching, which would be the first thing to revisit
with more time.

## Model toggle

`app/llm/provider.py` exposes `get_llm_client()`, which reads
`settings.LLM_PROVIDER` (from `.env` via `pydantic-settings`) and
returns either `OllamaClient` or `AnthropicClient`.

Both implement the same `generate(messages, system, max_tokens)`
interface, so calling code in `chat.py` and the Ship30/artifact modules
is provider-agnostic.

Switching providers requires only an `.env` change and a backend
container recreate --- no code change, satisfying the brief's explicit
requirement.

### Documented limitation

The local path (`OllamaClient`) is the mandated demo path but is
sensitive to available machine resources. During development,
`llama3.1:8b` reliably exceeded the client's timeout
(`httpx.ReadTimeout`) on both chat generation and, at times, the
embedding call, under Docker/WSL2 resource constraints.

`OLLAMA_MODEL` was changed to `llama3.2:1b`, which responds reliably on
the same hardware. This is surfaced in `README.md` as a first-class
trade-off, not hidden.

## Security: artifact rendering

Generated HTML is treated as fully untrusted input, since it originates
from an LLM completion that could --- intentionally or not --- include
executable script.

### Strategy implemented

HTML artifacts are rendered inside a sandboxed `<iframe>` with **no**
**`sandbox`** **flags granted** (i.e. `sandbox=""`), which:

-   Blocks script execution inside the iframe entirely
-   Blocks form submission, top-level navigation, and
    pointer-lock/plugin access
-   Isolates the iframe's DOM from the parent page's DOM and
    cookies/storage

### What this permits

Static HTML/CSS rendering --- layout, styling, tables, images --- which
covers the artifact use cases described in the brief (formatted
documents, not interactive applications).

### What this blocks, and why

Any `<script>` in generated HTML will not execute.

This was a deliberate choice over `sandbox="allow-scripts"`: since the
brief explicitly calls out HTML as untrusted, granting script execution
would require a much heavier mitigation (e.g. full `postMessage`-based
isolation, CSP injection, DOMPurify script-stripping with manual
verification of every allowed tag/attribute) that wasn't justified by
the actual use case of "render a formatted document."

Markdown artifacts are rendered via `marked.js` into the parent page
directly (not iframed), since Markdown does not carry executable script
in the same way.

If this were hardened further for production, HTML output from `marked`
would also be passed through a sanitizer (e.g. DOMPurify) as
defense-in-depth. This is flagged as a next-iteration hardening step,
not currently implemented, since Markdown syntax itself doesn't support
raw script execution by default.

## Deployment topology

-   `docker-compose.yml` defines `db` (`pgvector/pgvector:pg16`),
    `ollama` (`ollama/ollama`), and `backend` (custom Dockerfile,
    `uvicorn`)
-   A `frontend` service definition exists in the compose file but is
    currently non-functional (no corresponding Dockerfile) --- the
    frontend is intentionally run as a static file opened directly in
    the browser instead, to avoid npm/build tooling risk under the
    deadline. Evaluators should run
    `docker compose up -d db ollama backend` (explicitly naming
    services) rather than a bare `up -d`, or remove/fix the `frontend`
    service block before a production handoff.
-   **Volumes:**
    -   `./backend:/app` (live code reload via `uvicorn --reload`)
    -   `./data:/app/data` (transcript files --- must be explicitly
        mounted, was a fix made during development after transcripts
        weren't initially visible inside the container)
-   **CORS:** `allow_origins=["*"]` --- acceptable for local demo,
    flagged in `README.md` as requiring restriction before any real
    deployment

## Known gaps for a production handoff

-   No database migrations (Alembic) --- `create_all()` only
-   No authentication/multi-tenancy
-   No rate limiting or cost caps on the Anthropic path
-   No encryption-at-rest for session/message content
-   CORS is fully open
-   `frontend` Docker service is a stub, not a working container