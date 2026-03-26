import logging
import json
import os
from flask import Blueprint, request, abort
from dotenv import load_dotenv
from app.utils.security import verify_github_signature

load_dotenv()
logger = logging.getLogger(__name__)
github_bp = Blueprint("github", __name__)

@github_bp.route("/webhook/github", methods=["POST"])
def github_webhook():
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Hub-Signature-256", "")
    payload_bytes = request.get_data()

    if not verify_github_signature(payload_bytes, signature, secret):
        logger.warning("Rejected request — invalid GitHub signature")
        abort(403)

    payload = json.loads(payload_bytes)
    event = request.headers.get("X-GitHub-Event", "unknown")

    logger.info(f"GitHub event verified and received: {event}")
    logger.info(json.dumps(payload, indent=2))

    return {"status": "received"}, 200