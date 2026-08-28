Lenny Growth Assistant

A full-stack, RAG-grounded AI assistant for product and growth questions, powered by Lenny's Podcast transcripts.

The Lenny Growth Assistant turns long-form product and growth conversations into an interactive research and writing workspace. Users can ask questions, continue the conversation with session memory, receive answers grounded in transcript evidence, generate Ship 30/30-style essays, and turn conversations into Markdown or HTML artifacts inside the application.

Built as a Forward Deployed Engineer take-home project, with an emphasis on product judgment, grounding, operational readiness, graceful failure handling, and evaluator-friendly deployment.

✨ What it does

💬 Grounded product & growth Q&A

Ask questions such as:

"What do great PMs do differently?"

"How should a startup think about product-market fit?"

"What are effective growth loops?"

"How should a PM prioritize customer feedback?"

The assistant retrieves relevant transcript chunks using vector similarity and instructs the model to answer only from the retrieved evidence.

Every grounded response can identify the episode/source used. When the available corpus does not provide enough evidence, the system explicitly reports insufficient context rather than confidently inventing an answer.

🧠 Conversational sessions

Each conversation has its own session ID and persisted message history.

This allows follow-ups such as:

User: What makes a good product manager?
User: How does that change at an early-stage startup?
User: Turn that into an essay.

Conversation state is persisted in PostgreSQL rather than relying only on browser state.

✍️ Ship 30/30 writing skill

A dedicated Ship 30/30 skill converts grounded product/growth knowledge into a structured essay.

The skill is designed around:

A strong opening hook

Clear narrative progression

Skimmable headings

Selective emphasis

Practical takeaways

Claims grounded in the transcript knowledge base

Approximately 1,250 words

The writing capability is implemented as a distinct skill/module rather than treating essay generation as an unrelated one-off prompt.

📄 Artifact generation

The assistant can turn conversation context into:

Markdown documents

HTML/CSS artifacts

Generated artifacts appear in an in-app Artifact Viewer beside the conversation rather than forcing the user to copy raw code into another application.

HTML is treated as untrusted generated content and rendered in an isolated/sandboxed context.

🔀 Local / cloud model toggle

The application supports two provider paths:

Provider

Purpose

Ollama

Required local/demo path; no cloud API cost

Anthropic

Cloud-quality provider path

Switch providers through configuration without changing application code.

The active provider/model is exposed through the application configuration endpoint and shown in the frontend UI.

🏗️ Architecture

                         ┌─────────────────────────┐
                         │       Browser UI         │
                         │ React via CDN + HTML     │
                         │ Chat + Artifact Viewer   │
                         └────────────┬────────────┘
                                      │ HTTP
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI API        │
                         │                         │
                         │ /sessions              │
                         │ /chat                  │
                         │ /artifacts             │
                         │ /config                │
                         │ /health                │
                         └──────┬──────────┬───────┘
                                │          │
                 ┌──────────────┘          └──────────────┐
                 ▼                                        ▼
       ┌──────────────────┐                    ┌──────────────────┐
       │   Agent / Skills │                    │   PostgreSQL     │
       │                  │                    │   + pgvector     │
       │ Default Q&A      │                    │                  │
       │ Ship 30/30       │                    │ Sessions         │
       │ Artifact skill   │                    │ Messages         │
       └────────┬─────────┘                    │ Artifacts        │
                │                              │ Transcript chunks│
                ▼                              └────────┬─────────┘
       ┌──────────────────┐                             │
       │ Retrieval / RAG  │◄────────────────────────────┘
       │                  │
       │ Query embedding  │
       │ Cosine search    │
       │ Top-k retrieval  │
       │ Grounding check  │
       └────────┬─────────┘
                │
                ▼
       ┌───────────────────────────────┐
       │        LLM Provider            │
       │                               │
       │ Ollama          Anthropic      │
       │ local           cloud          │
       └───────────────────────────────┘

Core stack

Layer

Technology

Frontend

HTML + React via CDN

Backend

FastAPI / Python 3.11

Database

PostgreSQL 16

Vector search

pgvector

Embeddings

Ollama nomic-embed-text

Local LLM

Ollama llama3.2:1b by default

Cloud LLM

Anthropic

Containerization

Docker Compose

Retrieval

Cosine similarity over transcript chunks

🔎 RAG pipeline

The knowledge pipeline is deliberately simple and traceable:

Lenny Podcast transcripts
          │
          ▼
       Ingestion
          │
          ▼
    Word-based chunks
    size = 800
    overlap = 100
          │
          ▼
 Ollama nomic-embed-text
      768 dimensions
          │
          ▼
 PostgreSQL + pgvector
          │
          ▼
      User question
          │
          ▼
      Query embedding
          │
          ▼
   Cosine similarity
       top_k = 5
          │
          ▼
 Similarity threshold
       = 0.30
          │
     ┌────┴────┐
     │         │
 Sufficient  Insufficient
     │         │
     ▼         ▼
 Grounded    Explicitly
 answer      acknowledge

The retrieval layer returns both:

Relevant transcript chunks

A sufficient grounding signal

