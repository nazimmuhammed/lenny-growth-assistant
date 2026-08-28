# PRD — Lenny Growth Assistant

## 1. Product Overview

**Lenny Growth Assistant** is a full-stack, RAG-grounded conversational assistant built around Lenny Rachitsky's Podcast transcripts.

The product is designed to help product managers and growth practitioners quickly find credible, actionable insights from long-form operator conversations without manually listening to hours of podcast episodes or searching large transcript collections.

The assistant combines:

- Retrieval-Augmented Generation (RAG)
- Semantic vector search
- Source citations
- Conversational session persistence
- Specialized Ship 30/30 essay generation
- Markdown/HTML artifact generation
- Local and cloud LLM providers
- A lightweight in-app Artifact Viewer

The application was built for the **Forward Deployed Engineer take-home assessment**.

---

# 2. User and Problem

## Primary User

The primary user is a:

- Product Manager
- Growth Practitioner
- Product/Growth Individual Contributor
- Early-stage Product/Growth Manager

The user wants fast, credible answers to practical PM and growth questions grounded in real operator conversations.

## Job to Be Done

> "When I have a specific PM/growth question, I want a grounded answer sourced from real operator conversations, so I can act on it or share it with my team without spending 30+ minutes finding the right episode and timestamp."

## Core Pain

Long-form podcasts contain valuable product and growth knowledge, but finding one specific insight can require:

1. Identifying the right episode.
2. Searching transcripts.
3. Reading large amounts of surrounding context.
4. Verifying that the insight actually supports the question.
5. Turning the insight into something actionable.

This creates a significant time cost and introduces the risk of relying on generic, ungrounded LLM answers instead of lived operator experience.

## Product Solution

Lenny Growth Assistant addresses this by combining semantic retrieval with an LLM.

```text
PM / Growth Question
        │
        ▼
Semantic Retrieval
        │
        ▼
Relevant Podcast Transcript Chunks
        │
        ▼
Grounded LLM Response
        │
        ├── Source Citations
        │
        └── Insufficient Context Detection
```

---

# 3. Product Goals

## Primary Goals

### Goal 1 — Fast grounded answers

Allow users to ask PM and growth questions in natural language and receive answers grounded in transcript evidence.

### Goal 2 — Reduce research time

Replace manual transcript/episode searching with a conversational retrieval interface.

### Goal 3 — Preserve traceability

Show the source episode(s) supporting the answer so users can distinguish grounded insights from generic model knowledge.

### Goal 4 — Turn insights into action

Allow users to transform answers into:

- Ship 30/30-style essays
- Markdown documents
- HTML artifacts

### Goal 5 — Support flexible inference

Provide both:

- Local Ollama inference
- Cloud Anthropic inference

without requiring application-code changes when switching providers.

### Goal 6 — Fail safely

When sufficient transcript evidence is unavailable, the assistant should acknowledge the limitation rather than fabricate a confident answer.

---

# 4. Success Metrics

These metrics are **estimated pre-launch targets**, not measured production results.

There is currently no production usage data, so these should be treated as hypotheses to validate after launch.

## Grounding Rate

**Target:** ≥ 85% of answered questions cite at least one transcript source.

This measures whether users' questions can generally be answered from the available corpus rather than frequently falling back to insufficient context.

---

## Time to Answer

### Cloud Provider

**Target:** Median response time < 5 seconds.

### Local Provider

**Target:** < 15 seconds on a supported development machine.

The local threshold is intended as a viability benchmark because latency depends heavily on available CPU/RAM and the selected model.

---

## Artifact Usage

**Target:** ≥ 30% of sessions containing two or more questions generate at least one artifact.

Artifacts include:

- Ship 30/30 essays
- Markdown documents
- HTML documents

This is intended as a proxy for whether users find the assistant useful beyond simple Q&A.

---

## Session Return Rate

**Target:** A user who starts one session returns for another session within seven days.

This is a proxy for perceived usefulness and repeat value.

---

# 5. Product Assumptions

The original client brief left several implementation decisions open.

The following assumptions were made and should be validated with the client.

### Internal Tool

The assistant is treated as an internal product/growth tool rather than a public SaaS product.

Therefore:

