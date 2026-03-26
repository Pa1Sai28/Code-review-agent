import logging
import json
from flask import Blueprint, request

logger = logging.getLogger(__name__)
github_bp = Blueprint("github", __name__)

@github_bp.route("/webhook/github", methods=["POST"])
def github_webhook():
    payload = request.get_json(silent=True)
    event = request.headers.get("X-GitHub-Event", "unknown")

    logger.info(f"GitHub event received: {event}")
    logger.info(json.dumps(payload, indent=2))

    return {"status": "received"}, 200