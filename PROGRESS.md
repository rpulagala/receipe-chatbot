# Build Progress — AI Chatbot Portfolio

## Goal
Build 3 progressively complex AI chatbot projects to learn the Upwork job stack
(Claude/OpenAI API + FastAPI + React) and use them as portfolio pieces for a client
who wants a business-specific AI chatbot with prompt engineering, conversation history,
and a clean web UI.

---

## Project Roadmap

| # | Project | Status | Stack |
|---|---------|--------|-------|
| 1 | Recipe Assistant (Basil) | **Done — running locally** | FastAPI + Claude API + React (CDN) |
| 2 | Customer Support Bot (fake SaaS) | Not started | FastAPI + Next.js |
| 3 | Interview Prep Coach | Not started | FastAPI + Next.js + streaming |

---

## Project 1: Basil — Recipe Assistant

### Location
```
C:\Users\rpula\OneDrive\Documents\python-mini-projects\recipe-chatbot\
├── backend\
│   ├── main.py           ← FastAPI app + Claude API + SYSTEM_PROMPT
│   ├── requirements.txt
│   ├── .env              ← API key lives here (DO NOT commit)
│   └── .env.example
└── frontend\
    ├── index.html        ← React via CDN, no build step
    ├── app.js            ← React components, conversation history logic
    └── style.css
```

### How to Run
```powershell
# Backend
cd C:\Users\rpula\OneDrive\Documents\python-mini-projects\recipe-chatbot\backend
venv\Scripts\activate
uvicorn main:app --reload

# Frontend — just open in browser:
C:\Users\rpula\OneDrive\Documents\python-mini-projects\recipe-chatbot\frontend\index.html
```

### What Was Built
- `POST /chat` endpoint that accepts a `messages[]` array and calls Claude
- System prompt engineering: persona (Basil), constraints (food only), output format (## Ingredients / ## Steps)
- Conversation history: React state holds full message array; entire history sent on every request
- Markdown rendering in assistant bubbles (recipes with headers and bullets)
- Animated typing indicator while waiting for Claude response
- Enter to send, Shift+Enter for newline

### Key Concepts Demonstrated
- **Prompt engineering**: `SYSTEM_PROMPT` in `main.py:21` — persona + behavior rules + output format
- **Multi-turn memory**: frontend owns the history; backend is stateless; full array sent each call (`main.py:64`)
- **CORS**: configured so the plain HTML frontend can call the FastAPI backend
- **Pydantic models**: `ChatRequest` / `ChatResponse` for request validation and API docs
- **FastAPI auto-docs**: visit `http://localhost:8000/docs` when backend is running

---

## What to Build Next

### Project 2: Customer Support Bot
- Pick a fake SaaS product (e.g. "TaskFlow" — a project management tool)
- Write 2-3 markdown files describing the fake product's features, pricing, FAQ
- Inject that content into the system prompt (prompt stuffing / RAG-lite)
- Upgrade frontend to **Next.js** (first time using it)
- Add a sidebar showing "suggested questions"
- New concept to learn: **structured system prompts with injected context**

### Project 3: Interview Prep Coach
- AI conducts a mock technical interview, asks follow-up questions
- Gives structured feedback at the end of the session
- Add **streaming responses** (`stream=True` in Claude API) so text appears word by word
- New concept to learn: **Server-Sent Events (SSE)** for streaming

---

## Upwork Job Requirements Checklist

| Requirement | Covered by |
|-------------|-----------|
| Claude or OpenAI API integration | Project 1 (Claude) |
| React.js frontend | Project 1 (React via CDN) → Project 2/3 (Next.js) |
| Python FastAPI backend | Project 1 |
| Prompt engineering + system prompt | Project 1 SYSTEM_PROMPT |
| Conversation history | Project 1 messages[] array |
| Clean documented code on GitHub | Push all 3 projects when done |

---

## Session Notes

- Used `anthropic==0.40.0` SDK — `client.messages.create()` is the correct method
- Model used: `claude-sonnet-4-6`
- Frontend uses React 18 + Babel via unpkg CDN (no Node/npm needed to run)
- `marked.js` via CDN handles markdown rendering in chat bubbles
- The `.env` file must be in `backend/` alongside `main.py` for `load_dotenv()` to find it
- The welcome message is UI-only — it is sliced off (`messages.slice(1)`) before sending to the API
