import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


def verify_github_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify that the webhook request genuinely came from GitHub.
    GitHub signs the payload with HMAC-SHA256 using your webhook secret.
    We compute the same signature and compare — if they match, it's real.
    """
    if not signature_header:
        logger.warning("Missing X-Hub-Signature-256 header")
        return False

    if not signature_header.startswith("sha256="):
        logger.warning("Invalid signature format")
        return False

    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(expected_signature, signature_header)

    if not is_valid:
        logger.warning("Signature mismatch — request rejected")

    return is_valid