- Authentication is out of scope.
- Multi-tenancy is out of scope.
- A single-tenant evaluation deployment is acceptable.

### Citation Granularity

"Grounded" is interpreted as providing citation-by-episode-title traceability.

Timestamp-level citations are not required because the transcript formatting does not guarantee a consistent timestamp representation.

### Local Model Quality

Local inference is allowed to have lower quality than cloud inference.

The primary purpose of the local provider is:

- Deployability
- Cost control
- Local development
- Demonstrability

It is not expected to perfectly match cloud-grade model quality.

### Corpus Scope

A subset of the full transcript corpus is acceptable for the v1 assessment implementation, provided the ingestion pipeline can scale to the full dataset without requiring application-code changes.

### CORS

Open CORS (`*`) is acceptable for the local/demo deployment.

Production deployment would require origin restrictions and additional security hardening.

---

# 6. Scope

## Included

### RAG-Grounded Q&A

- Natural-language PM/growth questions
- Semantic transcript retrieval
- Top-k vector search
- Similarity threshold
- Insufficient-context detection
- Grounded responses
- Source citations

### Conversation Persistence

- Session creation
- Session reuse
- Message persistence
- Follow-up conversation context
- PostgreSQL-backed state

### LLM Provider Toggle

- Ollama local provider
- Anthropic cloud provider
- `.env` configuration
- Runtime provider/model visibility in UI

### Ship 30/30 Skill

- Distinct essay-generation behavior
- Keyword/request routing
- Grounded source context
- Structured long-form output

### Artifact Generation

- Markdown generation
- HTML generation
- Persisted artifacts
- Split-pane Artifact Viewer
- Sandboxed HTML rendering

### Deployment

- Docker Compose
- PostgreSQL + pgvector
- Ollama
- FastAPI backend
- Static frontend

### Resilience

Structured handling for:

- Missing API keys
- Ollama timeouts
- Ollama connection failures
- Insufficient retrieval
- Database failures

---

# 7. Explicitly Excluded

## Full 320-Episode Ingestion

The complete corpus was not ingested for the assessment.

Instead, 20 representative episodes were used.

This was a time-scoping decision.

The ingestion pipeline supports scaling to the complete corpus through configuration rather than requiring application-code changes.

---

## Authentication and User Accounts

Authentication, authorization, and multi-tenancy were excluded because the application is intended as an internal single-tenant evaluation tool.

For a production rollout, authentication would be required.

---

## Database Migrations

Alembic migrations were not implemented.

The application uses:

```text
create_all()
```

on startup.

This was a deliberate time trade-off for the assessment.

A production system would use a migration framework and versioned schema changes.

---

## Production Security Hardening

The assessment implementation does not attempt to provide complete production security hardening.

Known gaps include:

- Open CORS
- No authentication
- No encryption-at-rest configuration
- No production-grade secret management
- No cloud usage budget enforcement

These are documented rather than hidden.

---

# 8. Key User Flows

## Flow 1 — Ask a Question

```text
User asks PM/Growth question
        │
        ▼
Create or reuse session
        │
        ▼
Generate query embedding
        │
        ▼
Search transcript vectors
        │
        ▼
Evaluate retrieval sufficiency
        │
        ├───────────────┐
        │               │
   Sufficient       Insufficient
        │               │
        ▼               ▼
Grounded answer    Explicitly state
        │            insufficient
        ▼
Source citations
        │
        ▼
Persist message
```

### Expected Outcome

The user receives either:

1. A grounded answer with visible source citations, or
2. An explicit insufficient-context response.

---

# 9. Follow-Up Question Flow

The assistant supports conversational context.

```text
Question 1
   │
   ▼
Answer 1
   │
   ▼
Question 2
   │
   ▼
Retrieve relevant transcript evidence
   +
Previous session messages
   │
   ▼
Context-aware answer
```

Previous messages are stored in PostgreSQL and included when constructing follow-up context.

This allows users to ask questions such as:

```text
User:
How should I validate a new product idea?

Assistant:
[Grounded answer]

User:
How would you apply that to a B2B SaaS product?

Assistant:
[Answer using conversation context + retrieved evidence]
```

---

# 10. Ship 30/30 Essay Flow

A request such as:

