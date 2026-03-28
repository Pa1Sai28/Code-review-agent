import logging
import json
import os
import threading
from flask import Blueprint, request, abort
from dotenv import load_dotenv
from app.utils.security import verify_gitlab_token
from app.utils.gitlab_api import parse_gitlab_payload, fetch_mr_diff
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)
gitlab_bp = Blueprint("gitlab", __name__)


def process_gitlab_event(payload: dict, event: str, gitlab_pat: str):
    """
    Process the GitLab event in a background thread.
    This runs AFTER we've already returned 200 to GitLab.
    """
    try:
        if event == "Merge Request Hook" and payload.get("object_attributes", {}).get("action") in ["open", "update"]:
            parsed = parse_gitlab_payload(payload)

            if not parsed:
                logger.warning("Could not parse payload — skipping")
                return

            if parsed.get("pr_number") and parsed.get("repo"):
                logger.info(f"Processing MR !{parsed['pr_number']} in {parsed['repo']}")
                diff = fetch_mr_diff(parsed["repo"], parsed["pr_number"], gitlab_pat)
                logger.info(f"Diff fetched — {len(diff)} files changed")
                for f in diff:
                    logger.info(f"  {f['filename']} +{f['additions']} -{f['deletions']}")
        else:
            logger.info(f"Skipping event: {event}")

    except Exception as e:
        logger.error(f"Error processing GitLab event: {type(e).__name__}: {e}")


@gitlab_bp.route("/webhook/gitlab", methods=["POST"])
def gitlab_webhook():
    secret = os.getenv("GITLAB_WEBHOOK_TOKEN", "")
    gitlab_pat = os.getenv("GITLAB_PAT", "")
    token_header = request.headers.get("X-Gitlab-Token", "")
    payload_bytes = request.get_data()

    if not verify_gitlab_token(token_header, secret):
        logger.warning("Rejected request — invalid GitLab token")
        abort(403)

    payload = json.loads(payload_bytes)
    event = request.headers.get("X-Gitlab-Event", "unknown")

    logger.info(f"GitLab event received and verified: {event}")

    thread = threading.Thread(
        target=process_gitlab_event,
        args=(payload, event, gitlab_pat)
    )
    thread.daemon = True
    thread.start()

    return {"status": "received"}, 200