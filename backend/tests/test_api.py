"""
Tests for the Recipe Assistant (Basil) API.

Run all tests:
    pytest tests/

Run a single test:
    pytest tests/test_api.py::TestChat::test_empty_messages_returns_400

Integration tests hit the real Claude API and are skipped unless
a real ANTHROPIC_API_KEY is set in the environment.
"""
import os
import pytest
from unittest.mock import MagicMock, patch

# Load .env first so a real key takes precedence, then fall back to
# a dummy so the Anthropic client can still initialise in CI / unit tests.
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from fastapi.testclient import TestClient  # noqa: E402
from main import app, SYSTEM_PROMPT  # noqa: E402

http = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def mock_claude_response(text: str) -> MagicMock:
    """Return a minimal fake anthropic.types.Message with one text block."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_status_200(self):
        res = http.get("/")
        assert res.status_code == 200

    def test_body_ok(self):
        body = http.get("/").json()
        assert body["status"] == "ok"

    def test_body_has_service(self):
        body = http.get("/").json()
        assert "service" in body


# ---------------------------------------------------------------------------
# POST /chat — request validation
# ---------------------------------------------------------------------------

class TestRequestValidation:
    def test_empty_messages_list_returns_400(self):
        res = http.post("/chat", json={"messages": []})
        assert res.status_code == 400
        assert "empty" in res.json()["detail"].lower()

    def test_missing_messages_field_returns_422(self):
        res = http.post("/chat", json={})
        assert res.status_code == 422

    def test_missing_role_field_returns_422(self):
        res = http.post("/chat", json={"messages": [{"content": "hi"}]})
        assert res.status_code == 422

    def test_missing_content_field_returns_422(self):
        res = http.post("/chat", json={"messages": [{"role": "user"}]})
        assert res.status_code == 422

    def test_wrong_type_for_messages_returns_422(self):
        res = http.post("/chat", json={"messages": "not a list"})
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /chat — successful responses
# ---------------------------------------------------------------------------

class TestChat:
    @patch("main.client.messages.create")
    def test_single_user_message_returns_reply(self, mock_create):
        mock_create.return_value = mock_claude_response("Here are some ideas!")

        res = http.post("/chat", json={
            "messages": [{"role": "user", "content": "I have eggs and cheese"}]
        })

        assert res.status_code == 200
        assert res.json()["reply"] == "Here are some ideas!"

    @patch("main.client.messages.create")
    def test_multi_turn_conversation_succeeds(self, mock_create):
        mock_create.return_value = mock_claude_response("Great choice! Here's the recipe…")

        res = http.post("/chat", json={
            "messages": [
                {"role": "user",      "content": "I have spinach and eggs"},
                {"role": "assistant", "content": "How about a frittata?"},
                {"role": "user",      "content": "Yes, tell me how"},
            ]
        })

        assert res.status_code == 200
        assert "reply" in res.json()

    @patch("main.client.messages.create")
    def test_reply_field_is_a_string(self, mock_create):
        mock_create.return_value = mock_claude_response("Sure thing!")

        res = http.post("/chat", json={
            "messages": [{"role": "user", "content": "Hi"}]
        })

        assert isinstance(res.json()["reply"], str)


# ---------------------------------------------------------------------------
# POST /chat — Claude API call arguments
# ---------------------------------------------------------------------------

class TestClaudeCallArguments:
    @patch("main.client.messages.create")
    def test_system_prompt_is_forwarded(self, mock_create):
        mock_create.return_value = mock_claude_response("ok")

        http.post("/chat", json={
            "messages": [{"role": "user", "content": "hello"}]
        })

        assert mock_create.call_args.kwargs["system"] == SYSTEM_PROMPT

    @patch("main.client.messages.create")
    def test_correct_model_is_used(self, mock_create):
        mock_create.return_value = mock_claude_response("ok")

        http.post("/chat", json={
            "messages": [{"role": "user", "content": "hello"}]
        })

        assert mock_create.call_args.kwargs["model"] == "claude-sonnet-4-6"

    @patch("main.client.messages.create")
    def test_max_tokens_is_1024(self, mock_create):
        mock_create.return_value = mock_claude_response("ok")

        http.post("/chat", json={
            "messages": [{"role": "user", "content": "hello"}]
        })

        assert mock_create.call_args.kwargs["max_tokens"] == 1024

    @patch("main.client.messages.create")
    def test_messages_are_forwarded_in_order(self, mock_create):
        mock_create.return_value = mock_claude_response("ok")

        history = [
            {"role": "user",      "content": "I have tomatoes"},
            {"role": "assistant", "content": "Make pasta!"},
            {"role": "user",      "content": "Give me the full recipe"},
        ]
        http.post("/chat", json={"messages": history})

        forwarded = mock_create.call_args.kwargs["messages"]
        assert len(forwarded) == 3
        assert forwarded[0] == {"role": "user", "content": "I have tomatoes"}
        assert forwarded[2] == {"role": "user", "content": "Give me the full recipe"}

    @patch("main.client.messages.create")
    def test_message_count_matches_input(self, mock_create):
        mock_create.return_value = mock_claude_response("ok")

        messages = [{"role": "user", "content": f"message {i}"} for i in range(5)]
        http.post("/chat", json={"messages": messages})

        assert len(mock_create.call_args.kwargs["messages"]) == 5


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

class TestCORS:
    def test_post_response_has_cors_header(self):
        # Empty messages → 400, but CORS headers should still be present
        res = http.post(
            "/chat",
            json={"messages": []},
            headers={"Origin": "http://localhost:5500"},
        )
        assert "access-control-allow-origin" in res.headers

    def test_options_preflight_succeeds(self):
        res = http.options(
            "/chat",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert res.status_code in (200, 204)


# ---------------------------------------------------------------------------
# Integration tests — skipped unless a real key is configured
# ---------------------------------------------------------------------------

REAL_KEY = (
    os.getenv("ANTHROPIC_API_KEY", "test-key") != "test-key"
    and bool(os.getenv("ANTHROPIC_API_KEY"))
)


@pytest.mark.skipif(not REAL_KEY, reason="ANTHROPIC_API_KEY not set — skipping integration tests")
class TestIntegration:
    def test_recipe_suggestion_from_ingredients(self):
        res = http.post("/chat", json={
            "messages": [{"role": "user", "content": "I have chicken, lemon, and garlic. Suggest a recipe."}]
        })
        assert res.status_code == 200
        reply = res.json()["reply"]
        assert len(reply) > 80

    def test_off_topic_is_redirected(self):
        res = http.post("/chat", json={
            "messages": [{"role": "user", "content": "What is the capital of France?"}]
        })
        assert res.status_code == 200
        reply = res.json()["reply"].lower()
        # Basil should redirect, not answer geography questions
        assert any(word in reply for word in ("food", "cook", "recipe", "ingredient", "kitchen"))

    def test_multi_turn_context_is_maintained(self):
        res = http.post("/chat", json={
            "messages": [
                {"role": "user",      "content": "I have pasta and tomatoes."},
                {"role": "assistant", "content": "You could make a simple tomato pasta!"},
                {"role": "user",      "content": "Make it vegetarian."},
            ]
        })
        assert res.status_code == 200
        assert len(res.json()["reply"]) > 30