```text
ship30: How to build a strong product sense
```

or:

```text
Turn this into a Ship 30/30-style essay.
```

is routed to the dedicated Ship 30/30 skill.

```text
User Request
      │
      ▼
Intent / Keyword Routing
      │
      ▼
Ship 30/30 Skill
      │
      ▼
Grounded Transcript Context
      │
      ▼
Structured Essay
      │
      ▼
~1,250-word output
```

The essay is generated from grounded context rather than being treated as an independent source of factual information.

---

# 11. Artifact Generation Flow

The application supports generating artifacts from the current conversation context.

```text
Conversation
     │
     ▼
Artifact Endpoint
     │
     ├──────────────┐
     │              │
  Markdown        HTML
     │              │
     └──────┬───────┘
            ▼
      Persist Artifact
            │
            ▼
     Artifact Viewer
```

HTML artifacts are treated as untrusted content and rendered using a sandboxing strategy to prevent generated scripts from executing against the parent application page.

---

# 12. Provider Switching Flow

The LLM provider is controlled through `.env`.

```text
.env
 │
 ├── LLM_PROVIDER=ollama
 │
 └── LLM_PROVIDER=anthropic
```

After changing the value:

```bash
docker compose up -d --force-recreate backend
```

The backend exposes the active configuration through:

```text
GET /config
```

The frontend uses this to display the active provider/model badge.

No application-code changes are required.

---

# 13. Functional Requirements

## FR-01 — Question Answering

The system must accept natural-language PM/growth questions.

### Acceptance

- User can submit a question.
- Backend performs retrieval.
- Relevant transcript context is supplied to the LLM.
- Answer is returned to the frontend.
- Sources are displayed when available.

---

## FR-02 — Grounding Detection

The system must detect when retrieval does not provide sufficient evidence.

### Acceptance

- Retrieval returns a sufficiency signal.
- Low-quality retrieval does not silently become a confident answer.
- The model is instructed to acknowledge insufficient context.

---

## FR-03 — Source Citations

The system must expose source information for grounded answers.

### Acceptance

- At least one relevant source can be displayed.
- Source information is associated with retrieved transcript chunks.
- Citations are visible in the UI.

---

## FR-04 — Session Persistence

The system must persist sessions and messages.

### Acceptance

- New sessions can be created.
- Messages survive request boundaries.
- Follow-up questions can use previous conversation context.

---

## FR-05 — Provider Switching

The system must support Ollama and Anthropic.

### Acceptance

- Provider is selected using configuration.
- No code change is necessary.
- Active provider/model is visible in the frontend.

---

## FR-06 — Ship 30/30 Generation

The system must recognize essay-generation requests and route them to the Ship 30/30 skill.

### Acceptance

- Ship30-specific requests are routed separately.
- The generated essay is based on grounded context.
- Output is approximately 1,250 words and structurally formatted.

---

## FR-07 — Artifact Generation

The system must generate Markdown and HTML artifacts.

### Acceptance

- Current conversation context can be converted into an artifact.
- Artifact is persisted.
- Artifact is rendered in the frontend viewer.
- HTML is sandboxed.

---

## FR-08 — Graceful Errors

Major infrastructure failures must produce structured errors.

### Acceptance

- Missing Anthropic key → structured error.
- Ollama unavailable → clean `502`.
- Ollama timeout → clean `502`.
- Database failure → structured server error.
- Retrieval insufficiency → explicit model/user-facing handling.

---

# 14. Non-Functional Requirements

## Reliability

The backend should fail predictably when external dependencies are unavailable.

No dependency failure should result in an indefinite request hang.

---

## Maintainability

LLM provider logic should be abstracted so that provider switching does not require changes to business logic.

---

## Deployability

A fresh evaluator should be able to start the application using Docker Compose and a small number of commands.

---

## Traceability

Answers should remain linked to their retrieved source evidence.

---

## Resource Awareness

The default local model should be small enough to run on constrained development hardware.

---

# 15. Technical Architecture

```text
Frontend
React via CDN
Static index.html
       │
       │ HTTP
       ▼
FastAPI Backend
       │
       ├───────────────┐
       │               │
       ▼               ▼
PostgreSQL          LLM Layer
+ pgvector          │
       │            ├── Ollama
       │            └── Anthropic
       │
       ▼
Transcript Chunks
+ Embeddings
```

