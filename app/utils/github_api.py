import logging
from github import Github
import github
from github.GithubException import GithubException

logger = logging.getLogger(__name__)


def parse_github_payload(payload: dict) -> dict:
    """
    Extract the key fields we need from the webhook payload.
    Returns a clean dict regardless of event type.
    """
    try:
        repo_name = payload["repository"]["full_name"]
        pr_number = payload.get("number")
        action = payload.get("action")
        author = payload.get("pull_request", {}).get("user", {}).get("login", "unknown")
        pr_title = payload.get("pull_request", {}).get("title", "unknown")

        result = {
            "repo": repo_name,
            "pr_number": pr_number,
            "action": action,
            "author": author,
            "title": pr_title
        }

        logger.info(f"Parsed payload: repo={repo_name} pr=#{pr_number} action={action} author={author}")
        return result

    except KeyError as e:
        logger.error(f"Missing expected field in payload: {e}")
        return {}


def fetch_pr_diff(repo_name: str, pr_number: int, github_pat: str) -> list:
    """
    Fetch the list of changed files and their diffs for a given PR.
    Returns a list of dicts: [{filename, patch, additions, deletions}]
    """
    try:
        g = Github(auth=github.Auth.Token(github_pat))
        repo = g.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)
        files = pull_request.get_files()

        changed_files = []
        for f in files:
            changed_files.append({
                "filename": f.filename,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "patch": f.patch if f.patch else ""
            })
            logger.info(f"File: {f.filename} +{f.additions} -{f.deletions}")

        logger.info(f"Total files changed: {len(changed_files)}")
        return changed_files

    except GithubException as e:
        logger.error(f"GitHub API error: {e.status} {e.data}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching diff: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []