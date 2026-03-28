import json
import hmac
import hashlib
import pytest
from app.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def make_github_signature(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()


SECRET = "test_secret_for_integration"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_github_webhook_valid_signature(client):
    payload = json.dumps({"action": "opened", "number": 1,
                          "repository": {"full_name": "test/repo"},
                          "pull_request": {"title": "test", "user": {"login": "testuser"}}
                         }).encode()
    sig = make_github_signature(payload, SECRET)

    import os
    os.environ["GITHUB_WEBHOOK_SECRET"] = SECRET

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


def test_github_webhook_invalid_signature(client):
    payload = json.dumps({"action": "opened"}).encode()

    response = client.post(
        "/webhook/github",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalidsignature"
        }
    )
    assert response.status_code == 403


def test_github_webhook_missing_signature(client):
    payload = json.dumps({"action": "opened"}).encode()

    response = client.post(
        "/webhook/github",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 403


def test_gitlab_webhook_valid_token(client):
    payload = json.dumps({
        "object_kind": "merge_request",
        "object_attributes": {"action": "open", "iid": 1, "title": "test"},
        "project": {"path_with_namespace": "test/repo"},
        "user": {"username": "testuser"}
    }).encode()

    import os
    os.environ["GITLAB_WEBHOOK_TOKEN"] = "test_gitlab_token"

    response = client.post(
        "/webhook/gitlab",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Gitlab-Event": "Merge Request Hook",
            "X-Gitlab-Token": "test_gitlab_token"
        }
    )
    assert response.status_code == 200
    assert response.get_json() == {"status": "received"}


def test_gitlab_webhook_invalid_token(client):
    payload = json.dumps({"object_kind": "merge_request"}).encode()

    response = client.post(
        "/webhook/gitlab",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Gitlab-Event": "Merge Request Hook",
            "X-Gitlab-Token": "wrongtoken"
        }
    )
    assert response.status_code == 403


def test_server_stays_up_after_malformed_payload(client):
    import os
    os.environ["GITHUB_WEBHOOK_SECRET"] = SECRET

    malformed = b"this is not json at all"
    sig = make_github_signature(malformed, SECRET)

    response = client.post(
        "/webhook/github",
        data=malformed,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig
        }
    )
    assert response.status_code in [200, 400, 500]

    health = client.get("/health")
    assert health.status_code == 200