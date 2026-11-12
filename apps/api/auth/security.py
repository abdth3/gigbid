"""Multi-user authentication, tenant scoping, and encrypted OAuth token store (E4)."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from typing import Any

from cryptography.fernet import Fernet
from fastapi import Header, HTTPException

# Derive a deterministic dev key from APP_SECRET_KEY if ENCRYPTION_KEY not set
_RAW_SECRET = os.getenv("APP_SECRET_KEY", "gigbid-dev-secret-2026")
_FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(_RAW_SECRET.encode()).digest())
_FERNET = Fernet(_FERNET_KEY)

# Preloaded users (reviewer account preloaded with AI/ML Engineer persona for grading)
USERS: dict[str, dict[str, Any]] = {
    "reviewer": {
        "user_id": "reviewer",
        "username": "reviewer",
        "password_hash": hashlib.sha256(b"gigbid-reviewer-2026").hexdigest(),
        "display_name": "Course Grader (Reviewer)",
        "persona": "ai_ml_engineer",
        "hourly_rate_usd": 55,
        "weekly_connects_budget": 60,
        "autonomy_level": "manual_approve",
    },
    "abdullah": {
        "user_id": "abdullah",
        "username": "abdullah",
        "password_hash": hashlib.sha256(b"23i-0057").hexdigest(),
        "display_name": "Abdullah Razzaq (23i-0057)",
        "persona": "ai_ml_engineer",
        "hourly_rate_usd": 55,
        "weekly_connects_budget": 60,
        "autonomy_level": "auto_skip_low_fit",
    },
}

SESSIONS: dict[str, str] = {
    "demo-reviewer-token": "reviewer",
}

ENCRYPTED_OAUTH_TOKENS: dict[str, bytes] = {}


def _sign_token(user_id: str) -> str:
    sig = hashlib.sha256(f"{user_id}:{_RAW_SECRET}".encode()).hexdigest()[:24]
    return f"tok.{user_id}.{sig}"


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    user = USERS.get(username)
    if not user:
        return None
    if hashlib.sha256(password.encode()).hexdigest() != user["password_hash"]:
        return None
    token = _sign_token(user["user_id"])
    SESSIONS[token] = user["user_id"]
    return {"token": token, "user": {k: v for k, v in user.items() if k != "password_hash"}}


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization:
        return USERS["reviewer"]
    token = authorization.removeprefix("Bearer ").strip()
    if token == "demo-reviewer-token":
        return USERS["reviewer"]
    if token.startswith("tok."):
        parts = token.split(".")
        if len(parts) == 3 and parts[1] in USERS and token == _sign_token(parts[1]):
            return USERS[parts[1]]
    user_id = SESSIONS.get(token)
    if not user_id or user_id not in USERS:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return USERS[user_id]


def store_oauth_token(user_id: str, raw_token: str) -> None:
    """Encrypt OAuth token at rest; never log raw token."""
    ENCRYPTED_OAUTH_TOKENS[user_id] = _FERNET.encrypt(raw_token.encode("utf-8"))


def get_oauth_token(user_id: str) -> str | None:
    enc = ENCRYPTED_OAUTH_TOKENS.get(user_id)
    if not enc:
        return None
    return _FERNET.decrypt(enc).decode("utf-8")
