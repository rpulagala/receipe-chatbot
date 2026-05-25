import os
import re
import json
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

MAX_RECIPES = 5
HISTORY_FILE = Path("recipe_history.json")   # fallback for local dev


# ── Database helpers ──────────────────────────────────────────────────────────

def _get_db():
    """Return a Supabase client if credentials are configured, else None."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def load_history(ip: str) -> list:
    db = _get_db()
    if db:
        try:
            result = (
                db.table("recipe_history")
                .select("recipes")
                .eq("ip_address", ip)
                .execute()
            )
            if result.data:
                return result.data[0]["recipes"]
            return []
        except Exception:
            pass
    # Local fallback
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text()).get(ip, [])
    except Exception:
        pass
    return []


def save_history(ip: str, history: list):
    history = history[-MAX_RECIPES:]   # keep only the last 5
    db = _get_db()
    if db:
        try:
            db.table("recipe_history").upsert(
                {"ip_address": ip, "recipes": history}
            ).execute()
            return
        except Exception:
            pass
    # Local fallback
    try:
        data = json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else {}
        data[ip] = history
        HISTORY_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


# ── Session helpers ───────────────────────────────────────────────────────────

def get_client_ip() -> str:
    """Return the visitor's IP address. No login required."""
    try:
        ip = (
            st.context.headers.get("X-Forwarded-For")
            or st.context.headers.get("X-Real-Ip")
            or "local"
        )
        return ip.split(",")[0].strip()
    except Exception:
        return "local"


def is_full_recipe(text: str) -> bool:
    return "## Ingredients" in text and "## Steps" in text


def extract_recipe_name(text: str) -> str:
    match = re.search(r'^#{1,3}\s+(.+?)(?:\n|$)', text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(r'\*\*(.+?)\*\*', text)
    if match:
        return match.group(1).strip()
    return "Saved Recipe"


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Basil — AI Recipe Assistant", page_icon="🌿", layout="wide")

st.markdown("""
<style>
[data-testid="stChatMessageContent"] p { margin: 0.3rem 0; }
section[data-testid="stSidebar"] { min-width: 280px; max-width: 320px; }
</style>
""", unsafe_allow_html=True)

# ── Session state (runs once per browser session) ─────────────────────────────

if "messages" not in st.session_state:
    ip = get_client_ip()
    st.session_state.ip       = ip
    st.session_state.messages = []
    st.session_state.recipes  = load_history(ip)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # ── Top 50% — session info + API key ─────────────────────────────────────
    st.markdown("##### 🌐 Session")
    st.caption(f"IP: `{st.session_state.ip}`")

    st.markdown("##### 🔑 API Key")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = st.text_input(
            "Anthropic API key",
            type="password",
            placeholder="sk-ant-...",
            label_visibility="collapsed",
            help="Held in memory only — never stored.",
        )
    else:
        st.success("Key loaded from environment.", icon="✅")

    st.divider()

    # ── Bottom 50% — recipe history (scrollable) ──────────────────────────────
    st.markdown(f"##### 📋 Recipe History *(last {MAX_RECIPES})*")
    with st.container(height=460):
        if st.session_state.recipes:
            for i, recipe in enumerate(reversed(st.session_state.recipes)):
                with st.expander(recipe["name"]):
                    st.markdown(recipe["content"])
                    if st.button("Remove", key=f"del_{i}"):
                        st.session_state.recipes = [
                            r for r in st.session_state.recipes
                            if r["name"] != recipe["name"]
                        ]
                        save_history(st.session_state.ip, st.session_state.recipes)
                        st.rerun()
        else:
            st.caption("Full recipes will be saved here automatically.")

# ── Main chat ─────────────────────────────────────────────────────────────────

st.title("🌿 Basil")
st.caption("AI Recipe Assistant — tell me what ingredients you have!")

for msg in st.session_state.messages:
    avatar = "🌿" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

col_new, col_input = st.columns([1, 5])
with col_new:
    if st.button("🍽️ Start a new Recipe", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
with col_input:
    prompt = st.chat_input("Tell me what ingredients you have...")

if prompt:
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

    # Auto-save full recipes to DB (capped at MAX_RECIPES)
    if is_full_recipe(reply):
        name = extract_recipe_name(reply)
        if not any(r["name"] == name for r in st.session_state.recipes):
            st.session_state.recipes.append({"name": name, "content": reply})
            save_history(st.session_state.ip, st.session_state.recipes)
            st.toast(f"'{name}' saved to recipe history!", icon="📋")
