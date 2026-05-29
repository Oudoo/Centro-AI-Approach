"""
Aura (by Centro) — Auth helpers: resolve the RBAC UserContext from a token and
verify the HMAC signature on Action Card confirmations.

The dev fallback decodes an unsigned context so the stack runs locally without a
full identity provider; in production set JWT_SECRET and issue signed tokens.
"""
from __future__ import annotations

import hashlib
import hmac

from jose import JWTError, jwt

from config import get_settings
from models import UserContext


def resolve_user(token: str | None) -> UserContext:
    """Decode a JWT into a UserContext. Falls back to a global dev user."""
    settings = get_settings()
    if not token:
        return UserContext(user_id="dev-user")
    try:
        claims = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return UserContext(
            user_id=claims.get("sub", "unknown"),
            display_name=claims.get("name", "Centro User"),
            department=claims.get("department", "general"),
            account_scope=claims.get("account_scope", "global"),
            role=claims.get("role", "agent"),
        )
    except JWTError:
        # Invalid token -> least-privileged context, never elevated.
        return UserContext(user_id="anonymous", account_scope="global", role="agent")


def mint_token(
    user_id: str,
    role: str = "agent",
    account_scope: str = "global",
    department: str = "general",
    name: str | None = None,
) -> str:
    """Issue a signed JWT carrying RBAC claims. Used by the dev login helper."""
    settings = get_settings()
    claims = {
        "sub": user_id,
        "name": name or user_id,
        "role": role,
        "account_scope": account_scope,
        "department": department,
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_action_signature(session_id: str, action_id: str, signature: str | None) -> bool:
    """
    Validate the HMAC signature on a confirmed Action Card. In dev (no signature
    configured) we accept the confirmation flag alone; in production require it.
    """
    settings = get_settings()
    expected = hmac.new(
        settings.jwt_secret.encode(),
        f"{session_id}|{action_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if signature is None:
        return settings.app_env != "production"
    return hmac.compare_digest(expected, signature)
