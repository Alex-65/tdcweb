"""
Auth endpoints under /api/auth/*.

POST   /api/auth/login    -- email + password -> issue access + refresh + user
POST   /api/auth/refresh  -- Bearer refresh   -> rotated access + refresh
GET    /api/auth/me       -- Bearer access    -> current user
POST   /api/auth/logout   -- always succeeds  -> { success: true }

Tokens carried via cookies on the BFF side (frontend), via Authorization
header on the Flask side. Flask never sees cookies; the Nuxt BFF strips
them and forwards Bearer headers. See spec section 8 (Hybrid BFF).

Response shape: every endpoint goes through `app.utils.responses.success`,
which wraps the payload as { "success": true, "data": <payload> }. The
BFF unwraps `.data` before returning to the client.
"""
from flask import Blueprint, request, g

from app.models.user import User
from app.utils.auth_decorators import jwt_required
from app.utils.jwt_helpers import (
    issue_access_token,
    issue_refresh_token,
    verify_token,
)
from app.utils.password import verify_password
from app.utils.responses import bad_request, success, unauthorized

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate with email + password.

    Request body: { "email": "...", "password": "..." }
    Response 200: { success: true, data: { access, refresh, user } }
    Response 400: missing/malformed body
    Response 401: invalid credentials -- SAME generic message for
                  "no such user" vs "wrong password" vs "OAuth-only user"
                  to prevent enumeration.
    """
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return bad_request("Email and password are required")

    user = User.get_by_email(email)
    if not user or not user.password_hash:
        # No such user OR OAuth-only user (no password set) -> generic 401.
        return unauthorized("Invalid credentials")

    if not verify_password(password, user.password_hash):
        return unauthorized("Invalid credentials")

    user.update_last_login()

    access = issue_access_token(user.id, user.role)
    refresh = issue_refresh_token(user.id)

    return success({
        "access": access,
        "refresh": refresh,
        "user": user.to_dict(),  # password_hash NOT included
    })


@bp.route("/refresh", methods=["POST"])
def refresh():
    """
    Rotate the refresh token. Issues NEW access + NEW refresh.

    Request: Authorization: Bearer <refresh_token>
    Response 200: { success: true, data: { access, refresh } }
    Response 401: missing/invalid/expired refresh token

    Note: rotation invalidates the old refresh token by issuing a new jti.
    Future enhancement (TECH_DEBT): track revoked jtis in user_sessions
    table for proper invalidation. Today: client must use the new refresh
    and discard the old one (no server-side revocation list).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return unauthorized("Missing refresh token")

    token = auth_header[7:].strip()
    payload = verify_token(token, "refresh")
    if not payload:
        return unauthorized("Invalid or expired refresh token")

    user_id = payload["sub"]
    user = User.get_by_id(user_id)
    if not user:
        return unauthorized("User not found")

    new_access = issue_access_token(user.id, user.role)
    new_refresh = issue_refresh_token(user.id)

    return success({
        "access": new_access,
        "refresh": new_refresh,
    })


@bp.route("/me", methods=["GET"])
@jwt_required
def me():
    """
    Return the currently authenticated user.

    Request: Authorization: Bearer <access_token>
    Response 200: { success: true, data: <User dict> }
    Response 401: missing/invalid/expired access token (handled by @jwt_required)

    The BFF (frontend/server/api/auth/me.get.ts) wraps the response as
    `{ user: ... }` for client consumption. This endpoint returns the
    flat User dict inside `data`; let the BFF wrap.
    """
    return success(g.current_user.to_dict())


@bp.route("/logout", methods=["POST"])
def logout():
    """
    Defensive logout. Always succeeds.

    JWT tokens are stateless -- without a server-side revocation list,
    "logout" is just a client-side cookie clear. This endpoint exists so
    the BFF can call it and treat the response uniformly. Future: when
    user_sessions revocation lands (TECH_DEBT), this endpoint will mark
    the session revoked.

    Response 200: { success: true, data: { success: true } }
    """
    return success({"success": True})
