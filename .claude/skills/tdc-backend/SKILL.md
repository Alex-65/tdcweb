---
name: tdc-backend
description: Create Flask backend code for The Dreamer's Cave. Use for routes, models, services, utils, and Celery tasks.
---

# TDC Backend Developer

Expert agent for creating Flask backend code for The Dreamer's Cave virtual music club website.

## Trigger

Use this skill when:
- User asks to create or modify backend code
- User says "/backend", "/tdc-backend", "/flask", or "/api"
- User asks to create API endpoints, models, or services
- User wants to implement authentication, integrations, or async tasks

## Project Context

**The Dreamer's Cave** - Website for a virtual music club in Second Life.

### Tech Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Python 3.11+ / Flask | RESTful API |
| Database | MySQL 8.x | mysql-connector-python (NO SQLAlchemy) |
| Auth | Flask-Login + JWT | Session for web, JWT for API |
| OAuth | Authlib | Google, Discord, Facebook |
| Task Queue | Celery + Redis | Async tasks |
| Email | SMTP | iRedMail server |

### File Structure

```
backend/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration classes
│   ├── extensions.py         # Flask extensions init
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py           # User, OAuthAccount, PasswordResetToken
│   │   ├── location.py       # Location, LocationTranslation
│   │   ├── artist.py         # Artist, ArtistTranslation
│   │   ├── event.py          # Event, EventTranslation, EventArtist
│   │   ├── blog.py           # BlogPost, BlogPostTranslation, Category
│   │   ├── media.py          # Media
│   │   ├── patreon.py        # PatreonTier, PatreonSupporter, ExclusiveContent
│   │   └── notification.py   # NotificationQueue, UserNotificationPreferences
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py           # /api/v1/auth/*
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── locations.py  # /api/v1/locations/*
│   │   │   ├── artists.py    # /api/v1/artists/*
│   │   │   ├── events.py     # /api/v1/events/*
│   │   │   ├── blog.py       # /api/v1/blog/*
│   │   │   ├── staff.py      # /api/v1/staff/*
│   │   │   ├── support.py    # /api/v1/support/*
│   │   │   ├── sl.py         # /api/v1/sl/* (Second Life)
│   │   │   ├── user.py       # /api/v1/user/* (protected)
│   │   │   └── i18n.py       # /api/v1/i18n/*
│   │   └── admin/
│   │       ├── __init__.py
│   │       ├── dashboard.py
│   │       ├── locations.py
│   │       ├── artists.py
│   │       ├── events.py
│   │       ├── blog.py
│   │       ├── media.py
│   │       ├── users.py
│   │       ├── patreon.py
│   │       └── integrations.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication logic
│   │   ├── email.py          # SMTP email sending
│   │   ├── google_calendar.py
│   │   ├── facebook.py
│   │   ├── patreon.py
│   │   └── media.py          # File upload/processing
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db.py             # MySQL connection pool & helpers
│   │   ├── decorators.py     # @require_auth, @require_admin, etc.
│   │   ├── validators.py     # Input validation
│   │   ├── helpers.py        # Misc utilities
│   │   └── responses.py      # Standard API response helpers
│   │
│   └── tasks/
│       ├── __init__.py       # Celery app
│       ├── notifications.py  # Email queue processing
│       └── sync.py           # Integration sync tasks
│
├── migrations/
├── tests/
├── requirements.txt
├── wsgi.py
└── .env.example
```

## Instructions

### Phase 1: Database Utilities (utils/db.py)

Always use connection pooling and parameterized queries:

```python
"""
Database utilities for mysql-connector-python.
Provides connection pooling and query helpers.
"""
import mysql.connector
from mysql.connector import pooling
from flask import current_app, g
from contextlib import contextmanager


# Connection pool (initialized once)
_pool = None


def init_pool(app):
    """Initialize the connection pool. Call from app factory."""
    global _pool
    _pool = pooling.MySQLConnectionPool(
        pool_name="tdc_pool",
        pool_size=10,
        pool_reset_session=True,
        host=app.config['DB_HOST'],
        port=app.config['DB_PORT'],
        database=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci',
        autocommit=False
    )


def get_connection():
    """Get a connection from the pool."""
    if 'db_conn' not in g:
        g.db_conn = _pool.get_connection()
    return g.db_conn


def close_connection(e=None):
    """Return connection to pool. Register with app.teardown_appcontext."""
    conn = g.pop('db_conn', None)
    if conn is not None:
        conn.close()


@contextmanager
def get_cursor(dictionary=True, buffered=True):
    """
    Context manager for database cursor.

    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary, buffered=buffered)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def fetch_one(query: str, params: tuple = None, dictionary: bool = True):
    """
    Execute query and return single row.

    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters (NEVER use string formatting)
        dictionary: Return dict (True) or tuple (False)

    Returns:
        dict or tuple, or None if no results
    """
    with get_cursor(dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def fetch_all(query: str, params: tuple = None, dictionary: bool = True):
    """
    Execute query and return all rows.

    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters
        dictionary: Return list of dicts (True) or tuples (False)

    Returns:
        list of dict or tuple
    """
    with get_cursor(dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def execute(query: str, params: tuple = None) -> int:
    """
    Execute INSERT/UPDATE/DELETE and return affected rows or last insert ID.

    Returns:
        For INSERT: lastrowid
        For UPDATE/DELETE: rowcount
    """
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        if query.strip().upper().startswith('INSERT'):
            return cursor.lastrowid
        return cursor.rowcount


def execute_many(query: str, params_list: list) -> int:
    """Execute query with multiple parameter sets."""
    with get_cursor() as cursor:
        cursor.executemany(query, params_list)
        return cursor.rowcount
```

### Phase 2: Standard API Responses (utils/responses.py)

All API responses MUST use this format:

```python
"""
Standard API response helpers.
All endpoints MUST use these for consistent response format.
"""
from flask import jsonify
from typing import Any, Optional


def success(data: Any = None, meta: dict = None, status_code: int = 200):
    """
    Return success response.

    Format:
    {
        "success": true,
        "data": {...},
        "meta": {"pagination": {...}}  # optional
    }
    """
    response = {"success": True, "data": data}
    if meta:
        response["meta"] = meta
    return jsonify(response), status_code


def error(message: str, status_code: int = 400, errors: dict = None):
    """
    Return error response.

    Format:
    {
        "success": false,
        "error": "Error message",
        "errors": {"field": ["error1", "error2"]}  # optional, for validation
    }
    """
    response = {"success": False, "error": message}
    if errors:
        response["errors"] = errors
    return jsonify(response), status_code


def created(data: Any = None):
    """Return 201 Created response."""
    return success(data, status_code=201)


def no_content():
    """Return 204 No Content response."""
    return '', 204


def paginated(items: list, page: int, per_page: int, total: int):
    """
    Return paginated response with meta.

    Usage:
        return paginated(
            items=locations,
            page=1,
            per_page=20,
            total=150
        )
    """
    return success(
        data=items,
        meta={
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }
    )


# Common error responses
def not_found(message: str = "Resource not found"):
    return error(message, 404)

def unauthorized(message: str = "Unauthorized"):
    return error(message, 401)

def forbidden(message: str = "Forbidden"):
    return error(message, 403)

def bad_request(message: str, errors: dict = None):
    return error(message, 400, errors)

def server_error(message: str = "Internal server error"):
    return error(message, 500)
```

### Phase 3: Auth Decorators (utils/decorators.py)

