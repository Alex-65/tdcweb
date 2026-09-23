"""
Shared pytest fixtures for the TDC backend test suite.

Design notes:
- Tests target the `tdcweb_test` database (TestingConfig.DB_NAME).
- `tdcweb_test` is created out-of-band (Phase 4B.1 setup); this conftest
  only verifies it exists and that its schema looks sane, then uses it.
- mysql-connector-python's pool does not support transactional rollback
  per-test out of the box, so each fixture that mutates state cleans up
  what it created (CLAUDE.md rule 17 "Test state cleanup").
"""
from __future__ import annotations

import os
import secrets

import pytest

# IMPORTANT: tell create_app to load TestingConfig BEFORE importing the app
# package (config classes read env at class-definition time).
os.environ["FLASK_ENV"] = "testing"

from app import create_app  # noqa: E402  -- import after env mutation
from app.config import TestingConfig  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils.db import fetch_one, get_connection  # noqa: E402
from app.utils.password import hash_password  # noqa: E402


# --------------------------------------------------------------------- app


@pytest.fixture(scope="session")
def app():
    """Flask app wired to the test DB. Session-scoped (one boot per pytest run)."""
    flask_app = create_app(TestingConfig)
    # Sanity: verify we are pointed at the test DB, not dev / prod.
    assert flask_app.config["DB_NAME"] == "tdcweb_test", (
        f"Test app must use tdcweb_test, got {flask_app.config['DB_NAME']!r}"
    )
    yield flask_app


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_db_schema(app):
    """
    Verify `tdcweb_test` is reachable and has the expected schema.

    The test DB is provisioned out-of-band (see Task 4B.1 setup). If it is
    missing or empty, fail loudly so the developer knows to run setup --
    don't try to provision from inside the test suite (requires GRANT,
    which the `tdcweb` test user lacks).
    """
    with app.app_context():
        row = fetch_one(
            """
            SELECT COUNT(*) AS table_count
            FROM information_schema.tables
            WHERE table_schema = %s
            """,
            (app.config["DB_NAME"],),
        )
        if row is None or row["table_count"] == 0:
            pytest.exit(
                f"Test database {app.config['DB_NAME']!r} is empty or missing. "
                "Provision it with the Task 4B.1 schema-clone procedure first.",
                returncode=1,
            )
    yield


# --------------------------------------------------------------------- HTTP client


@pytest.fixture
def client(app):
    """A Flask test client for HTTP-level testing."""
    return app.test_client()


# --------------------------------------------------------------------- DB connection


@pytest.fixture
def db(app):
    """
    Yield a request-scoped DB connection within an app context.

    Tests that mutate state are responsible for cleaning up rows they
    inserted (rule 17). The fixture provides the connection but does NOT
    auto-rollback (mysql-connector-python's pooled connections reset
    session state but do not roll back uncommitted writes from prior test
    code that already committed).
    """
    with app.app_context():
        conn = get_connection()
        try:
            yield conn
        finally:
            # Don't .close() here -- close_connection (registered as
            # teardown_appcontext) returns it to the pool when the app
            # context exits.
            pass


# --------------------------------------------------------------------- user fixtures


def _unique_suffix() -> str:
    """8 random hex chars -- collision-resistant within a single pytest run."""
    return secrets.token_hex(4)


def _delete_user(app, user_id: int) -> None:
    """Hard-delete a test user. Runs in its own app context so it's safe to
    call from any teardown, even after the original fixture's context exits.
    """
    with app.app_context():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
        finally:
            cursor.close()


@pytest.fixture
def fresh_user(app):
    """
    Create a non-privileged test user with a known plaintext password.

    Yields:
        User with .id set, password 'testpass123' (hashed in DB).
        The plaintext password is also accessible as user._test_password
        for convenience inside the test.

    Cleanup: hard-deletes the row at teardown (rule 17).
    """
    suffix = _unique_suffix()
    with app.app_context():
        user = User.create(
            email=f"test-{suffix}@example.com",
            username=f"testuser-{suffix}",
            password_hash=hash_password("testpass123"),
            role="user",
        )
    user._test_password = "testpass123"  # type: ignore[attr-defined]
    yield user
    _delete_user(app, user.id)


@pytest.fixture
def staff_user(app):
    """Create a staff-role test user. Cleanup at teardown."""
    suffix = _unique_suffix()
    with app.app_context():
        user = User.create(
            email=f"staff-{suffix}@example.com",
            username=f"staffuser-{suffix}",
            password_hash=hash_password("staffpass123"),
            role="staff",
        )
    user._test_password = "staffpass123"  # type: ignore[attr-defined]
    yield user
    _delete_user(app, user.id)


@pytest.fixture
def admin_user(app):
    """Create an admin-role test user. Cleanup at teardown."""
    suffix = _unique_suffix()
    with app.app_context():
        user = User.create(
            email=f"admin-{suffix}@example.com",
            username=f"adminuser-{suffix}",
            password_hash=hash_password("adminpass123"),
            role="admin",
        )
    user._test_password = "adminpass123"  # type: ignore[attr-defined]
    yield user
    _delete_user(app, user.id)


# --------------------------------------------------------------------- location + event fixtures


def _delete_location(app, location_id: int) -> None:
    """Hard-delete a location and its translations. Safe in any teardown."""
    with app.app_context():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Translations FK to location -- delete children first to avoid
            # FK constraint errors regardless of ON DELETE CASCADE config.
            cursor.execute(
                "DELETE FROM location_translations WHERE location_id = %s",
                (location_id,),
            )
            cursor.execute("DELETE FROM locations WHERE id = %s", (location_id,))
            conn.commit()
        finally:
            cursor.close()