This allows the application to distinguish "I found supporting evidence" from "I should not answer this from the available corpus."

📚 Knowledge-base scope

For this take-home, 20 representative episodes from the available Lenny transcript corpus were selected as the v1 knowledge scope.

The ingestion pipeline is not hard-coded to 20 episodes. It can scale to the complete corpus by pointing ingestion at the full transcript directory.

This was an intentional time-scoping decision:

Prefer a smaller, demonstrably grounded corpus over pretending the assistant knows content that was never indexed.

Questions outside the indexed material should fail safely through the insufficient-context path rather than encouraging hallucination.

🚀 Quick start

Prerequisites

Docker Desktop

WSL2 backend on Windows

Approximately 4 GB RAM available to Docker/WSL2 for a comfortable local run

Modern browser

Git

Optional: Anthropic API key for the cloud provider

1. Clone the repository

git clone https://github.com/nazimmuhammed/lenny-growth-assistant.git
cd lenny-growth-assistant

2. Configure environment

Copy the example environment file:

Windows PowerShell

Copy-Item .env.example .env

macOS / Linux

cp .env.example .env

For the default local setup, no Anthropic key is required.

3. Start the backend stack

docker compose up -d db ollama backend

Check the containers:

docker compose ps

4. Pull the local models

First run only:

docker exec -it lenny-growth-assistant-ollama-1 ollama pull llama3.2:1b
docker exec -it lenny-growth-assistant-ollama-1 ollama pull nomic-embed-text

5. Ingest the transcript corpus

Run:

docker exec -it lenny-growth-assistant-backend-1 python -m app.rag.ingest

Verify the indexed chunks:

docker exec -it lenny-growth-assistant-db-1 \
  psql -U lenny -d lenny_assistant \
  -c "SELECT COUNT(*) FROM chunks;"

6. Open the frontend

No frontend build is required.

Open:

frontend/src/index.html

On Windows:

start frontend/src/index.html

The frontend connects directly to:

http://localhost:8000

⚙️ Configuration

Configuration is controlled through .env.

Example:

LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:1b

ANTHROPIC_API_KEY=

CHUNK_SIZE=800
CHUNK_OVERLAP=100

Main variables

Variable

Default

Required

Description

LLM_PROVIDER

ollama

No

ollama or anthropic

OLLAMA_MODEL

llama3.2:1b

No

Local chat model

ANTHROPIC_API_KEY

—

Only for Anthropic

Cloud provider credential

CHUNK_SIZE

800

No

Transcript chunk size

CHUNK_OVERLAP

100

No

Chunk overlap

Never commit .env. Only .env.example belongs in the repository.

🔀 Switching models

Change:

LLM_PROVIDER=ollama

to:

LLM_PROVIDER=anthropic

and configure:

ANTHROPIC_API_KEY=your_key_here

Then recreate the backend:

docker compose up -d --force-recreate backend

No application-code change is required.

The selected provider/model is exposed to the frontend so the evaluator can see which path is active.

🧪 Testing

Run the automated test suite inside the backend container:

docker exec -it lenny-growth-assistant-backend-1 pytest

The tests cover critical behavior including:

Session creation

Message persistence round-trip

Retrieval relevance

Ship 30/30 vs default routing

A manual UI test plan is maintained under:

docs/manual_test_plan.md

🛡️ Resilience & failure handling

The system is designed to fail explicitly rather than silently.

Missing Anthropic API key

If:

LLM_PROVIDER=anthropic

but the API key is missing, the backend returns a structured error instead of exposing a raw exception.

Ollama unavailable / timeout

Ollama connection and timeout failures are caught and surfaced as a structured:

502 Bad Gateway

response.

Insufficient retrieval

If no retrieved chunk meets the grounding threshold, the retrieval layer marks the result as insufficient.

The assistant is instructed to acknowledge the limitation rather than fabricate an answer.

Database failure

Database connection errors are allowed to surface through structured API error handling rather than producing an unexplained application crash.

⚠️ Known local-model trade-off

The originally intended local model was llama3.1:8b.

During development, it repeatedly timed out under the available CPU/RAM resources inside Docker/WSL2. The issue was observed during both generation and, at times, embedding operations.

A smaller model, llama3.2:1b, was tested successfully and became the default local model.

Trade-off

llama3.1:8b
    ↑
better depth / quality
    │
    │
    ↓
llama3.2:1b
    ↑
better local responsiveness / lower resource requirements

The application therefore prioritizes reliable local execution for the evaluator over pretending that constrained hardware can comfortably run a larger model.

On a machine with sufficient resources, the model can be changed through:

OLLAMA_MODEL=llama3.1:8b

No code change is necessary.

🔐 Artifact security

Generated HTML is treated as untrusted content.

The Artifact Viewer isolates generated HTML rather than allowing arbitrary generated scripts to execute in the parent application context.

This follows the principle:

Generated content should be rendered as an artifact, not trusted as application code.

For a production deployment, additional hardening would include a stricter Content Security Policy, HTML sanitization, origin isolation, and tighter iframe permissions.

🗂️ Project structure

