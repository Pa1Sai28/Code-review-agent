import logging
import json
import os
import threading
from flask import Blueprint, request, abort
from dotenv import load_dotenv
from nacl import secret
from app.utils.security import verify_gitlab_token
from app.utils.gitlab_api import parse_gitlab_payload, fetch_mr_diff
from app.agent.diff_formatter import format_diff_for_review, is_reviewable
from app.agent.reviewer import review_diff
from app.agent.comment_poster import post_gitlab_review
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)
gitlab_bp = Blueprint("gitlab", __name__)


def process_gitlab_event(payload: dict, event: str, gitlab_pat: str):
    """
    Process the GitLab event in a background thread.
    Full pipeline: parse → fetch diff → format → review → post comments.
    """
    try:
        if event == "Merge Request Hook" and payload.get(
            "object_attributes", {}
        ).get("action") in ["open", "update"]:

            parsed = parse_gitlab_payload(payload)

            if not parsed:
                logger.warning("Could not parse GitLab payload — skipping")
                return

            repo = parsed.get("repo")
            mr_iid = parsed.get("pr_number")

            if not repo or not mr_iid:
                logger.warning("Missing repo or MR IID — skipping")
                return

            logger.info(f"Processing MR !{mr_iid} in {repo}")

            diff = fetch_mr_diff(repo, mr_iid, gitlab_pat)

            if not diff:
                logger.warning("No diff found — skipping review")
                return

            reviewable_files = [f for f in diff if is_reviewable(f["filename"])]
            logger.info(f"Reviewing {len(reviewable_files)} of {len(diff)} files")

            if not reviewable_files:
                logger.info("No reviewable files — skipping")
                return

            formatted = format_diff_for_review(reviewable_files, parsed)
            comments = review_diff(formatted, parsed)

            logger.info(f"Claude found {len(comments)} issues")

            success = post_gitlab_review(repo, mr_iid, comments, gitlab_pat, parsed)

            if success:
                logger.info(f"Review posted successfully for MR !{mr_iid}")
            else:
                logger.error(f"Failed to post review for MR !{mr_iid}")

        else:
            logger.info(f"Skipping GitLab event: {event}")

    except Exception as e:
        logger.error(f"Error processing GitLab event: {type(e).__name__}: {e}")


@gitlab_bp.route("/webhook/gitlab", methods=["POST"])
def gitlab_webhook():
    secret = os.getenv("GITLAB_WEBHOOK_TOKEN", "")
    gitlab_pat = os.getenv("GITLAB_PAT", "")
    token_header = request.headers.get("X-Gitlab-Token", "")
    payload_bytes = request.get_data()

    token_header = request.headers.get("X-Gitlab-Token", "")
    
    if not verify_gitlab_token(token_header, secret):
        logger.warning("Rejected request — invalid GitLab token")
        abort(403)

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON payload — ignoring")
        return {"status": "received"}, 200

    event = request.headers.get("X-Gitlab-Event", "unknown")
    logger.info(f"GitLab event received and verified: {event}")

    thread = threading.Thread(
        target=process_gitlab_event,
        args=(payload, event, gitlab_pat)
    )
    thread.daemon = True
    thread.start()

    return {"status": "received"}, 200