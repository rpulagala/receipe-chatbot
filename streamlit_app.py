import os
import re
import json
import socket
from pathlib import Path

import streamlit as st
import anthropic
from dotenv import load_dotenv

load_dotenv()

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

HISTORY_FILE = Path("recipe_history.json")


def get_session_identity():
    """Return (computer_name, ip) for the current user. No login required."""
    try:
        ip = (
            st.context.headers.get("X-Forwarded-For")
            or st.context.headers.get("X-Real-Ip")
            or "local"
        )
        ip = ip.split(",")[0].strip()
    except Exception:
        ip = "local"

    # Computer name: available when running locally; falls back to IP on cloud
    try:
        computer = socket.gethostname()
    except Exception:
        computer = ip

    return computer, ip


def load_history(user_id: str) -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text()).get(user_id, [])
        except Exception:
            pass
    return []


def save_history(user_id: str, history: list):
    try:
        data = json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else {}
        data[user_id] = history
        HISTORY_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def is_full_recipe(text: str) -> bool:
    return "## Ingredients" in text and "## Steps" in text


def extract_recipe_name(text: str) -> str:
    """Pull the recipe title out of a formatted response."""
    match = re.search(r'^#{1,3}\s+(.+?)(?:\n|$)', text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(r'\*\*(.+?)\*\*', text)
    if match:
        return match.group(1).strip()
    return "Saved Recipe"


# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Basil — AI Recipe Assistant", page_icon="🌿", layout="wide")

st.markdown("""
<style>
[data-testid="stChatMessageContent"] p { margin: 0.3rem 0; }
section[data-testid="stSidebar"] { min-width: 280px; max-width: 320px; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────

if "identity" not in st.session_state:
    computer, ip = get_session_identity()
    st.session_state.computer   = computer
    st.session_state.ip         = ip
    st.session_state.user_id    = ip          # key for persistent storage
    st.session_state.messages   = []
    st.session_state.recipes    = load_history(ip)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Session info
    st.markdown("### 💻 Your Session")
    st.markdown(f"**Computer:** `{st.session_state.computer}`")
    st.markdown(f"**IP address:** `{st.session_state.ip}`")
    st.divider()

    # API key
    st.markdown("### 🔑 API Key")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = st.text_input(
            "Anthropic API key",
            type="password",
            placeholder="sk-ant-...",
            help="Held in memory only — never stored.",
        )
    else:
        st.success("Key loaded from environment.", icon="✅")
    st.divider()

    # Recipe history
    st.markdown("### 📋 Recipe History")
    if st.session_state.recipes:
        for i, recipe in enumerate(reversed(st.session_state.recipes)):
            with st.expander(recipe["name"]):
                st.markdown(recipe["content"])
                if st.button("🗑️ Remove", key=f"del_{i}"):
                    st.session_state.recipes = [
                        r for r in st.session_state.recipes if r["name"] != recipe["name"]
                    ]
                    save_history(st.session_state.user_id, st.session_state.recipes)
                    st.rerun()
    else:
        st.caption("Recipes Basil provides will appear here automatically.")
    st.divider()

    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

# ── Main chat ─────────────────────────────────────────────────────────────────

st.title("🌿 Basil")
st.caption("AI Recipe Assistant — tell me what ingredients you have!")

for msg in st.session_state.messages:
    avatar = "🌿" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if prompt := st.chat_input("Tell me what ingredients you have…"):
    if not api_key:
        st.warning("Enter your Anthropic API key in the sidebar to start chatting.", icon="🔑")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌿"):
        client = anthropic.Anthropic(api_key=api_key)
        with st.spinner(""):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=st.session_state.messages,
            )
            reply = response.content[0].text
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Auto-save full recipes to history
    if is_full_recipe(reply):
        name = extract_recipe_name(reply)
        if not any(r["name"] == name for r in st.session_state.recipes):
            st.session_state.recipes.append({"name": name, "content": reply})
            save_history(st.session_state.user_id, st.session_state.recipes)
            st.toast(f"✅ "{name}" saved to your recipe history!", icon="📋")
