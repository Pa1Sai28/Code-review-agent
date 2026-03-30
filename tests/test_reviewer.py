import pytest
import os
from unittest.mock import MagicMock, patch
from app.agent.reviewer import get_claude_client
from app.agent.reviewer import test_claude_connection as call_claude_test


def test_get_claude_client_missing_key():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not set"):
            get_claude_client()


def test_connection_calls_api():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Claude connection successful.")]
    mock_client.messages.create.return_value = mock_message

    with patch("app.agent.reviewer.get_claude_client", return_value=mock_client):
        result = call_claude_test()

    assert result == "Claude connection successful."
    mock_client.messages.create.assert_called_once()


def test_claude_uses_correct_model():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Claude connection successful.")]
    mock_client.messages.create.return_value = mock_message

    with patch("app.agent.reviewer.get_claude_client", return_value=mock_client):
        call_claude_test()

    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"