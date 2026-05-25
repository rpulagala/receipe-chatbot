# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tests

```powershell
cd backend
venv\Scripts\activate
python -m pytest tests/ -v              # all unit tests (no API key needed)
python -m pytest tests/test_api.py::TestChat::test_single_user_message_returns_reply  # single test
```

Integration tests (require a real `ANTHROPIC_API_KEY` in `.env`) are skipped automatically when only the dummy key is present.

Install test dependencies (one-time):
```powershell
pip install -r requirements-dev.txt
```

## Running the Project

**Backend** (from `backend/` directory):
```powershell
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```
Runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

**Frontend**: Open `frontend/index.html` directly in a browser (no build step). Use VS Code Live Server for auto-reload.

**First-time setup**:
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then add ANTHROPIC_API_KEY to .env
```

## Architecture

Single-endpoint FastAPI backend + no-build React frontend.

**Backend** (`backend/main.py`): One `POST /chat` endpoint that accepts a `messages` array (full conversation history), prepends `SYSTEM_PROMPT`, and calls Claude (`claude-sonnet-4-6`). Stateless — no server-side session storage.

**Frontend** (`frontend/app.js`): React loaded via CDN (no npm/bundler). Manages the full conversation history in `useState`. On each send, it slices off the static welcome message (index 0) and sends only real conversation turns to the backend. Assistant responses are rendered as markdown via `marked.js` using `dangerouslySetInnerHTML`.

**Conversation flow**:
```
User types → messages state grows → history (messages[1:] + new msg) → POST /chat → Claude API → reply appended to state
```

**Key design detail**: The welcome message shown at startup is never sent to the Claude API — `app.js:56` slices `messages` from index 1 before building the request body.

## Modifying the Chatbot Persona

The chatbot's behavior is controlled entirely by `SYSTEM_PROMPT` in `backend/main.py:21`. Changing the persona, topic constraints, or response format is done there.
