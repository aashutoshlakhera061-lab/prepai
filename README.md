# PrepAI — Adaptive AI Interview Preparation Platform

[![CI](https://github.com/YOUR_USERNAME/prepai/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/prepai/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Next.js](https://img.shields.io/badge/next.js-14-black)
![License](https://img.shields.io/badge/license-MIT-green)

Upload your notes, previous-year papers, or a job description → PrepAI turns
them into summaries, flashcards, adaptive mock tests, and a study assistant —
all grounded in **your own material**, with retrieval-augmented generation
(RAG) so the AI can't wander off into hallucinated facts.

**[Live demo](#) · [Screenshots](#screenshots) · [Setup](#setup--local-development)**
*(replace the live demo link once deployed, or remove this line)*

## Why this exists

Most "AI study tool" demos just prompt an LLM with generic knowledge. PrepAI
is built around a different idea: every piece of generated content — summary,
flashcard, mock test question, chat answer — must be traceable back to a
specific chunk of *your* uploaded document. That constraint shapes the whole
architecture: chunking on upload, TF-IDF retrieval before every generation
call, and page-level source citations in responses.

It also closes a real feedback loop, not just a one-shot generator: mock test
results feed into a per-topic weakness score, which then biases what the
*next* mock test asks more questions about — the same idea behind spaced
repetition, applied to test generation.

## Features

| Feature | What it does |
|---|---|
| 📄 **Smart upload** | PDF → text extraction → chunking → private per-user knowledge base |
| 📝 **AI summaries** | Quick / detailed / interview-focused / cheat-sheet modes, grounded only in your material |
| 🃏 **Flashcards** | Auto-generated Q&A pairs with spaced-repetition scheduling (retention score drives next-due date) |
| 🧪 **Adaptive mock tests** | MCQs generated from your material, topic-tagged, automatically weighted toward your weakest topics over time |
| 📊 **Progress dashboard** | Interview readiness estimate, topic-score breakdown, accuracy trend, priority weak topic |
| 🐛 **Mistake book** | Every wrong answer logged with topic, your answer, and the correct one |
| 💬 **RAG study assistant** | Chat that answers only from your uploaded material — cites page numbers, says "not covered" rather than guessing |
| 🔌 **Swappable LLM backend** | One interface, three providers (Anthropic / Groq / OpenRouter) — switch via a single env var |

## Tech stack

**Backend:** FastAPI · SQLAlchemy · PostgreSQL/SQLite · JWT auth · pytest
**Frontend:** Next.js 14 (App Router) · TypeScript · Tailwind CSS · Recharts
**AI/ML:** RAG via TF-IDF retrieval (scikit-learn) · Anthropic/Groq/OpenRouter APIs
**Infra:** Docker Compose · GitHub Actions CI

## Screenshots

*(add 3-4 screenshots here once captured — dashboard, flashcards, mock test, chat)*

```
![Dashboard](docs/screenshots/dashboard.png)
![Flashcards](docs/screenshots/flashcards.png)
![Mock Test](docs/screenshots/mocktest.png)
```

## Architecture

```
                     ┌──────────────┐
   PDF upload   ───▶ │   FastAPI     │
                     │   backend     │
                     └───────┬───────┘
                             │
                 chunk + store in DB
                             │
                             ▼
                     ┌──────────────┐
   User question ───▶│  TF-IDF RAG   │───▶ relevant chunks
                     │  retrieval    │
                     └───────┬───────┘
                             │
                             ▼
                     ┌──────────────┐
                     │  LLM provider │  (Anthropic / Groq / OpenRouter)
                     │  (swappable)  │
                     └───────┬───────┘
                             │
                 summary / flashcards / questions / chat reply
                             │
                             ▼
                     ┌──────────────┐
                     │  Next.js UI   │
                     └──────────────┘
```

## Scope note

This is a working MVP core, built to be extended — not the full 19-feature
vision (voice interviews, gamification, a trained ML readiness model,
company-specific research). Those are scoped out below with clear extension
points, because they each deserve real design/data work rather than a stub.

## What's intentionally NOT built yet (and how to extend)

| Feature | Why deferred | Where to start |
|---|---|---|
| Voice mock interview | Needs speech-to-text, filler-word/pace analysis, and a separate audio pipeline | Add a `/interview` router using a STT API, feed the transcript through `llm_service.generate_text` for evaluation |
| Resume + JD matching | Needs resume parsing (docx/pdf) + skill-gap scoring | Extend `pdf_processor.py` for resumes, add a `/resume` router that prompts Claude to compare resume vs. JD text |
| Company-specific prep | Requires *verified, current* company info — must not let the LLM hallucinate this | Wire in a real search API (not model memory) before generating company-specific content |
| Trained ML readiness/forgetting model | Needs real usage data first | Current `dashboard.py` uses a simple weighted-average heuristic — replace once you have labeled outcomes (e.g. logistic regression on mock scores → interview pass/fail) |
| Gamification (XP, streaks, badges) | Pure product feature, no research needed | Add `streak`, `xp`, `level` columns to `User`, increment on relevant actions |
| Mistake categorization (conceptual/memory/careless/etc.) | Currently defaults to "conceptual" | Add a second Claude call in `mocktest.py`'s submit handler classifying each wrong answer |

## Project structure

```
prepai/
├── backend/                 FastAPI + SQLAlchemy + Claude API
│   ├── app/
│   │   ├── main.py          App entrypoint, router registration
│   │   ├── config.py        Settings (reads .env)
│   │   ├── database.py      SQLAlchemy engine/session
│   │   ├── models.py        DB tables (User, Document, Chunk, Flashcard, MockTest, ...)
│   │   ├── schemas.py       Pydantic request/response models
│   │   ├── auth.py          JWT + password hashing
│   │   ├── services/
│   │   │   ├── pdf_processor.py   PDF text extraction + chunking
│   │   │   ├── rag.py              TF-IDF retrieval for chat/context building
│   │   │   └── llm_service.py      Claude API wrapper (text + JSON generation)
│   │   └── routers/
│   │       ├── auth.py, upload.py, summary.py, flashcards.py,
│   │       └── mocktest.py, dashboard.py, chat.py, mistakes.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                 Next.js 14 (App Router) + TypeScript + Tailwind
│   ├── app/
│   │   ├── page.tsx          Login/register
│   │   ├── upload/           Upload PDFs, list documents
│   │   ├── dashboard/        Charts (recharts) — readiness, topic scores, trend
│   │   ├── flashcards/       Generate + review flashcards
│   │   ├── mocktest/         Generate + take + score mock tests
│   │   └── chat/             RAG study assistant
│   ├── lib/api.ts            Axios client with JWT interceptor
│   └── Dockerfile
└── docker-compose.yml         Postgres + backend + frontend, one command
```

## Testing

The backend has a real automated test suite (pytest) covering auth, document
upload/ownership isolation, flashcard generation + spaced-repetition scoring,
and mock test generation/scoring/mistake-logging. Tests run against an
isolated in-memory database and mock all LLM/PDF calls — no API key or real
file needed to run them.

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

For a coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```

## Setup — local development

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env — set ANTHROPIC_API_KEY (get one at console.anthropic.com)
# DATABASE_URL defaults to local SQLite, no Postgres needed to get started
uvicorn app.main:app --reload
```
Backend runs at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Frontend runs at `http://localhost:3000`.

### 3. Or run everything with Docker

```bash
# first, put your real ANTHROPIC_API_KEY in backend/.env (copy from .env.example)
docker compose up --build
```

## Using it

1. Go to `http://localhost:3000`, register an account.
2. Go to **Upload**, upload a PDF (notes, previous-year paper, textbook chapter). Note the **Document ID** shown in the list.
3. Go to **Flashcards**, paste the Document ID, click **Generate**, then review cards.
4. Go to **Mock Test**, paste the Document ID, pick difficulty/count, generate and take it — mistakes are automatically logged.
5. Go to **Dashboard** to see readiness score and topic breakdown build up as you take more tests.
6. Go to **Study Assistant** to ask questions about the uploaded material.

## Notes on the RAG approach

Retrieval uses TF-IDF cosine similarity (`scikit-learn`) rather than a vector
embedding API — this keeps the MVP free of an extra API dependency and works
fully offline once installed. It's good enough for single-document Q&A. If you
scale to many long documents and need true semantic search, swap
`services/rag.py` for embeddings + a vector store (pgvector, Chroma, or
Pinecone) — the router code (`chat.py`) doesn't need to change, just the
retrieval function's internals.

## Known limitations of this MVP

- PDF only (no DOCX/PPTX) — extend `pdf_processor.py`
- Single global LLM call per generation (no streaming) — fine for MVP, add SSE/websockets for real-time token streaming later
- No rate limiting / usage quotas on the LLM API calls — add before any public deployment
- Mistake categorization is a placeholder — see table above

## Using Groq or OpenRouter instead of Anthropic

`backend/app/services/llm_service.py` supports three providers via `LLM_PROVIDER` in `.env`:
`anthropic`, `groq`, or `openrouter`. Groq and OpenRouter are OpenAI-compatible, so they're
called through the standard `openai` Python package pointed at each provider's base URL — no
other app code needs to change. See `.env.example` for the exact variables and recommended
model ids per provider.

## Troubleshooting — fixes for issues hit during real setup

These are pinned in `requirements.txt` already if you're starting fresh, but documented here
in case you hit them (e.g. after manually recreating a venv):

- **`AttributeError: module 'bcrypt' has no attribute '__about__'`** on register/login — newer
  `bcrypt` releases dropped an attribute `passlib` still reads. Fix: `pip install "bcrypt==4.0.1"`.
- **`TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`** when calling
  Groq/OpenRouter — a newer `httpx` is incompatible with `openai==1.51.0`. Fix:
  `pip install "httpx==0.27.2"`.
- **`ModuleNotFoundError: No module named 'openai'`** — the install was interrupted or run before
  this package was added. Fix: `pip install openai==1.51.0`, or just re-run
  `pip install -r requirements.txt` (safe to run repeatedly, it skips what's already installed).
- **numpy fails to build from source on Windows** (`Unknown compiler(s)` / Meson errors) — usually
  means you're on a very new Python version (e.g. 3.14) that doesn't yet have a pre-built numpy
  wheel for the pinned version. Either install Python 3.11/3.12 alongside your current version and
  create the venv with `py -3.12 -m venv venv`, or loosen the pins to `numpy>=2.2` and
  `scikit-learn>=1.6` in `requirements.txt`.
- **PowerShell: "running scripts is disabled on this system"** when activating the venv — run
  `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once, then retry
  `venv\Scripts\activate`.
- **Frontend shows `AxiosError: Network Error`** — the backend (`uvicorn`) isn't running or was
  stopped. Check that terminal window for `Application startup complete`; restart with
  `uvicorn app.main:app --reload` if not.
- **`RuntimeError: LLM_PROVIDER is set to '...' but ..._API_KEY is empty`** on startup — this is
  intentional: the app now validates your LLM config at boot instead of failing later mid-request.
  Check `.env` has both `LLM_PROVIDER` and the matching `*_API_KEY` filled in correctly.
