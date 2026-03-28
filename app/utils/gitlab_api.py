import logging
import gitlab
from gitlab.exceptions import GitlabError

logger = logging.getLogger(__name__)


def parse_gitlab_payload(payload: dict) -> dict:
    """
    Extract key fields from a GitLab merge request webhook payload.
    Returns same shape as parse_github_payload for unified processing.
    """
    try:
        object_attributes = payload.get("object_attributes", {})
        project = payload.get("project", {})

        repo_name = project.get("path_with_namespace", "")
        mr_iid = object_attributes.get("iid")
        action = object_attributes.get("action")
        author = payload.get("user", {}).get("username", "unknown")
        title = object_attributes.get("title", "unknown")

        result = {
            "repo": repo_name,
            "pr_number": mr_iid,
            "action": action,
            "author": author,
            "title": title
        }

        logger.info(f"Parsed GitLab payload: repo={repo_name} mr=!{mr_iid} action={action} author={author}")
        return result

    except Exception as e:
        logger.error(f"Error parsing GitLab payload: {e}")
        return {}


def fetch_mr_diff(repo_name: str, mr_iid: int, gitlab_pat: str) -> list:
    """
    Fetch the list of changed files and diffs for a GitLab merge request.
    Returns same shape as fetch_pr_diff for unified processing.
    """
    try:
        gl = gitlab.Gitlab("https://gitlab.com", private_token=gitlab_pat)
        project = gl.projects.get(repo_name)
        mr = project.mergerequests.get(mr_iid)
        diffs = mr.diffs.list()

        if not diffs:
            logger.warning("No diffs found for this MR")
            return []

        latest_diff = diffs[0]
        diff_detail = mr.diffs.get(latest_diff.id)

        changed_files = []
        for d in diff_detail.diffs:
            changed_files.append({
                "filename": d["new_path"],
                "status": "modified",
                "additions": d["diff"].count("\n+"),
                "deletions": d["diff"].count("\n-"),
                "patch": d["diff"]
            })
            logger.info(f"File: {d['new_path']}")

        logger.info(f"Total files changed: {len(changed_files)}")
        return changed_files

    except GitlabError as e:
        logger.error(f"GitLab API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching MR diff: {type(e).__name__}: {e}")
        return []