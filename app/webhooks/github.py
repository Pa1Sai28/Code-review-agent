import logging
import json
import os
import threading
from flask import Blueprint, request, abort
from dotenv import load_dotenv
from app.utils.security import verify_github_signature
from app.utils.github_api import parse_github_payload, fetch_pr_diff
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)
github_bp = Blueprint("github", __name__)


def process_github_event(payload: dict, event: str, github_pat: str):
    """
    Process the GitHub event in a background thread.
    This runs AFTER we've already returned 200 to GitHub.
    """
    try:
        if event == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
            parsed = parse_github_payload(payload)

            if not parsed:
                logger.warning("Could not parse payload — skipping")
                return

            if parsed.get("pr_number") and parsed.get("repo"):
                logger.info(f"Processing PR #{parsed['pr_number']} in {parsed['repo']}")
                diff = fetch_pr_diff(parsed["repo"], parsed["pr_number"], github_pat)
                logger.info(f"Diff fetched — {len(diff)} files changed")
                for f in diff:
                    logger.info(f"  {f['filename']} +{f['additions']} -{f['deletions']}")
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
        logger.warning("Invalid JSON payload received — ignoring")
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