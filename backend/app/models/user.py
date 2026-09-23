"""
User model -- thin wrapper around the `users` table.

Uses app.utils.db (mysql-connector-python pool) for all queries.
NO SQLAlchemy (per CLAUDE.md hard rule).

Schema (verified 2026-04-25):
    id INT PK AUTO_INCREMENT
    email VARCHAR(255) UNIQUE NOT NULL
    username VARCHAR(100) UNIQUE NOT NULL
    password_hash VARCHAR(255) NULL          -- NULL = OAuth-only account
    avatar_name VARCHAR(255) NULL
    role ENUM('user','staff','admin') DEFAULT 'user'
    language VARCHAR(10) DEFAULT 'en'
    country_code CHAR(2) NULL
    detected_language VARCHAR(10) NULL
    email_verified TINYINT(1) DEFAULT 0
    email_notifications TINYINT(1) DEFAULT 1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    last_login TIMESTAMP NULL
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.utils.db import execute, fetch_one


# Role hierarchy: higher number = strictly more privileges.
# `has_role(target)` returns True iff this user's level >= target's level.
_ROLE_LEVEL: dict[str, int] = {
    "user": 1,
    "staff": 2,
    "admin": 3,
}


class User:
    """Domain object for a row in the `users` table."""

    # ----- Construction --------------------------------------------------

    def __init__(self, row: dict) -> None:
        """Populate fields from a dict row returned by mysql-connector (dictionary cursor)."""
        self.id: int = row["id"]
        self.email: str = row["email"]
        self.username: str = row["username"]
        self.password_hash: Optional[str] = row.get("password_hash")
        self.avatar_name: Optional[str] = row.get("avatar_name")
        self.role: str = row.get("role") or "user"
        self.language: str = row.get("language") or "en"
        self.country_code: Optional[str] = row.get("country_code")
        self.detected_language: Optional[str] = row.get("detected_language")
        self.email_verified: bool = bool(row.get("email_verified") or 0)
        self.email_notifications: bool = bool(
            1 if row.get("email_notifications") is None else row["email_notifications"]
        )
        self.created_at: Optional[datetime] = row.get("created_at")
        self.updated_at: Optional[datetime] = row.get("updated_at")
        self.last_login: Optional[datetime] = row.get("last_login")

    # ----- Read --------------------------------------------------------

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional["User"]:
        """Return the user with this id, or None."""
        row = fetch_one(
            "SELECT * FROM users WHERE id = %s",
            (user_id,),
        )
        return cls(row) if row else None

    @classmethod
    def get_by_email(cls, email: str) -> Optional["User"]:
        """Return the user with this email (case-insensitive in MySQL utf8mb4_unicode_ci), or None."""
        row = fetch_one(
            "SELECT * FROM users WHERE email = %s",
            (email,),
        )
        return cls(row) if row else None

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """Return the user with this username, or None."""
        row = fetch_one(
            "SELECT * FROM users WHERE username = %s",
            (username,),
        )
        return cls(row) if row else None

    # ----- Write -------------------------------------------------------

    @classmethod
    def create(
        cls,
        email: str,
        username: str,
        password_hash: Optional[str],
        role: str = "user",
        language: str = "en",
    ) -> "User":
        """
        Insert a new user and return the materialised User instance.

        password_hash may be None for OAuth-only accounts (the schema permits NULL).
        Raises mysql.connector.IntegrityError on duplicate email/username.
        """
        if role not in _ROLE_LEVEL:
            raise ValueError(f"Invalid role: {role!r}. Must be one of {list(_ROLE_LEVEL)}.")

        new_id = execute(
            """
            INSERT INTO users (email, username, password_hash, role, language)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (email, username, password_hash, role, language),
        )
        # Re-fetch so timestamps and defaults populated server-side are visible.
        created = cls.get_by_id(new_id)
        if created is None:  # pragma: no cover -- DB invariant violated
            raise RuntimeError(f"User {new_id} disappeared immediately after INSERT")
        return created

    def update_last_login(self) -> None:
        """Stamp last_login = NOW() for this user."""
        execute(
            "UPDATE users SET last_login = NOW() WHERE id = %s",
            (self.id,),
        )
        # Reflect change locally without an extra SELECT. Tz-aware UTC
        # (consistent with jwt_helpers.py; datetime.utcnow() deprecated in
        # Python 3.12+).
        self.last_login = datetime.now(timezone.utc)

    # ----- Authorisation -----------------------------------------------

    def has_role(self, role: str) -> bool:
        """
        True iff this user's role is at least `role` in the hierarchy
        user(1) < staff(2) < admin(3). Unknown roles return False.
        """
        target_level = _ROLE_LEVEL.get(role)
        if target_level is None:
            return False
        own_level = _ROLE_LEVEL.get(self.role, 0)
        return own_level >= target_level

    # ----- Serialisation -----------------------------------------------

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Return a JSON-serialisable dict.

        include_sensitive=False (default) -- safe for API responses; password_hash excluded.
        include_sensitive=True            -- includes password_hash; use only for internal verify.
        """
        payload: dict = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "avatar_name": self.avatar_name,
            "role": self.role,
            "language": self.language,
            "country_code": self.country_code,
            "detected_language": self.detected_language,
            "email_verified": self.email_verified,
            "email_notifications": self.email_notifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_sensitive:
            payload["password_hash"] = self.password_hash
        return payload

    # ----- Repr --------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover -- debugging aid
        return f"<User id={self.id} username={self.username!r} role={self.role!r}>"