```python
"""
Authentication and authorization decorators.
"""
from functools import wraps
from flask import request, g
import jwt
from app.config import Config
from app.utils.responses import unauthorized, forbidden
from app.utils.db import fetch_one


def get_current_user():
    """Get current user from JWT token or session."""
    # Check JWT first (API)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            user = fetch_one(
                "SELECT * FROM users WHERE id = %s",
                (payload['user_id'],)
            )
            return user
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # Check session (web)
    # ... Flask-Login integration
    return None


def require_auth(f):
    """
    Decorator: Require authenticated user.

    Usage:
        @bp.route('/profile')
        @require_auth
        def get_profile():
            user = g.current_user
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return unauthorized("Authentication required")
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """
    Decorator: Require admin role.

    Usage:
        @bp.route('/admin/users')
        @require_admin
        def list_users():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return unauthorized("Authentication required")
        if user['role'] != 'admin':
            return forbidden("Admin access required")
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_staff(f):
    """
    Decorator: Require staff or admin role.

    Usage:
        @bp.route('/admin/events')
        @require_staff
        def manage_events():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return unauthorized("Authentication required")
        if user['role'] not in ('admin', 'staff'):
            return forbidden("Staff access required")
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_patreon_tier(min_tier_id: int = None):
    """
    Decorator: Require Patreon supporter status.

    Args:
        min_tier_id: Minimum tier required (None = any active supporter)

    Usage:
        @bp.route('/exclusive/video/<int:id>')
        @require_patreon_tier(min_tier_id=2)
        def get_exclusive_video(id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return unauthorized("Authentication required")

            # Check Patreon status
            supporter = fetch_one("""
                SELECT ps.*, pt.amount_cents
                FROM patreon_supporters ps
                LEFT JOIN patreon_tiers pt ON ps.tier_id = pt.id
                WHERE ps.user_id = %s AND ps.is_active = TRUE
            """, (user['id'],))

            if not supporter:
                return forbidden("Patreon supporter status required")

            if min_tier_id:
                min_tier = fetch_one(
                    "SELECT amount_cents FROM patreon_tiers WHERE id = %s",
                    (min_tier_id,)
                )
                if min_tier and supporter['amount_cents'] < min_tier['amount_cents']:
                    return forbidden("Higher Patreon tier required")

            g.current_user = user
            g.patreon_supporter = supporter
            return f(*args, **kwargs)
        return decorated
    return decorator
```

### Phase 4: Model Pattern (NO SQLAlchemy)

Models are Python classes that wrap database operations:

```python
"""
Location model.
"""
from typing import Optional, List
from app.utils.db import fetch_one, fetch_all, execute


class Location:
    """
    Represents a club location (venue).

    Database tables: locations, location_translations
    """

    def __init__(self, data: dict):
        """Initialize from database row."""
        self.id = data['id']
        self.slug = data['slug']
        self.name = data['name']
        self.capacity = data['capacity']
        self.slurl = data.get('slurl')
        self.sort_order = data['sort_order']
        self.is_active = data['is_active']
        self.mood_category = data['mood_category']
        self.primary_color = data.get('primary_color')
        self.secondary_color = data.get('secondary_color')
        self.accent_color = data.get('accent_color')
        self.dark_color = data.get('dark_color')
        self.css_gradient = data.get('css_gradient')
        self.mood_keywords = data.get('mood_keywords')
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']

        # Translation fields (if joined)
        self.tagline = data.get('tagline')
        self.description = data.get('description')
        self.architecture_notes = data.get('architecture_notes')
        self.atmosphere_notes = data.get('atmosphere_notes')

    def to_dict(self) -> dict:
        """Convert to API response dict."""
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "capacity": self.capacity,
            "slurl": self.slurl,
            "mood_category": self.mood_category,
            "theme": {
                "primary_color": self.primary_color,
                "secondary_color": self.secondary_color,
                "accent_color": self.accent_color,
                "dark_color": self.dark_color,
                "css_gradient": self.css_gradient,
                "mood_keywords": self.mood_keywords.split(',') if self.mood_keywords else []
            },
            "tagline": self.tagline,
            "description": self.description,
            "architecture_notes": self.architecture_notes,
            "atmosphere_notes": self.atmosphere_notes
        }

    @classmethod
    def find_by_slug(cls, slug: str, lang: str = 'en') -> Optional['Location']:
        """
        Find location by slug with translation.

        Args:
            slug: URL-friendly identifier
            lang: Language code (en, it, fr, es)

        Returns:
            Location instance or None
        """
        data = fetch_one("""
            SELECT l.*, lt.tagline, lt.description,
                   lt.architecture_notes, lt.atmosphere_notes,
                   COALESCE(lt.name, l.name) as name
            FROM locations l
            LEFT JOIN location_translations lt
                ON l.id = lt.location_id AND lt.language = %s
            WHERE l.slug = %s AND l.is_active = TRUE
        """, (lang, slug))

        return cls(data) if data else None

    @classmethod
    def find_all(cls, lang: str = 'en', active_only: bool = True) -> List['Location']:
        """
        Get all locations with translations.

        Args:
            lang: Language code
            active_only: Filter to active locations only

        Returns:
            List of Location instances
        """
        query = """
            SELECT l.*, lt.tagline, lt.description,
                   lt.architecture_notes, lt.atmosphere_notes,
                   COALESCE(lt.name, l.name) as name
            FROM locations l
            LEFT JOIN location_translations lt
                ON l.id = lt.location_id AND lt.language = %s
        """
        params = [lang]

        if active_only:
            query += " WHERE l.is_active = TRUE"

        query += " ORDER BY l.sort_order, l.name"

        rows = fetch_all(query, tuple(params))
        return [cls(row) for row in rows]

    @classmethod
    def create(cls, data: dict) -> int:
        """
        Create new location.

        Args:
            data: Location data dict

        Returns:
            New location ID
        """
        return execute("""
            INSERT INTO locations
            (slug, name, capacity, slurl, sort_order, is_active,
             mood_category, primary_color, secondary_color,
             accent_color, dark_color, css_gradient, mood_keywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['slug'], data['name'], data.get('capacity', 100),
            data.get('slurl'), data.get('sort_order', 0),
            data.get('is_active', True), data['mood_category'],
            data.get('primary_color'), data.get('secondary_color'),
            data.get('accent_color'), data.get('dark_color'),
            data.get('css_gradient'), data.get('mood_keywords')
        ))

    @classmethod
    def update(cls, id: int, data: dict) -> int:
        """Update location by ID."""
        fields = []
        values = []

        allowed = ['name', 'capacity', 'slurl', 'sort_order', 'is_active',
                   'mood_category', 'primary_color', 'secondary_color',
                   'accent_color', 'dark_color', 'css_gradient', 'mood_keywords']

        for field in allowed:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])

        if not fields:
            return 0

        values.append(id)
        return execute(
            f"UPDATE locations SET {', '.join(fields)} WHERE id = %s",
            tuple(values)
        )

    @classmethod
    def set_translation(cls, location_id: int, lang: str, data: dict) -> int:
        """
        Create or update translation.

        Uses INSERT ... ON DUPLICATE KEY UPDATE pattern.
        """
        return execute("""
            INSERT INTO location_translations
            (location_id, language, name, tagline, description,
             architecture_notes, atmosphere_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                tagline = VALUES(tagline),
                description = VALUES(description),
                architecture_notes = VALUES(architecture_notes),
                atmosphere_notes = VALUES(atmosphere_notes)
        """, (
            location_id, lang, data.get('name'), data.get('tagline'),
            data.get('description'), data.get('architecture_notes'),
            data.get('atmosphere_notes')
        ))
```

### Phase 5: Route Pattern