## Persistence

PostgreSQL stores:

- Sessions
- Messages
- Artifacts
- Transcript chunks
- Vector embeddings

## Retrieval

pgvector provides cosine similarity search using:

```sql
<=>
```

Default retrieval:

```text
top_k = 5
similarity_threshold = 0.3
```

## Embeddings

The system uses:

```text
nomic-embed-text
```

with:

```text
768 dimensions
```

---

# 16. Local Model Decision

The originally intended local model was:

```text
llama3.1:8b
```

During development, the 8B model repeatedly timed out under the available Docker/WSL2 CPU and memory resources.

The issue was investigated through direct model testing and observed timeout behavior.

The smaller model:

```text
llama3.2:1b
```

was substantially more reliable in the development environment.

### Decision

The default is:

```env
OLLAMA_MODEL=llama3.2:1b
```

### Trade-off

| Factor | `llama3.2:1b` | `llama3.1:8b` |
|---|---|---|
| Resource usage | Lower | Higher |
| Local responsiveness | Better | Slower on constrained hardware |
| Answer depth | Lower | Higher |
| Development reliability | Higher | Lower on constrained hardware |

The 8B model remains available for machines with sufficient resources.

This is an explicit engineering trade-off rather than an undocumented model substitution.

---

# 17. Risks and Trade-offs

## Local Model Quality / Latency

The largest implementation trade-off is local model performance.

`llama3.1:8b` provided the desired quality target but was too slow on the development environment.

`llama3.2:1b` was selected for reliability.

---

## Hallucination Risk

RAG reduces hallucination risk but does not eliminate it.

Mitigations include:

- Strict grounded system prompting
- Similarity threshold
- Insufficient-context detection
- Source citations

The model can still occasionally over-extrapolate from thin evidence.

---

## Cloud Cost Risk

Anthropic usage is metered.

This version does not implement a hard usage or budget cap.

Before production deployment, the system should add:

- Per-user quotas
- Token budgets
- Cost monitoring
- Rate limiting
- Usage alerts

---

## Unsafe Artifact Rendering

Generated HTML is untrusted content.

The implementation uses sandboxing so generated scripts cannot execute against the parent application context.

---

## Data Leakage

Session information is stored in PostgreSQL without encryption-at-rest configuration.

This is acceptable for a local assessment environment but should be addressed before production deployment.

---

## Corpus Coverage

The current corpus contains only 20 representative episodes.

A question whose answer exists only in the remaining episodes may correctly return:

```text
Insufficient context
```

This is an intentional safer failure mode than generating an unsupported answer.

---

# 18. Acceptance Criteria

The implementation is considered successful when:

### AC-01 — Fresh Setup

A fresh evaluator can run:

```bash
docker compose up -d db ollama backend
```

and successfully ingest the transcript corpus.

---

### AC-02 — Grounded Answer

The evaluator can ask a product/growth question and receive:

- A grounded response
- At least one visible source citation when evidence exists

---

### AC-03 — Provider Switching

Changing:

```env
LLM_PROVIDER
```

requires no code modification.

The active provider/model is visible in the UI.

---

### AC-04 — Ollama Failure

If Ollama is unavailable or times out, the application returns a clean structured error instead of hanging or crashing.

---

### AC-05 — Safe HTML

Generated HTML renders inside the Artifact Viewer without allowing untrusted scripts to execute against the parent application.

---

### AC-06 — Automated Tests

The test suite includes coverage for:

- Retrieval
- Persistence
- Routing behavior

---

# 19. Implementation Plan

The following plan reflects the implementation as executed.

## Phase 1 — Infrastructure

Implemented:

- Docker Compose
- PostgreSQL
- pgvector
- Ollama
- Environment configuration

---

## Phase 2 — Persistence

Implemented:

- Session models
- Message models
- Artifact models
- PostgreSQL persistence
- `/sessions` endpoints

---

## Phase 3 — RAG

Implemented:

- Transcript ingestion
- Chunking
- Embedding generation
- pgvector storage
- Semantic retrieval
- Similarity threshold
- Insufficient-context detection

---

