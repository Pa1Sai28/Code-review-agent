from app.utils.github_api import parse_github_payload


def test_parse_valid_payload():
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "title": "feat: add login",
            "user": {"login": "testuser"}
        },
        "repository": {
            "full_name": "testuser/testrepo"
        }
    }
    result = parse_github_payload(payload)
    assert result["repo"] == "testuser/testrepo"
    assert result["pr_number"] == 42
    assert result["action"] == "opened"
    assert result["author"] == "testuser"
    assert result["title"] == "feat: add login"


def test_parse_missing_pr_number():
    payload = {
        "repository": {"full_name": "testuser/testrepo"}
    }
    result = parse_github_payload(payload)
    assert result.get("pr_number") is None


def test_parse_missing_repository():
    result = parse_github_payload({})
    assert result == {}