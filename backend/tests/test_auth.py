"""
Auth blueprint tests -- /api/auth/{login,refresh,me,logout}.

Covers the success path + every failure mode the spec calls out:

  Login flow  (6):
    - success returns access + refresh + user (no password_hash leak)
    - wrong password -> 401 generic
    - unknown email  -> 401 generic (SAME error as wrong password -> no enumeration)
    - OAuth-only user (NULL password_hash) -> 401 generic
    - missing / malformed body -> 400
    - last_login timestamp gets stamped

  Refresh flow (6):
    - valid refresh -> NEW access + NEW refresh (rotation)
    - expired refresh -> 401
    - tampered signature -> 401
    - access token used as refresh -> 401 (type mismatch)
    - missing Authorization header -> 401
    - user deleted between issuance and refresh -> 401

  Me flow (5):
    - valid access -> user dict
    - missing Authorization header -> 401
    - expired access -> 401
    - refresh token used as access -> 401 (type mismatch)
    - response redacts password_hash

  Logout (1):
    - returns success unconditionally

Total: 18 tests. All use the conftest fixtures whose teardown restores
DB state (rule 17). No /api/v1 prefix -- pre-flight relocated public API
to /api/.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from flask import current_app

from app.models.user import User
from app.utils.db import execute
from app.utils.jwt_helpers import (
    ALGORITHM,
    issue_access_token,
    issue_refresh_token,
)
from app.utils.password import hash_password


# ---------------------------------------------------------------- helpers


def _bearer(token: str) -> dict:
    """Build an Authorization header dict for the test client."""
    return {"Authorization": f"Bearer {token}"}


def _decode_data(response) -> dict:
    """Pull `.data` out of the standard success envelope."""
    body = response.get_json()
    assert body is not None, "Response had no JSON body"
    assert body.get("success") is True, f"Expected success=true, got {body!r}"
    return body["data"]


def _make_token_with_exp(
    app, user_id: int, token_type: str, exp_offset: timedelta, jti: str | None = None
) -> str:
    """
    Forge a JWT with an arbitrary exp offset relative to now. Used to
    simulate expired tokens without sleeping for 15 minutes / 7 days.
    """
    with app.app_context():
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + exp_offset).timestamp()),
        }
        if token_type == "access":
            payload["role"] = "user"
        if token_type == "refresh":
            payload["jti"] = jti or "test-jti"
        return pyjwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm=ALGORITHM)


# ===================================================================== LOGIN


def test_login_success_returns_access_refresh_user(client, fresh_user):
    """Happy path: correct credentials -> 200 with access, refresh, user."""
    resp = client.post(
        "/api/auth/login",
        json={"email": fresh_user.email, "password": fresh_user._test_password},
    )
    assert resp.status_code == 200
    data = _decode_data(resp)
    assert "access" in data and isinstance(data["access"], str) and data["access"]
    assert "refresh" in data and isinstance(data["refresh"], str) and data["refresh"]
    assert data["user"]["email"] == fresh_user.email
    assert data["user"]["id"] == fresh_user.id
    # CRITICAL security check: never leak the hash.
    assert "password_hash" not in data["user"]


def test_login_wrong_password_returns_401(client, fresh_user):
    """Correct email + wrong password -> 401 generic 'Invalid credentials'."""
    resp = client.post(
        "/api/auth/login",
        json={"email": fresh_user.email, "password": "definitely-not-the-right-password"},
    )
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["success"] is False
    assert body["error"] == "Invalid credentials"


def test_login_unknown_email_returns_401(client):
    """Unknown email -> 401 with the SAME message as wrong password (no enumeration)."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody-here-9999@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["success"] is False
    # Identical wording -> attacker cannot distinguish "no such user" from
    # "wrong password" by the response.
    assert body["error"] == "Invalid credentials"


def test_login_oauth_only_user_returns_401(app, client):
    """User with NULL password_hash (OAuth-only) -> 401 generic, never accepted."""
    import secrets
    suffix = secrets.token_hex(4)
    with app.app_context():
        user = User.create(
            email=f"oauth-{suffix}@example.com",
            username=f"oauthuser-{suffix}",
            password_hash=None,  # OAuth-only
            role="user",
        )
    try:
        resp = client.post(
            "/api/auth/login",
            json={"email": user.email, "password": "anything"},
        )
        assert resp.status_code == 401
        body = resp.get_json()
        assert body["error"] == "Invalid credentials"
    finally:
        # Manual cleanup -- no fixture for this OAuth-only user (rule 17).
        with app.app_context():
            execute("DELETE FROM users WHERE id = %s", (user.id,))