## Phase 4 — Chat API

Implemented:

- `/chat`
- Retrieval + LLM orchestration
- Provider abstraction
- Session context
- Message persistence
- Structured error handling

---

## Phase 5 — Ship 30/30 Skill

Implemented:

- Dedicated Ship30 module
- Keyword/request routing
- Grounded essay generation

---

## Phase 6 — Artifact Generation

Implemented:

- Artifact endpoint
- Markdown generation
- HTML generation
- Artifact persistence
- Sandboxed HTML rendering

---

## Phase 7 — Frontend

Implemented:

- Single-file React frontend
- Chat interface
- Source citation chips
- Provider/model badge
- Split-pane Artifact Viewer

---

## Phase 8 — Validation and Documentation

Implemented:

- Automated tests
- Manual UI test plan
- Architecture documentation
- README documentation
- Failure-mode documentation
- Engineering trade-off documentation
- Agent transcripts
- Demo video

---

# 20. Out of Scope for Production

The following would be appropriate next steps for a production rollout:

1. Authentication and authorization
2. Multi-tenancy
3. Production CORS restrictions
4. Alembic database migrations
5. Secret-management infrastructure
6. Encryption at rest
7. Rate limiting
8. Cloud usage budgets
9. Observability and tracing
10. Full 320-episode ingestion
11. Better timestamp-level source citations
12. Evaluation datasets for RAG quality
13. Automated hallucination/grounding evaluation
14. Production-grade deployment infrastructure

---

# 21. Future Improvements

## Full Corpus Ingestion

Expand from the current 20 episodes to the complete transcript archive.

---

## Better Retrieval Evaluation

Introduce a benchmark dataset containing representative PM/growth questions with expected source episodes.

Measure:

- Recall@K
- Precision@K
- Grounding accuracy
- Answer faithfulness

---

## Improved Citations

Add:

- Episode title
- Guest
- Transcript section
- Timestamp when available
- Direct source links

---

## Production Observability

Track:

- Request latency
- Retrieval latency
- LLM latency
- Token usage
- Error rate
- Provider usage
- Retrieval sufficiency
- Citation rate

---

## Model Evaluation

Compare local and cloud models on a fixed evaluation set rather than relying only on qualitative inspection.

---

# 22. Product Principle

The central product principle is:

> **Prefer an explicit "I don't have enough evidence" over a confident unsupported answer.**

The application is designed around the idea that useful product advice should be:

- Grounded
- Traceable
- Actionable
- Fast to retrieve
- Honest about uncertainty

The assistant therefore treats retrieval quality as a first-class part of the product rather than simply using an LLM as a generic chatbot.

---

# 23. Definition of Done

The assessment implementation is considered complete when all of the following are true:

- [x] User can ask PM/growth questions
- [x] Relevant transcript chunks are retrieved using vector search
- [x] Answers can include source citations
- [x] Insufficient retrieval is explicitly handled
- [x] Sessions persist in PostgreSQL
- [x] Follow-up messages retain conversation context
- [x] Ollama provider works locally
- [x] Anthropic provider is supported
- [x] Provider can be switched through configuration
- [x] Active provider/model is visible in the UI
- [x] Ship 30/30 requests are separately routed
- [x] Markdown artifacts can be generated
- [x] HTML artifacts can be generated
- [x] HTML rendering is sandboxed
- [x] Backend runs through Docker Compose
- [x] Major infrastructure failures are handled gracefully
- [x] Retrieval, persistence, and routing have automated test coverage
- [x] Documentation and manual testing materials are included
- [x] Local model limitations are explicitly documented

---

# 24. Summary

Lenny Growth Assistant turns long-form product and growth podcast knowledge into a fast, conversational research workflow.

The product combines **RAG, vector search, LLM provider abstraction, persistent sessions, specialized generation skills, and artifact creation** into a single lightweight application.

The v1 assessment scope deliberately favors:

- Grounding over generic generation
- Explicit failure over hallucination
- Simple deployment over unnecessary infrastructure
- Provider flexibility over vendor lock-in
- Documented trade-offs over hidden limitations

The architecture is intentionally designed so that the initial 20-episode corpus can be expanded to the complete transcript archive without requiring a fundamental redesign.