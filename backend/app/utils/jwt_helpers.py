"""
JWT issue + verify helpers. PyJWT, HS256, signed with app.config['JWT_SECRET_KEY'].

Tokens shape (minimal, deliberately):
  Access:  { sub: <user_id>, role: <role>, type: 'access',  iat, exp }
  Refresh: { sub: <user_id>,                type: 'refresh', iat, exp, jti: <uuid4> }

Phase 4B.2 will use the refresh `jti` claim for rotation + revocation
(via the existing `user_sessions` table). 4B.1 only issues + verifies.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import jwt
from flask import current_app

ALGORITHM: str = "HS256"
ACCESS_TTL: timedelta = timedelta(minutes=15)
REFRESH_TTL: timedelta = timedelta(days=7)

TokenType = Literal["access", "refresh"]


def _secret() -> str:
    """Pull the signing secret from the live Flask app config (NOT module-level)."""
    secret = current_app.config.get("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY missing from Flask config. "
            "Set it via .env or the active config class."
        )
    return secret


def _now() -> datetime:
    """Timezone-aware UTC now -- PyJWT requires aware datetimes for iat/exp."""
    return datetime.now(timezone.utc)


def issue_access_token(user_id: int, role: str) -> str:
    """
    Sign and return a short-lived (15 min) access token.

    The role is embedded for cheap RBAC checks at request time without
    re-querying the DB. Beware: a user demoted via the admin UI keeps the
    old role until their token expires (max 15 min).

    Note: `sub` is encoded as a string (PyJWT >= 2.10 enforces RFC 7519
    "Subject MUST be a StringOrURI"). `verify_token` parses it back to int.
    """
    now = _now()
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + ACCESS_TTL).timestamp()),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def issue_refresh_token(user_id: int) -> str:
    """
    Sign and return a long-lived (7 day) refresh token.

    The `jti` (JWT ID) claim is a fresh uuid4 -- 4B.2 records it in
    `user_sessions` and rotates it on every /refresh call so a leaked
    refresh token is single-use.
    """
    now = _now()
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + REFRESH_TTL).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def verify_token(token: str, expected_type: TokenType) -> Optional[dict]:
    """
    Decode + verify `token`. Returns the payload dict on success, None on any failure.

    On success the returned dict has `sub` coerced back to `int` for
    convenience -- callers can index Users without re-parsing.

    NEVER raises -- callers handle None.

    Failure modes that all collapse to None:
      - bad signature
      - expired
      - malformed
      - missing claim
      - `type` claim mismatches `expected_type`
      - `sub` is not a string of digits
    """
    if not token or not isinstance(token, str):
        return None
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except (jwt.InvalidTokenError, jwt.DecodeError, jwt.ExpiredSignatureError):
        return None
    except Exception:
        # Defensive: any other unexpected library error is treated as auth failure.
        return None

    if payload.get("type") != expected_type:
        return None

    # PyJWT gives `sub` back as the string we encoded. Coerce to int so
    # auth_decorators.py and downstream callers can use it directly.
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.isdigit():
        return None
    payload["sub"] = int(sub)

    return payload