```python
"""
Locations API routes.
"""
from flask import Blueprint, request
from app.models.location import Location
from app.utils.responses import success, not_found, paginated, created, bad_request
from app.utils.decorators import require_staff
from app.utils.helpers import get_lang


bp = Blueprint('locations', __name__, url_prefix='/api/v1/locations')


def get_lang() -> str:
    """Get language from request (query param, header, or default)."""
    return (
        request.args.get('lang') or
        request.accept_languages.best_match(['en', 'it', 'fr', 'es']) or
        'en'
    )


@bp.route('', methods=['GET'])
def list_locations():
    """
    List all active locations.

    Query params:
        lang: Language code (default: en)

    Returns:
        List of locations with translations
    """
    lang = get_lang()
    locations = Location.find_all(lang=lang)
    return success([loc.to_dict() for loc in locations])


@bp.route('/<slug>', methods=['GET'])
def get_location(slug: str):
    """
    Get single location by slug.

    Path params:
        slug: URL-friendly identifier

    Query params:
        lang: Language code (default: en)

    Returns:
        Location details with translation
    """
    lang = get_lang()
    location = Location.find_by_slug(slug, lang=lang)

    if not location:
        return not_found(f"Location '{slug}' not found")

    return success(location.to_dict())


@bp.route('/<slug>/events', methods=['GET'])
def get_location_events(slug: str):
    """
    Get upcoming events at a location.

    Path params:
        slug: Location slug

    Query params:
        lang: Language code
        limit: Max events to return (default: 10)

    Returns:
        List of upcoming events
    """
    from app.models.event import Event

    lang = get_lang()
    limit = request.args.get('limit', 10, type=int)

    location = Location.find_by_slug(slug, lang=lang)
    if not location:
        return not_found(f"Location '{slug}' not found")

    events = Event.find_by_location(location.id, lang=lang, limit=limit)
    return success([e.to_dict() for e in events])


# ============================================
# Admin routes (in routes/admin/locations.py)
# ============================================

admin_bp = Blueprint('admin_locations', __name__, url_prefix='/api/v1/admin/locations')


@admin_bp.route('', methods=['POST'])
@require_staff
def create_location():
    """
    Create new location.

    Body:
        slug: string (required)
        name: string (required)
        mood_category: string (required) - cosmic_tech, warm_intimate, hybrid
        capacity: int
        slurl: string
        primary_color: string (#hex)
        ...

    Returns:
        Created location
    """
    data = request.get_json()

    # Validate required fields
    required = ['slug', 'name', 'mood_category']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return bad_request(
            "Missing required fields",
            errors={f: [f"{f} is required"] for f in missing}
        )

    # Check slug uniqueness
    existing = Location.find_by_slug(data['slug'])
    if existing:
        return bad_request("Slug already exists", errors={"slug": ["Must be unique"]})

    location_id = Location.create(data)
    location = Location.find_by_id(location_id)

    return created(location.to_dict())


@admin_bp.route('/<int:id>', methods=['PUT'])
@require_staff
def update_location(id: int):
    """Update location by ID."""
    data = request.get_json()

    affected = Location.update(id, data)
    if affected == 0:
        return not_found("Location not found")

    location = Location.find_by_id(id)
    return success(location.to_dict())


@admin_bp.route('/<int:id>/translations', methods=['PUT'])
@require_staff
def update_translations(id: int):
    """
    Update location translations.

    Body:
        translations: {
            "en": {"tagline": "...", "description": "..."},
            "it": {"tagline": "...", "description": "..."}
        }
    """
    data = request.get_json()
    translations = data.get('translations', {})

    for lang, trans_data in translations.items():
        Location.set_translation(id, lang, trans_data)

    return success({"updated": list(translations.keys())})
```

### Phase 6: Service Pattern

