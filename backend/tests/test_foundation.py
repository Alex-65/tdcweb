"""
Smoke test for Phase 4B.1 backend foundation + Phase 4 holistic-review guard.

Verifies:
  - Password hash + verify round-trip and salting
  - JWT access-token round-trip
  - JWT type-claim is enforced
  - User model create + fetch with fixture cleanup
  - Role hierarchy (admin >= staff >= user)
  - ProductionConfig refuses to inherit dev secret placeholders (rule 16
    HIGH finding from Phase 4 holistic review)

If all pass, the foundation is ready and prod cannot boot with the public
dev secrets.
"""
from __future__ import annotations

import importlib
import os

import pytest

from app.models.user import User
from app.utils.jwt_helpers import issue_access_token, issue_refresh_token, verify_token
from app.utils.password import hash_password, verify_password


def test_password_hash_verify_roundtrip(app):
    """Hash + verify works; bcrypt produces fresh salt each call."""
    h = hash_password("foo")
    assert verify_password("foo", h)
    assert not verify_password("bar", h)

    # Sanity: bcrypt salts are random, so two hashes of the same input differ.
    h2 = hash_password("foo")
    assert h != h2
    assert verify_password("foo", h2)


def test_jwt_access_token_roundtrip(app):
    """issue + verify yields the original claims."""
    with app.app_context():
        token = issue_access_token(user_id=1, role="user")
        payload = verify_token(token, "access")

    assert payload is not None
    assert payload["sub"] == 1
    assert payload["role"] == "user"
    assert payload["type"] == "access"
    assert "iat" in payload and "exp" in payload


def test_jwt_refresh_token_distinguished_from_access(app):
    """Verifying an access token as a refresh token must fail (None)."""
    with app.app_context():
        access = issue_access_token(user_id=1, role="user")
        refresh = issue_refresh_token(user_id=1)

        # Cross-type verification: each must reject the other.
        assert verify_token(access, "refresh") is None
        assert verify_token(refresh, "access") is None

        # Sanity: same-type verification still passes.
        assert verify_token(access, "access") is not None
        assert verify_token(refresh, "refresh") is not None


def test_user_model_create_and_fetch(fresh_user, app):
    """Fixture user is reachable via get_by_id / get_by_email / get_by_username."""
    with app.app_context():
        assert fresh_user.id is not None

        by_id = User.get_by_id(fresh_user.id)
        assert by_id is not None
        assert by_id.email == fresh_user.email
        assert by_id.username == fresh_user.username
        assert by_id.role == "user"

        by_email = User.get_by_email(fresh_user.email)
        assert by_email is not None and by_email.id == fresh_user.id

        by_username = User.get_by_username(fresh_user.username)
        assert by_username is not None and by_username.id == fresh_user.id

        # to_dict() default must NOT leak the hash.
        d = fresh_user.to_dict()
        assert "password_hash" not in d
        d_sensitive = fresh_user.to_dict(include_sensitive=True)
        assert "password_hash" in d_sensitive


def test_user_role_hierarchy(admin_user, staff_user, fresh_user):
    """admin >= staff >= user; reverse is False; unknown role is False."""
    # admin satisfies everything below it.
    assert admin_user.has_role("admin")
    assert admin_user.has_role("staff")
    assert admin_user.has_role("user")

    # staff satisfies staff + user but NOT admin.
    assert staff_user.has_role("staff")
    assert staff_user.has_role("user")
    assert not staff_user.has_role("admin")

    # user only satisfies user.
    assert fresh_user.has_role("user")
    assert not fresh_user.has_role("staff")
    assert not fresh_user.has_role("admin")

    # Unknown role -> False (no crash).
    assert not admin_user.has_role("superadmin")


def test_production_config_rejects_missing_secrets(monkeypatch):
    """ProductionConfig MUST raise KeyError if SECRET_KEY or JWT_SECRET_KEY
    are not set in the environment, so a fresh prod boot cannot silently
    inherit the dev placeholder strings (which are public in the repo).

    Phase 4 holistic-review HIGH finding: the base Config provides dev
    fallbacks like 'jwt-secret-key-change-in-production'. Anyone reading the
    repo knew the value; a prod deploy that forgot the env var would have
    issued admin JWTs signed with that string. ProductionConfig now overrides
    with `os.environ['...']` (no default) so the misconfig fails at class
    instantiation rather than silently downgrading security.

    Test mechanics: app.config calls `load_dotenv()` at module-eval, which
    re-populates env vars from backend/.env on every reload. To exercise
    the "no env, no fallback" path we (a) clear the secrets from os.environ
    and (b) patch load_dotenv to a no-op so the reload doesn't undo our
    deletion. After the reload, the ProductionConfig class body evaluates
    `os.environ['SECRET_KEY']` with no key set and raises KeyError, which
    is the misconfig-fails-loud guarantee we want.
    """
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    # Stop dotenv from re-reading the .env file during the reload.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: False)

    import app.config as _config

    with pytest.raises(KeyError):
        importlib.reload(_config)

    # Restore module state for downstream tests: re-set placeholders so the
    # reload succeeds and other tests using the imported Config see the
    # expected values.
    monkeypatch.setenv("SECRET_KEY", "dev-secret-key-change-in-production")
    monkeypatch.setenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    monkeypatch.undo()  # restore real load_dotenv for any later importer
    importlib.reload(_config)
