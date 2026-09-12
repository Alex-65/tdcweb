"""
Flask request decorators for JWT auth + RBAC.

Usage:

    from app.utils.auth_decorators import jwt_required, staff_required, admin_required

    @bp.route('/me', methods=['GET'])
    @jwt_required
    def me():
        return success(g.current_user.to_dict())

    @bp.route('/admin/users', methods=['GET'])
    @jwt_required
    @admin_required
    def list_users():
        ...

The decorators must be stacked in this order:  @jwt_required ABOVE @{role}_required.
@jwt_required populates `g.current_user`; the role decorators read it.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import g, request

from app.models.user import User
from app.utils.jwt_helpers import verify_token
from app.utils.responses import forbidden, unauthorized

_BEARER_PREFIX = "Bearer "


def jwt_required(f: Callable) -> Callable:
    """
    Require a valid `Authorization: Bearer <access-token>` header.

    On success: sets `g.current_user` (a `User`) and calls the wrapped view.
    On failure: returns 401 with a generic message (no enumeration).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith(_BEARER_PREFIX):
            return unauthorized("Missing bearer token")

        token = auth_header[len(_BEARER_PREFIX):].strip()
        payload = verify_token(token, "access")
        if payload is None:
            return unauthorized("Invalid or expired token")

        user_id = payload.get("sub")
        if not isinstance(user_id, int):
            return unauthorized("Invalid token payload")

        user = User.get_by_id(user_id)
        if user is None:
            # Token was valid but the underlying user no longer exists --
            # treat as auth failure rather than 500.
            return unauthorized("User not found")

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def admin_required(f: Callable) -> Callable:
    """
    Require g.current_user.role == 'admin'. Apply AFTER @jwt_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if user is None or not user.has_role("admin"):
            return forbidden("Admin only")
        return f(*args, **kwargs)

    return decorated


def staff_required(f: Callable) -> Callable:
    """
    Require staff or admin (admin satisfies staff via role hierarchy).
    Apply AFTER @jwt_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if user is None or not user.has_role("staff"):
            return forbidden("Staff only")
        return f(*args, **kwargs)

    return decorated
