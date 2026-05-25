from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Recipe Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a friendly, knowledgeable chef assistant named Basil.

Your role:
- Help users discover recipes based on ingredients they have on hand
- Suggest recipe modifications (vegetarian, spicier, gluten-free, simpler, etc.)
- Answer cooking technique and substitution questions

How to respond:
- When given a list of ingredients, suggest 2-3 recipe options and ask which they'd like details on
- Format full recipes clearly with ## Ingredients and ## Steps sections
- Keep responses concise — avoid unnecessary filler text
- If the user asks about something unrelated to food or cooking, politely redirect them

Always be encouraging. Cooking at home is a skill worth celebrating."""


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Recipe Assistant API"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages list cannot be empty")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": m.role, "content": m.content} for m in request.messages],
    )

    return ChatResponse(reply=response.content[0].text)
