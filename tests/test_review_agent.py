import json
import pytest
from unittest.mock import MagicMock, patch
from app.agent.reviewer import review_diff, parse_review_response


SAMPLE_VALID_RESPONSE = json.dumps([
    {
        "filename": "app/auth.py",
        "line_content": "+    password = 'hardcoded123'",
        "comment": "Never hardcode credentials. Use environment variables.",
        "severity": "error",
        "dimension": "SECURITY"
    },
    {
        "filename": "app/auth.py",
        "line_content": "+    query = 'SELECT * FROM users WHERE name = ' + username",
        "comment": "SQL injection vulnerability. Use parameterized queries.",
        "severity": "error",
        "dimension": "SECURITY"
    }
])


def test_parse_valid_json_response():
    result = parse_review_response(SAMPLE_VALID_RESPONSE)
    assert len(result) == 2
    assert result[0]["severity"] == "error"
    assert result[0]["dimension"] == "SECURITY"


def test_parse_empty_array():
    result = parse_review_response("[]")
    assert result == []


def test_parse_json_with_markdown_fences():
    wrapped = f"```json\n{SAMPLE_VALID_RESPONSE}\n```"
    result = parse_review_response(wrapped)
    assert len(result) == 2


def test_parse_invalid_json_returns_empty():
    result = parse_review_response("this is not json")
    assert result == []


def test_parse_missing_required_fields():
    incomplete = json.dumps([{"filename": "app/main.py", "comment": "test"}])
    result = parse_review_response(incomplete)
    assert result == []


def test_review_diff_calls_claude():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=SAMPLE_VALID_RESPONSE)]
    mock_client.messages.create.return_value = mock_message

    with patch("app.agent.reviewer.get_claude_client", return_value=mock_client):
        result = review_diff("sample diff text")

    assert len(result) == 2
    mock_client.messages.create.assert_called_once()


def test_review_diff_returns_empty_on_api_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API error")

    with patch("app.agent.reviewer.get_claude_client", return_value=mock_client):
        result = review_diff("sample diff text")

    assert result == []


def test_review_diff_with_pr_context():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="[]")]
    mock_client.messages.create.return_value = mock_message

    pr_context = {
        "repo": "test/repo",
        "pr_number": 1,
        "author": "testuser",
        "title": "test PR"
    }

    with patch("app.agent.reviewer.get_claude_client", return_value=mock_client):
        result = review_diff("sample diff", pr_context)

    assert result == []
    call_args = mock_client.messages.create.call_args
    assert "test PR" in call_args.kwargs["messages"][0]["content"]