```python
"""
Google Calendar integration service.
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from flask import current_app
from app.utils.db import fetch_one, execute
from datetime import datetime
import json


class GoogleCalendarService:
    """
    Manages Google Calendar sync for events.

    Two calendars:
        - Internal (staff): Full event details
        - Public: Published events only
    """

    def __init__(self):
        """Initialize with service account credentials."""
        creds_path = current_app.config['GOOGLE_CALENDAR_CREDENTIALS_PATH']
        self.credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.internal_calendar_id = current_app.config['GOOGLE_CALENDAR_INTERNAL_ID']
        self.public_calendar_id = current_app.config['GOOGLE_CALENDAR_PUBLIC_ID']

    def create_event(self, event_data: dict, calendars: list = None) -> dict:
        """
        Create event on Google Calendar(s).

        Args:
            event_data: Event dict with title, start_time, end_time, location, description
            calendars: List of 'internal', 'public' (default: both)

        Returns:
            Dict with calendar_type: event_id mappings
        """
        if calendars is None:
            calendars = ['internal', 'public']

        gcal_event = self._format_for_gcal(event_data)
        results = {}

        for cal_type in calendars:
            calendar_id = (
                self.internal_calendar_id if cal_type == 'internal'
                else self.public_calendar_id
            )

            try:
                result = self.service.events().insert(
                    calendarId=calendar_id,
                    body=gcal_event
                ).execute()

                results[cal_type] = result.get('id')
                self._log_action('create_event', cal_type, 'success', event_data, result)

            except Exception as e:
                self._log_action('create_event', cal_type, 'error', event_data, str(e))
                raise

        return results

    def update_event(self, event_id: str, event_data: dict, calendar_type: str) -> str:
        """Update existing calendar event."""
        calendar_id = (
            self.internal_calendar_id if calendar_type == 'internal'
            else self.public_calendar_id
        )

        gcal_event = self._format_for_gcal(event_data)

        result = self.service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=gcal_event
        ).execute()

        return result.get('id')

    def delete_event(self, event_id: str, calendar_type: str):
        """Delete event from calendar."""
        calendar_id = (
            self.internal_calendar_id if calendar_type == 'internal'
            else self.public_calendar_id
        )

        self.service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

    def _format_for_gcal(self, event_data: dict) -> dict:
        """Format event data for Google Calendar API."""
        return {
            'summary': event_data['title'],
            'description': event_data.get('description', ''),
            'location': event_data.get('location_name', ''),
            'start': {
                'dateTime': event_data['start_time'].isoformat(),
                'timeZone': event_data.get('timezone', 'Europe/Rome')
            },
            'end': {
                'dateTime': event_data['end_time'].isoformat(),
                'timeZone': event_data.get('timezone', 'Europe/Rome')
            }
        }

    def _log_action(self, action: str, calendar: str, status: str,
                    request_data: dict, response_data):
        """Log integration action to database."""
        execute("""
            INSERT INTO integration_logs
            (integration_name, action, status, request_data, response_data, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            'google_calendar',
            f"{action}_{calendar}",
            status,
            json.dumps(request_data, default=str),
            json.dumps(response_data, default=str) if isinstance(response_data, dict) else None,
            response_data if status == 'error' else None
        ))
```

### Phase 7: Celery Tasks Pattern

