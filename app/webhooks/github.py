import logging
import json
import os
from flask import Blueprint, request, abort
from dotenv import load_dotenv
from app.utils.security import verify_github_signature
from app.utils.github_api import parse_github_payload, fetch_pr_diff
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)
github_bp = Blueprint("github", __name__)


@github_bp.route("/webhook/github", methods=["POST"])
def github_webhook():
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    github_pat = os.getenv("GITHUB_PAT", "")
    signature = request.headers.get("X-Hub-Signature-256", "")
    payload_bytes = request.get_data()

    if not verify_github_signature(payload_bytes, signature, secret):
        logger.warning("Rejected request — invalid GitHub signature")
        abort(403)

    payload = json.loads(payload_bytes)
    event = request.headers.get("X-GitHub-Event", "unknown")

    logger.info(f"GitHub event verified and received: {event}")

    if event == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        parsed = parse_github_payload(payload)

        if parsed.get("pr_number") and parsed.get("repo"):
            logger.info(f"Fetching diff for PR #{parsed['pr_number']} in {parsed['repo']}")
            diff = fetch_pr_diff(parsed["repo"], parsed["pr_number"], github_pat)
            logger.info(f"Diff fetched — {len(diff)} files changed")

    return {"status": "received"}, 200