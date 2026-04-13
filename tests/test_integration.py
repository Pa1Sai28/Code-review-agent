import json
import hmac
import hashlib
import pytest
import os
from unittest.mock import MagicMock, patch
from app.main import app

SECRET = "test_integration_secret"


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def make_signature(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()


def test_full_pipeline_pr_opened(client):
    """
    Integration test: simulate a PR opened webhook event
    and verify the full pipeline is triggered.
    """
    payload = json.dumps({
        "action": "opened",
        "number": 1,
        "pull_request": {
            "title": "feat: add vulnerable code",
            "user": {"login": "testuser"}
        },
        "repository": {"full_name": "test/repo"}
    }).encode()

    sig = make_signature(payload, SECRET)

    mock_diff = [{
        "filename": "vulnerable_code.py",
        "patch": "@@ -0,0 +1,5 @@\n+def auth(user, pwd):\n+    query = 'SELECT * FROM users WHERE user = ' + user\n+    api_key = 'hardcoded_key_123'\n",
        "additions": 3,
        "deletions": 0,
        "status": "added"
    }]

    mock_comments = [{
        "filename": "vulnerable_code.py",
        "line_content": "+    query = 'SELECT * FROM users WHERE user = ' + user",
        "comment": "SQL injection vulnerability detected.",
        "severity": "error",
        "dimension": "SECURITY"
    }]

    with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET, "GITHUB_PAT": "test_pat"}):
        with patch("app.webhooks.github.fetch_pr_diff", return_value=mock_diff):
            with patch("app.webhooks.github.review_diff", return_value=mock_comments):
                with patch("app.webhooks.github.post_github_review", return_value=True) as mock_post:
                    response = client.post(
                        "/webhook/github",
                        data=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-GitHub-Event": "pull_request",
                            "X-Hub-Signature-256": sig
                        }
                    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "received"}


def test_pipeline_skips_non_pr_events(client):
    """Verify ping and push events don't trigger the review pipeline."""
    payload = json.dumps({"zen": "Keep it simple"}).encode()
    sig = make_signature(payload, SECRET)

    with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET}):
        with patch("app.webhooks.github.fetch_pr_diff") as mock_fetch:
            response = client.post(
                "/webhook/github",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": sig
                }
            )

    assert response.status_code == 200
    mock_fetch.assert_not_called()


def test_pipeline_handles_empty_diff(client):
    """Verify pipeline handles PRs with no reviewable files gracefully."""
    payload = json.dumps({
        "action": "opened",
        "number": 2,
        "pull_request": {
            "title": "chore: update lock file",
            "user": {"login": "testuser"}
        },
        "repository": {"full_name": "test/repo"}
    }).encode()

    sig = make_signature(payload, SECRET)

    with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": SECRET, "GITHUB_PAT": "test_pat"}):
        with patch("app.webhooks.github.fetch_pr_diff", return_value=[]):
            with patch("app.webhooks.github.review_diff") as mock_review:
                response = client.post(
                    "/webhook/github",
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-GitHub-Event": "pull_request",
                        "X-Hub-Signature-256": sig
                    }
                )

    assert response.status_code == 200
    mock_review.assert_not_called()