lenny-growth-assistant/
│
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   └── skills/
│   │   │       └── ship30.py
│   │   │
│   │   ├── api/
│   │   │   ├── artifacts.py
│   │   │   ├── chat.py
│   │   │   └── sessions.py
│   │   │
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   │
│   │   ├── llm/
│   │   │   ├── anthropic_client.py
│   │   │   ├── ollama_client.py
│   │   │   └── provider.py
│   │   │
│   │   ├── rag/
│   │   │   ├── embed.py
│   │   │   ├── ingest.py
│   │   │   └── retriever.py
│   │   │
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
│
├── frontend/
│   └── src/
│       └── index.html
│
├── docs/
│   ├── architecture.md
│   └── manual_test_plan.md
│
├── .env.example
├── .gitignore
└── docker-compose.yml

🎯 Product decisions

This project intentionally favors trust and usability over unnecessary complexity.

Decision 1 — Grounding over generic intelligence

The assistant is not positioned as a general-purpose PM chatbot.

Its value comes from answering:

"What does the source material actually say?"

This makes insufficient-context detection a product feature, not merely an engineering detail.

Decision 2 — Small corpus, complete pipeline

Rather than spending the entire implementation window ingesting all available episodes, the v1 scope uses 20 representative episodes while preserving a general ingestion pipeline.

Decision 3 — Local-first demo

Ollama is the default provider because the assessment requires a local model that the evaluator can actually run.

Cloud Anthropic support remains available for higher-quality generation.

Decision 4 — Artifacts inside the product

Generated writing becomes useful when it can immediately be viewed and reused.

The Artifact Viewer therefore lives beside the conversation rather than redirecting users to another tool.

Decision 5 — Explicit failure states

A slower or smaller model is acceptable.

A fabricated answer presented as source-grounded is not.

📈 Success metrics

These are pre-launch target hypotheses, not measured production metrics.

Metric

Target

Grounding rate

≥ 85% of answered questions cite a transcript source

Cloud time-to-answer

< 5 seconds median

Local time-to-answer

Establish a documented machine-specific viability threshold

Artifact usage

≥ 30% of sessions with 2+ questions generate an artifact

Session return

User returns for another session within 7 days

These metrics would be validated after real internal usage rather than presented as existing results.

🧭 Scope

Included

RAG-grounded conversational Q&A

Session persistence

PostgreSQL + pgvector

Local Ollama provider

Anthropic cloud provider

Provider toggle

Ship 30/30 writing skill

Markdown/HTML artifact generation

In-app Artifact Viewer

Docker Compose deployment

Structured failure handling

Automated tests

Operational documentation

Intentionally excluded

Full 320-episode corpus for the take-home scope

Authentication and multi-tenancy

Production database migrations

Production-grade CORS/security hardening

Usage-based cloud cost controls

These are documented trade-offs rather than accidental omissions.

🔧 Troubleshooting

Problem

Likely cause

Fix

/chat returns 502

Ollama is slow/unavailable

Check Ollama logs and confirm the model is pulled

Frontend stays on Connecting...

Backend unreachable

Check docker compose ps and browser console

Docker Compose fails immediately

Invalid/unneeded frontend service configuration

Start db, ollama, and backend explicitly

Ingestion produces 0 chunks

Transcript data unavailable or ingestion failed

Verify the data mount and rerun ingestion

Anthropic path fails

Missing API key

Set ANTHROPIC_API_KEY and recreate backend

Local generation is very slow

Hardware constraints

Use llama3.2:1b or increase Docker/WSL2 resources

Useful commands:

docker compose ps
docker compose logs backend
docker compose logs ollama
docker compose logs db

📋 Forward-deployment handoff

A fresh evaluator should be able to:

Clone the repository

Create .env from .env.example

Start PostgreSQL, Ollama, and FastAPI with Docker Compose

Pull the required local models

Ingest the transcript corpus

Open the frontend

Ask a grounded question

Inspect the source citation

Continue the conversation

Generate a Ship 30/30 essay

Generate a Markdown/HTML artifact

Run the automated tests

The system is intentionally structured so that another engineer can replace the LLM provider, expand the corpus, modify skills, or extend the API without rewriting the entire application.

🎥 Demo

The submission demo should show:

The product problem

The chat experience

A grounded answer with source citation

A follow-up question using session context

Ship 30/30 essay generation

Artifact generation and in-app rendering

Ollama running locally

The provider/model indicator

One important technical trade-off — the local 8B → 1B model decision

📄 Assessment deliverables

The repository is intended to contain:

README.md — setup, architecture, operation and troubleshooting

PRD.md — discovery framing, assumptions, scope, success metrics and trade-offs

design.md — UI/UX rationale and interaction design

architecture.md — system architecture, data model, APIs, retrieval and security

docs/manual_test_plan.md — manual UI verification

agent-transcripts/ — coding-agent logs, including failed attempts and corrections

Automated tests under the backend test suite

Demo video covering the product and key technical decisions

👤 Author

Nazim Muhammed

Built for the Forward Deployed Engineer — Lenny Growth Assistant take-home assessment.

License

This repository was created as an evaluation project. Review the applicable source/data terms before redistributing transcript content.