def test_login_missing_body_returns_400(client):
    """Missing email/password -> 400 with descriptive message."""
    # Empty JSON body.
    resp = client.post("/api/auth/login", json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
    assert "Email and password" in body["error"]

    # Only email, no password.
    resp = client.post("/api/auth/login", json={"email": "x@y.z"})
    assert resp.status_code == 400

    # Only password, no email.
    resp = client.post("/api/auth/login", json={"password": "secret"})
    assert resp.status_code == 400

    # No body at all.
    resp = client.post("/api/auth/login")
    assert resp.status_code == 400


def test_login_updates_last_login_timestamp(app, client, fresh_user):
    """Successful login bumps users.last_login from NULL to a recent timestamp."""
    # Sanity: fresh_user has no last_login yet.
    with app.app_context():
        before = User.get_by_id(fresh_user.id)
        assert before.last_login is None

    resp = client.post(
        "/api/auth/login",
        json={"email": fresh_user.email, "password": fresh_user._test_password},
    )
    assert resp.status_code == 200

    with app.app_context():
        after = User.get_by_id(fresh_user.id)
        assert after.last_login is not None
        # Should be within the last 30 seconds (very generous CI margin).
        # MySQL stores last_login as naive; treat it as UTC.
        last_login = after.last_login
        if last_login.tzinfo is None:
            last_login = last_login.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - last_login
        assert delta.total_seconds() < 30


# =================================================================== REFRESH


def test_refresh_with_valid_refresh_returns_new_access_and_new_refresh(app, client, fresh_user):
    """Valid refresh token -> 200 with NEW access + NEW refresh (rotation)."""
    with app.app_context():
        original_refresh = issue_refresh_token(fresh_user.id)

    resp = client.post("/api/auth/refresh", headers=_bearer(original_refresh))
    assert resp.status_code == 200
    data = _decode_data(resp)
    assert "access" in data and data["access"]
    assert "refresh" in data and data["refresh"]
    # Rotation: new refresh must differ from the original (fresh jti).
    assert data["refresh"] != original_refresh


def test_refresh_with_expired_token_returns_401(app, client, fresh_user):
    """Refresh token whose exp is in the past -> 401."""
    expired = _make_token_with_exp(
        app, fresh_user.id, "refresh", exp_offset=timedelta(days=-1)
    )
    resp = client.post("/api/auth/refresh", headers=_bearer(expired))
    assert resp.status_code == 401


def test_refresh_with_tampered_signature_returns_401(app, client, fresh_user):
    """Tampered token (signature broken) -> 401."""
    with app.app_context():
        valid = issue_refresh_token(fresh_user.id)

    # Flip the last character of the signature segment.
    last = valid[-1]
    swapped = "A" if last != "A" else "B"
    tampered = valid[:-1] + swapped

    resp = client.post("/api/auth/refresh", headers=_bearer(tampered))
    assert resp.status_code == 401


def test_refresh_with_access_token_returns_401(app, client, fresh_user):
    """Access token sent to /refresh -> 401 (type claim mismatch)."""
    with app.app_context():
        access = issue_access_token(fresh_user.id, fresh_user.role)
    resp = client.post("/api/auth/refresh", headers=_bearer(access))
    assert resp.status_code == 401


def test_refresh_without_authorization_header_returns_401(client):
    """No Authorization header at all -> 401."""
    resp = client.post("/api/auth/refresh")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["success"] is False


def test_refresh_user_no_longer_exists_returns_401(app, client):
    """User deleted between issuance and refresh -> 401."""
    import secrets
    suffix = secrets.token_hex(4)
    with app.app_context():
        ghost = User.create(
            email=f"ghost-{suffix}@example.com",
            username=f"ghost-{suffix}",
            password_hash=hash_password("temporary"),
            role="user",
        )
        token = issue_refresh_token(ghost.id)
        # Delete the user immediately -- token is still cryptographically valid.
        execute("DELETE FROM users WHERE id = %s", (ghost.id,))

    resp = client.post("/api/auth/refresh", headers=_bearer(token))
    assert resp.status_code == 401


# ======================================================================= ME


def test_me_with_valid_access_returns_user(app, client, fresh_user):
    """Valid access token -> 200 with the user dict."""
    with app.app_context():
        access = issue_access_token(fresh_user.id, fresh_user.role)
    resp = client.get("/api/auth/me", headers=_bearer(access))
    assert resp.status_code == 200
    data = _decode_data(resp)
    assert data["id"] == fresh_user.id
    assert data["email"] == fresh_user.email
    assert data["username"] == fresh_user.username


def test_me_without_authorization_header_returns_401(client):
    """No Authorization header -> 401 (handled by @jwt_required)."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_expired_access_returns_401(app, client, fresh_user):
    """Expired access token -> 401."""
    expired = _make_token_with_exp(
        app, fresh_user.id, "access", exp_offset=timedelta(minutes=-5)
    )
    resp = client.get("/api/auth/me", headers=_bearer(expired))
    assert resp.status_code == 401


def test_me_with_refresh_token_used_as_access_returns_401(app, client, fresh_user):
    """Refresh token sent to /me -> 401 (type claim mismatch)."""
    with app.app_context():
        refresh = issue_refresh_token(fresh_user.id)
    resp = client.get("/api/auth/me", headers=_bearer(refresh))
    assert resp.status_code == 401


def test_me_redacts_password_hash(app, client, fresh_user):
    """The /me response must NEVER include password_hash."""
    with app.app_context():
        access = issue_access_token(fresh_user.id, fresh_user.role)
    resp = client.get("/api/auth/me", headers=_bearer(access))
    assert resp.status_code == 200
    data = _decode_data(resp)
    assert "password_hash" not in data
    # Sanity-check the entire response body for the substring -- defence in depth.
    raw = resp.get_data(as_text=True)
    assert "password_hash" not in raw


# =================================================================== LOGOUT


def test_logout_returns_success(client):
    """Logout always succeeds (stateless JWT, defensive endpoint)."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    data = _decode_data(resp)
    assert data == {"success": True}
