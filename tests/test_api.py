"""
Tests for FastAPI endpoints (main.py)
These tests verify the API structure without requiring Ollama/MCP server.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


@pytest.fixture
def client():
    """
    Create a test client with mocked agent dependencies.
    We mock the LLM and MCP since they require external services.
    """
    from fastapi.testclient import TestClient

    # Mock the agent_utils before importing main
    with patch('agent_utils.get_agent', new_callable=AsyncMock) as mock_get_agent, \
         patch('agent_utils.handle_user_message', new_callable=AsyncMock) as mock_handle:

        mock_agent = MagicMock()
        mock_tools = [MagicMock()]
        mock_tools[0].metadata.name = "test_tool"
        mock_tools[0].metadata.description = "A test tool for testing purposes only"
        mock_get_agent.return_value = (mock_agent, mock_tools)
        mock_handle.return_value = ("Test response", [])

        from main import app
        
        with TestClient(app) as test_client:
            yield test_client, mock_handle


class TestRootEndpoint:
    """Tests for GET /"""

    def test_root_returns_ok(self, client):
        """Health check should return status ok"""
        test_client, _ = client
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_has_message(self, client):
        """Health check should have a message"""
        test_client, _ = client
        response = test_client.get("/")
        data = response.json()
        assert "message" in data


class TestChatEndpoint:
    """Tests for POST /chat"""

    def test_chat_success(self, client):
        """Should return a response for valid message"""
        test_client, mock_handle = client
        mock_handle.return_value = ("Hello! I can help you.", [])

        response = test_client.post("/chat", json={"message": "hello"})
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! I can help you."
        assert data["tool_calls"] == []

    def test_chat_with_verbose(self, client):
        """Should include tool calls when verbose=True"""
        test_client, mock_handle = client
        mock_handle.return_value = ("Got reviews", [
            {"type": "call", "tool_name": "get_comments", "tool_kwargs": {}}
        ])

        response = test_client.post("/chat", json={
            "message": "show reviews",
            "verbose": True
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool_name"] == "get_comments"

    def test_chat_without_verbose_hides_tools(self, client):
        """Should hide tool calls when verbose=False (default)"""
        test_client, mock_handle = client
        mock_handle.return_value = ("Got reviews", [
            {"type": "call", "tool_name": "get_comments", "tool_kwargs": {}}
        ])

        response = test_client.post("/chat", json={"message": "show reviews"})
        data = response.json()
        assert data["tool_calls"] == []

    def test_chat_empty_message(self, client):
        """Should accept empty message (agent handles it)"""
        test_client, _ = client
        response = test_client.post("/chat", json={"message": ""})
        assert response.status_code == 200

    def test_chat_missing_message(self, client):
        """Should return 422 for missing message field"""
        test_client, _ = client
        response = test_client.post("/chat", json={})
        assert response.status_code == 422


class TestResetEndpoint:
    """Tests for POST /reset"""

    def test_reset_success(self, client):
        """Should reset context successfully"""
        test_client, _ = client
        response = test_client.post("/reset")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestCORS:
    """Tests for CORS configuration"""

    def test_cors_headers(self, client):
        """Should include CORS headers"""
        test_client, _ = client
        response = test_client.options(
            "/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )
        assert response.status_code == 200