def _delete_event(app, event_id: int) -> None:
    """Hard-delete an event and its translations. Safe in any teardown."""
    with app.app_context():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM event_translations WHERE event_id = %s",
                (event_id,),
            )
            cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            conn.commit()
        finally:
            cursor.close()


@pytest.fixture
def make_location(app):
    """
    Factory for test locations. Returns a callable that creates a location
    row (and optional translations) and registers cleanup.

    Usage:
        loc = make_location(name='Test Cave', mood='cosmic_tech',
                            translations={'en': {'name': 'Test Cave EN',
                                                 'description': 'desc en'},
                                          'it': {'name': 'Grotta Test',
                                                 'description': 'desc it'}})

    Returns the inserted row as a dict (id, slug, name, mood_category, ...).

    Each call uses a fresh suffix so multiple locations in the same test
    do not collide on the unique slug constraint. Cleanup is registered
    on the fixture finalizer; all rows created via the factory are deleted
    at fixture teardown (rule 17).
    """
    created_ids: list[int] = []

    def _factory(
        name: str = "Test Location",
        mood: str = "cosmic_tech",
        slug: str | None = None,
        is_active: bool = True,
        sort_order: int = 0,
        capacity: int = 100,
        hero_image_url: str | None = None,
        translations: dict | None = None,
    ) -> dict:
        suffix = _unique_suffix()
        actual_slug = slug or f"test-loc-{suffix}"
        with app.app_context():
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO locations
                        (slug, name, capacity, sort_order, is_active,
                         mood_category, hero_image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        actual_slug,
                        name,
                        capacity,
                        sort_order,
                        1 if is_active else 0,
                        mood,
                        hero_image_url,
                    ),
                )
                location_id = cursor.lastrowid
                if translations:
                    for lang, fields in translations.items():
                        cursor.execute(
                            """
                            INSERT INTO location_translations
                                (location_id, language, name, tagline,
                                 description, architecture_notes, atmosphere_notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                location_id,
                                lang,
                                fields.get("name"),
                                fields.get("tagline"),
                                fields.get("description"),
                                fields.get("architecture_notes"),
                                fields.get("atmosphere_notes"),
                            ),
                        )
                conn.commit()
            finally:
                cursor.close()
        created_ids.append(location_id)
        return {
            "id": location_id,
            "slug": actual_slug,
            "name": name,
            "mood_category": mood,
            "is_active": is_active,
            "sort_order": sort_order,
            "capacity": capacity,
        }

    yield _factory

    # Cleanup all locations created during the test (rule 17).
    for loc_id in created_ids:
        _delete_location(app, loc_id)


@pytest.fixture
def sample_location(make_location):
    """Convenience: a single ready-to-use active location with EN+IT translations."""
    return make_location(
        name="Sample Cave",
        mood="cosmic_tech",
        translations={
            "en": {"name": "Sample Cave EN", "description": "English description"},
            "it": {"name": "Grotta di Esempio", "description": "Descrizione italiana"},
        },
    )


@pytest.fixture
def make_event(app, make_location):
    """
    Factory for test events. Creates an event row + translations and
    registers cleanup.

    Usage:
        ev = make_event(
            location_id=42,                    # if None, a sample location is created
            start_offset_seconds=3600,         # +1h from now (default +86400 = 1 day)
            duration_seconds=7200,             # 2h (default 7200)
            translations={'en': {'title': 'Concert', 'description': 'desc'}},
            is_published=True,
            slug=None,                         # auto if None
        )

    Returns dict with id, slug, location_id, start_time, end_time,
    is_published, plus _location_id if a location was auto-created.
    """
    from datetime import datetime, timedelta

    created_ids: list[int] = []

    def _factory(
        location_id: int | None = None,
        start_offset_seconds: int = 86400,  # +1 day
        duration_seconds: int = 7200,  # 2h
        translations: dict | None = None,
        is_published: bool = True,
        slug: str | None = None,
        event_type: str = "live_singer",
    ) -> dict:
        # Auto-create a location if none given
        if location_id is None:
            loc = make_location(
                name="Auto Loc",
                translations={"en": {"name": "Auto Loc EN"}},
            )
            location_id = loc["id"]

        suffix = _unique_suffix()
        actual_slug = slug or f"test-ev-{suffix}"
        now = datetime.now().replace(microsecond=0)
        start = now + timedelta(seconds=start_offset_seconds)
        end = start + timedelta(seconds=duration_seconds)

        # Default translation must exist (events need at least 'en' for title)
        if translations is None:
            translations = {"en": {"title": "Test Event"}}

        with app.app_context():
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO events
                        (slug, event_type, location_id, start_time, end_time,
                         is_published)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        actual_slug,
                        event_type,
                        location_id,
                        start,
                        end,
                        1 if is_published else 0,
                    ),
                )
                event_id = cursor.lastrowid
                for lang, fields in translations.items():
                    cursor.execute(
                        """
                        INSERT INTO event_translations
                            (event_id, language, title, description)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            event_id,
                            lang,
                            fields.get("title", "Test Event"),
                            fields.get("description"),
                        ),
                    )
                conn.commit()
            finally:
                cursor.close()
        created_ids.append(event_id)
        return {
            "id": event_id,
            "slug": actual_slug,
            "location_id": location_id,
            "start_time": start,
            "end_time": end,
            "is_published": is_published,
        }

    yield _factory

    for ev_id in created_ids:
        _delete_event(app, ev_id)


@pytest.fixture
def sample_event(make_event):
    """Convenience: a single ready-to-use upcoming published event with EN translation."""
    return make_event(
        translations={
            "en": {"title": "Sample Concert EN", "description": "EN desc"},
            "it": {"title": "Concerto di Esempio", "description": "Descrizione IT"},
        },
    )
