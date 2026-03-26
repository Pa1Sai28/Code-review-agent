import logging
import json
from flask import Blueprint, request

logger = logging.getLogger(__name__)
gitlab_bp = Blueprint("gitlab", __name__)

@gitlab_bp.route("/webhook/gitlab", methods=["POST"])
def gitlab_webhook():
    payload = request.get_json(silent=True)
    event = request.headers.get("X-Gitlab-Event", "unknown")

    logger.info(f"GitLab event received: {event}")
    logger.info(json.dumps(payload, indent=2))

    return {"status": "received"}, 200