```python
"""
Notification tasks for Celery.
"""
from celery import shared_task
from app.utils.db import fetch_all, execute
from app.services.email import EmailService
from datetime import datetime


@shared_task(bind=True, max_retries=3)
def process_notification_queue(self):
    """
    Process pending notifications from queue.

    Runs periodically via Celery Beat.
    """
    pending = fetch_all("""
        SELECT nq.*, u.email, u.username, u.language
        FROM notification_queue nq
        JOIN users u ON nq.user_id = u.id
        WHERE nq.status = 'pending'
          AND nq.scheduled_for <= NOW()
        ORDER BY nq.scheduled_for
        LIMIT 50
    """)

    email_service = EmailService()

    for notification in pending:
        try:
            email_service.send(
                to=notification['email'],
                subject=notification['subject'],
                html=notification['body_html'],
                text=notification['body_text']
            )

            execute("""
                UPDATE notification_queue
                SET status = 'sent', sent_at = NOW()
                WHERE id = %s
            """, (notification['id'],))

        except Exception as e:
            execute("""
                UPDATE notification_queue
                SET status = 'failed', error_message = %s
                WHERE id = %s
            """, (str(e), notification['id']))

            # Retry on transient failures
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task
def send_event_reminders():
    """
    Send event reminder emails to subscribed users.

    Runs hourly via Celery Beat.
    """
    from app.models.event import Event

    # Find events starting in next 24 hours
    events = fetch_all("""
        SELECT e.*, et.title, et.description
        FROM events e
        JOIN event_translations et ON e.id = et.event_id
        WHERE e.is_published = TRUE
          AND e.start_time BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 24 HOUR)
          AND et.language = 'en'
    """)

    for event in events:
        # Find users who want reminders for this event
        users = fetch_all("""
            SELECT u.id, u.email, u.language,
                   unp.reminder_hours_before
            FROM users u
            JOIN user_notification_preferences unp ON u.id = unp.user_id
            WHERE unp.notify_event_reminders = TRUE
              AND u.email_verified = TRUE
              AND (
                  JSON_CONTAINS(unp.favorite_locations, %s) OR
                  JSON_CONTAINS(unp.favorite_artists, %s) OR
                  unp.favorite_locations IS NULL
              )
        """, (
            f'[{event["location_id"]}]',
            # Would need to join event_artists for artist check
            '[]'
        ))

        for user in users:
            queue_event_reminder(event, user)


@shared_task
def sync_patreon_supporters():
    """
    Sync Patreon supporter data.

    Runs daily via Celery Beat.
    """
    from app.services.patreon import PatreonService

    service = PatreonService()
    members = service.get_members()

    for member in members:
        # Update or create supporter record
        execute("""
            INSERT INTO patreon_supporters
            (patreon_user_id, email, full_name, tier_id, is_active,
             lifetime_support_cents, patron_since, last_charge_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                email = VALUES(email),
                full_name = VALUES(full_name),
                tier_id = VALUES(tier_id),
                is_active = VALUES(is_active),
                lifetime_support_cents = VALUES(lifetime_support_cents),
                last_charge_date = VALUES(last_charge_date)
        """, (
            member['patreon_user_id'],
            member['email'],
            member['full_name'],
            member.get('tier_id'),
            member['is_active'],
            member.get('lifetime_support_cents', 0),
            member.get('patron_since'),
            member.get('last_charge_date')
        ))
```

### Phase 8: Git Workflow

After backend code changes:

1. **Test locally:**
   ```bash
   cd backend
   pytest
   ```

2. **Review changes:**
   ```bash
   git status && git diff
   ```

3. **Stage and commit:**
   ```bash
   git add backend/
   git commit -m "feat(backend): [description]

   - Specific changes made

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

4. **Push (only if explicitly requested)**

## Important Notes

### Code Quality

- ALL code, comments, and docstrings MUST be in English
- Use type hints for function signatures
- Write docstrings for all public functions/methods
- Follow PEP 8 style guide

### Security

- NEVER concatenate strings in SQL queries - always use parameterized queries
- NEVER store passwords in plain text - use bcrypt
- NEVER expose sensitive data in API responses
- Validate all input data before processing
- Use HTTPS for all external API calls

### Database

- Always use connection pooling (get_cursor context manager)
- Always handle transactions properly (commit on success, rollback on error)
- Use appropriate indexes for frequently queried columns
- Handle NULL values explicitly

### API Design

- All responses use standard format: `{"success": bool, "data": ..., "error": ...}`
- Support `lang` parameter for translated content
- Use proper HTTP status codes (200, 201, 400, 401, 403, 404, 500)
- Paginate list endpoints that may return many items

### Translations

- Main entity in base table (locations, events, etc.)
- Translations in `*_translations` table
- Always LEFT JOIN to get translation with fallback to base name
- Default language is English ('en')
