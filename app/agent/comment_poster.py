import logging
from github import Github
from github.GithubException import GithubException
import github

logger = logging.getLogger(__name__)


def build_diff_position_map(files) -> dict:
    """
    Build a map of {filename: {line_content: diff_position}}
    GitHub inline comments need the diff position, not the line number.
    Diff position is the line's index within the unified diff output.
    """
    position_map = {}

    for f in files:
        filename = f.filename
        patch = f.patch if f.patch else ""
        position_map[filename] = {}

        position = 0
        for line in patch.split("\n"):
            position += 1
            stripped = line.strip()
            if stripped:
                position_map[filename][stripped] = position

    return position_map


def format_review_body(comments: list, pr_context: dict = None) -> str:
    """
    Create the review summary that appears at the top of the review.
    """
    error_count = sum(1 for c in comments if c.get("severity") == "error")
    warning_count = sum(1 for c in comments if c.get("severity") == "warning")
    info_count = sum(1 for c in comments if c.get("severity") == "info")

    repo = pr_context.get("repo", "unknown") if pr_context else "unknown"
    pr_number = pr_context.get("pr_number", "unknown") if pr_context else "unknown"

    summary = (
        f"## AI Code Review by Claude\n\n"
        f"Reviewed PR #{pr_number} in `{repo}`\n\n"
        f"### Summary\n"
        f"- Errors: {error_count}\n"
        f"- Warnings: {warning_count}\n"
        f"- Info: {info_count}\n"
        f"- Total issues: {len(comments)}\n\n"
    )

    if len(comments) == 0:
        summary += "No issues found. "
        summary += "The code looks good! \n"
    else:
        summary += "See inline comments for details.\n"

    summary += "\n---\n*Powered by Anthropic Claude via Code Review Agent*"
    return summary


def post_github_review(
    repo_name: str,
    pr_number: int,
    comments: list,
    github_pat: str,
    pr_context: dict = None
) -> bool:
    """
    Post Claude's review comments as a GitHub Pull Request Review.

    Posts all comments as a single review — industry standard approach.
    Inline comments appear on the specific diff lines that were changed.

    Args:
        repo_name: full repo name e.g. 'Pa1Sai28/crates'
        pr_number: PR number
        comments: list of comment dicts from reviewer.py
        github_pat: GitHub personal access token
        pr_context: optional PR metadata dict

    Returns:
        True if review posted successfully, False otherwise
    """
    try:
        g = Github(auth=github.Auth.Token(github_pat))
        repo = g.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)

        files = list(pull_request.get_files())
        position_map = build_diff_position_map(files)

        review_comments = []
        skipped = 0

        for c in comments:
            filename = c.get("filename", "")
            line_content = c.get("line_content", "").strip()
            if line_content.startswith("+"):
                line_content = line_content[1:].strip()

            file_positions = position_map.get(filename, {})

            position = None
            for content, pos in file_positions.items():
                if line_content in content or content in line_content:
                    position = pos
                    break

            if position is None:
                logger.warning(f"Could not find diff position for: {line_content[:50]}")
                skipped += 1
                continue

            severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                c.get("severity", "info"), "🔵"
            )
            dimension = c.get("dimension", "")

            review_comments.append({
                "path": filename,
                "position": position,
                "body": f"{severity_emoji} **{dimension}**\n\n{c.get('comment', '')}"
            })

        review_body = format_review_body(comments, pr_context)

        if review_comments:
            pull_request.create_review(
                body=review_body,
                event="COMMENT",
                comments=[
                    {
                        "path": rc["path"],
                        "position": rc["position"],
                        "body": rc["body"]
                    }
                    for rc in review_comments
                ]
            )
            logger.info(f"Posted review with {len(review_comments)} inline comments")
        else:
            pull_request.create_review(
                body=review_body,
                event="COMMENT"
            )
            logger.info("Posted review summary (no inline comments could be positioned)")

        if skipped > 0:
            logger.warning(f"Skipped {skipped} comments — could not find diff position")

        return True

    except GithubException as e:
        logger.error(f"GitHub API error posting review: {e.status} {e.data}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error posting review: {type(e).__name__}: {e}")
        return False
