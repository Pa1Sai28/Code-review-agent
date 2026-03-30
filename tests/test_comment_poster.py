import pytest
from unittest.mock import MagicMock, patch
from app.agent.comment_poster import format_review_body, post_github_review

SAMPLE_COMMENTS = [
    {
        "filename": "app/auth.py",
        "line_content": "+    password = 'hardcoded123'",
        "comment": "Never hardcode credentials.",
        "severity": "error",
        "dimension": "SECURITY"
    },
    {
        "filename": "app/auth.py",
        "line_content": "+    query = 'SELECT * FROM users WHERE name = ' + username",
        "comment": "SQL injection vulnerability.",
        "severity": "error",
        "dimension": "SECURITY"
    },
    {
        "filename": "app/main.py",
        "line_content": "+    print('debug')",
        "comment": "Remove debug print statement.",
        "severity": "warning",
        "dimension": "STYLE"
    }
]

PR_CONTEXT = {
    "repo": "Pa1Sai28/crates",
    "pr_number": 1,
    "author": "Pa1Sai28",
    "title": "feat: add auth"
}


def test_format_review_body_contains_summary():
    body = format_review_body(SAMPLE_COMMENTS, PR_CONTEXT)
    assert "AI Code Review by Claude" in body
    assert "Errors: 2" in body
    assert "Warnings: 1" in body
    assert "Total issues: 3" in body


def test_format_review_body_no_issues():
    body = format_review_body([], PR_CONTEXT)
    assert "No issues found" in body


def test_format_review_body_contains_repo():
    body = format_review_body(SAMPLE_COMMENTS, PR_CONTEXT)
    assert "Pa1Sai28/crates" in body


def test_post_github_review_success():
    mock_github = MagicMock()
    mock_repo = MagicMock()
    mock_pr = MagicMock()

    mock_file = MagicMock()
    mock_file.filename = "app/auth.py"
    mock_file.patch = "@@ -0,0 +1,5 @@\n+    password = 'hardcoded123'\n+    query = 'SELECT'\n"
    mock_pr.get_files.return_value = [mock_file]
    mock_repo.get_pull.return_value = mock_pr
    mock_github.get_repo.return_value = mock_repo

    with patch("app.agent.comment_poster.Github", return_value=mock_github):
        with patch("app.agent.comment_poster.github") as mock_gh_module:
            mock_gh_module.Auth.Token.return_value = MagicMock()
            result = post_github_review(
                "Pa1Sai28/crates", 1, SAMPLE_COMMENTS, "fake_pat", PR_CONTEXT
            )

    assert result is True
    mock_pr.create_review.assert_called_once()


def test_post_github_review_handles_api_error():
    with patch("app.agent.comment_poster.Github") as mock_github_class:
        mock_github_class.side_effect = Exception("API Error")
        result = post_github_review(
            "Pa1Sai28/crates", 1, SAMPLE_COMMENTS, "fake_pat"
        )
    assert result is False


def test_post_github_review_empty_comments():
    mock_github = MagicMock()
    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_pr.get_files.return_value = []
    mock_repo.get_pull.return_value = mock_pr
    mock_github.get_repo.return_value = mock_repo

    with patch("app.agent.comment_poster.Github", return_value=mock_github):
        with patch("app.agent.comment_poster.github") as mock_gh_module:
            mock_gh_module.Auth.Token.return_value = MagicMock()
            result = post_github_review(
                "Pa1Sai28/crates", 1, [], "fake_pat", PR_CONTEXT
            )

    assert result is True
