import logging
import json
import os
import threading
from flask import Blueprint, request, abort
from dotenv import load_dotenv
from app.utils.security import verify_github_signature
from app.utils.github_api import parse_github_payload, fetch_pr_diff
from app.agent.diff_formatter import format_diff_for_review, is_reviewable
from app.agent.reviewer import review_diff
from app.agent.comment_poster import post_github_review
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)
github_bp = Blueprint("github", __name__)


def process_github_event(payload: dict, event: str, github_pat: str):
    """
    Process the GitHub event in a background thread.
    Full pipeline: parse → fetch diff → format → review → post comments.
    """
    try:
        if event == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
            parsed = parse_github_payload(payload)

            if not parsed:
                logger.warning("Could not parse payload — skipping")
                return

            repo = parsed.get("repo")
            pr_number = parsed.get("pr_number")

            if not repo or not pr_number:
                logger.warning("Missing repo or PR number — skipping")
                return

            logger.info(f"Processing PR #{pr_number} in {repo}")

            diff = fetch_pr_diff(repo, pr_number, github_pat)

            if not diff:
                logger.warning("No diff found — skipping review")
                return

            reviewable_files = [f for f in diff if is_reviewable(f["filename"])]
            logger.info(f"Reviewing {len(reviewable_files)} of {len(diff)} files")

            if not reviewable_files:
                logger.info("No reviewable files found — skipping")
                return

            formatted = format_diff_for_review(reviewable_files, parsed)
            comments = review_diff(formatted, parsed)

            logger.info(f"Claude found {len(comments)} issues")

            success = post_github_review(repo, pr_number, comments, github_pat, parsed)

            if success:
                logger.info(f"Review posted successfully for PR #{pr_number}")
            else:
                logger.error(f"Failed to post review for PR #{pr_number}")

        else:
            logger.info(f"Skipping event: {event} action={payload.get('action', 'n/a')}")

    except Exception as e:
        logger.error(f"Error processing GitHub event: {type(e).__name__}: {e}")


@github_bp.route("/webhook/github", methods=["POST"])
def github_webhook():
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    github_pat = os.getenv("GITHUB_PAT", "")
    signature = request.headers.get("X-Hub-Signature-256", "")
    payload_bytes = request.get_data()

    if not verify_github_signature(payload_bytes, signature, secret):
        logger.warning("Rejected request — invalid GitHub signature")
        abort(403)

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON payload — ignoring")
        return {"status": "received"}, 200

    event = request.headers.get("X-GitHub-Event", "unknown")
    logger.info(f"GitHub event received and verified: {event}")

    thread = threading.Thread(
        target=process_github_event,
        args=(payload, event, github_pat)
    )
    thread.daemon = True
    thread.start()

    return {"status": "received"}, 200