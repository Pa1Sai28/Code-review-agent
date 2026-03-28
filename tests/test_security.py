import hmac
import hashlib
import pytest
from app.utils.security import verify_github_signature

SECRET = "test_secret_key"

def make_signature(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

def test_valid_signature_passes():
    payload = b'{"action": "opened"}'
    sig = make_signature(payload, SECRET)
    assert verify_github_signature(payload, sig, SECRET) is True

def test_tampered_payload_fails():
    payload = b'{"action": "opened"}'
    sig = make_signature(payload, SECRET)
    tampered = b'{"action": "closed"}'
    assert verify_github_signature(tampered, sig, SECRET) is False

def test_wrong_secret_fails():
    payload = b'{"action": "opened"}'
    sig = make_signature(payload, "wrong_secret")
    assert verify_github_signature(payload, sig, SECRET) is False

def test_missing_signature_fails():
    payload = b'{"action": "opened"}'
    assert verify_github_signature(payload, "", SECRET) is False

def test_invalid_format_fails():
    payload = b'{"action": "opened"}'
    assert verify_github_signature(payload, "invalidsignature", SECRET) is False
    
from app.utils.security import verify_gitlab_token

def test_valid_gitlab_token_passes():
    assert verify_gitlab_token("mysecrettoken", "mysecrettoken") is True

def test_invalid_gitlab_token_fails():
    assert verify_gitlab_token("wrongtoken", "mysecrettoken") is False

def test_missing_gitlab_token_fails():
    assert verify_gitlab_token("", "mysecrettoken") is False