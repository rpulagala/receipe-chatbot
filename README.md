# Basil — AI Recipe Assistant

A simple chatbot built with **FastAPI + Claude API + React** (no build step).

## Project Structure

```
recipe-chatbot/
├── backend/
│   ├── main.py          # FastAPI app with /chat endpoint
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html       # Entry point (React via CDN)
    ├── app.js           # React components
    └── style.css        # Chat UI styles
```

## Setup

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

# Add your API key
copy .env.example .env
# Edit .env and paste your Anthropic API key

uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. Visit `/docs` for the auto-generated API docs.

### Frontend

Open `frontend/index.html` directly in your browser — no build step needed.

> Tip: Use the VS Code **Live Server** extension for auto-reload on file changes.

## Key Concepts to Study

| File | What it teaches |
|------|----------------|
| `main.py` | FastAPI routing, Pydantic validation, CORS, Claude API |
| `app.js`  | React hooks (`useState`, `useEffect`, `useRef`), fetch API |
| `SYSTEM_PROMPT` in `main.py` | Prompt engineering — persona, constraints, output format |

## How Conversation History Works

The frontend keeps the full `messages` array in React state. Every request sends
the **entire history** to the backend, which passes it to Claude. This is how
Claude maintains context — it sees the whole conversation each time.

```
User types → messages array grows → full array sent to /chat → Claude responds → added to array
```
