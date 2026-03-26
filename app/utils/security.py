import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

# We use hmac.compare_digest() instead of == to compare the two signatures. Why? Because == stops comparing the moment 
# it finds a difference  — a timing attack can exploit that tiny difference in response time to guess your secret character 
# by character. compare_digest always takes the same amount of time regardless of where the mismatch is.

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
        logger.warning("Invalid signature format — expected sha256= prefix")
        return False

    expected_signature = "sha256=" + hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    is_valid = hmac.compare_digest(expected_signature, signature_header)

    if not is_valid:
        logger.warning("Signature mismatch — request rejected")

    return is_valid