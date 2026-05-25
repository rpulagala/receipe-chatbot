import os
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

st.set_page_config(page_title="Basil — AI Recipe Assistant", page_icon="🌿")

st.markdown("""
<style>
[data-testid="stChatMessageContent"] p { margin: 0.3rem 0; }
</style>
""", unsafe_allow_html=True)

# Sidebar — API key input (used when no env key is present)
with st.sidebar:
    st.markdown("### 🔑 API Key")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = st.text_input(
            "Anthropic API key",
            type="password",
            placeholder="sk-ant-...",
            help="Your key is only held in memory for this session and never stored.",
        )
    else:
        st.success("API key loaded from environment.", icon="✅")
    st.divider()
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

st.title("🌿 Basil")
st.caption("AI Recipe Assistant — tell me what ingredients you have!")

if "messages" not in st.session_state:
    st.session_state.messages = []

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
