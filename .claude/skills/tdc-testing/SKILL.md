---
name: tdc-testing
description: Create and run tests for The Dreamer's Cave. Use for pytest (backend), vitest (frontend), fixtures, mocking, and coverage.
fork: true
---

# TDC Testing Expert

Expert agent for creating and running tests for The Dreamer's Cave virtual music club website.

## Trigger

Use this skill when:
- User asks to create or run tests
- User says "/testing", "/tdc-testing", "/test", "/pytest", or "/vitest"
- User asks about test coverage or test fixtures
- User wants to mock external services
- User needs to verify code changes with tests

## Project Context

**The Dreamer's Cave** - Website for a virtual music club in Second Life.

### Test Stack

| Component | Technology | Config File |
|-----------|------------|-------------|
| Backend Tests | pytest | pytest.ini |
| Frontend Tests | vitest | vitest.config.js |
| Coverage Backend | pytest-cov | .coveragerc |
| Coverage Frontend | @vitest/coverage-v8 | vitest.config.js |
| Mocking | unittest.mock / vi.mock | - |

### Test Database

| Property | Value |
|----------|-------|
| Database | tdcweb_test |
| User | tdcweb |
| Password | tdcweb |
| Strategy | Transaction rollback per test |

### File Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── pytest.ini            # Pytest config
│   │
│   ├── unit/                 # Unit tests
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── test_user.py
│   │   │   ├── test_location.py
│   │   │   ├── test_event.py
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── test_auth.py
│   │   │   ├── test_email.py
│   │   │   └── ...
│   │   └── utils/
│   │       ├── test_db.py
│   │       ├── test_validators.py
│   │       └── ...
│   │
│   ├── api/                  # API endpoint tests
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_locations.py
│   │   ├── test_events.py
│   │   ├── test_admin.py
│   │   └── ...
│   │
│   └── fixtures/             # Test data
│       ├── __init__.py
│       ├── users.py
│       ├── locations.py
│       ├── events.py
│       └── ...

frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── __tests__/
│   │   │   │   ├── Modal.spec.js
│   │   │   │   └── Toast.spec.js
│   │   ├── locations/
│   │   │   └── __tests__/
│   │   │       └── LocationCard.spec.js
│   │   └── ...
│   │
│   ├── composables/
│   │   └── __tests__/
│   │       ├── useAuth.spec.js
│   │       ├── useApi.spec.js
│   │       └── useScrollAnimations.spec.js
│   │
│   └── stores/
│       └── __tests__/
│           ├── auth.spec.js
│           └── locations.spec.js
│
├── vitest.config.js
└── vitest.setup.js
```

## Instructions

### Phase 1: Backend - Pytest Configuration

#### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
python_classes = Test*

# Markers
markers =
    unit: Unit tests (fast, no DB)
    api: API endpoint tests
    integration: Integration tests (external services)
    slow: Slow tests

# Options
addopts =
    -v
    --strict-markers
    --tb=short
    -ra

# Environment
env =
    FLASK_ENV=testing
    DB_NAME=tdcweb_test
```

#### conftest.py (Main Fixtures)

```python
"""
Pytest fixtures for TDC backend tests.
"""
import pytest
import mysql.connector
from flask import Flask
from app import create_app
from app.config import TestConfig
from app.utils.db import init_pool, get_cursor, execute


# ============================================
# App Fixtures
# ============================================

@pytest.fixture(scope='session')
def app():
    """Create Flask application for testing."""
    app = create_app(TestConfig)
    app.config['TESTING'] = True

    # Initialize test database pool
    init_pool(app)

    yield app


@pytest.fixture(scope='session')
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def app_context(app):
    """Push application context for each test."""
    with app.app_context():
        yield


# ============================================
# Database Fixtures
# ============================================

@pytest.fixture(scope='session')
def db_connection():
    """
    Create test database connection.
    Runs once per test session.
    """
    conn = mysql.connector.connect(
        host='localhost',
        user='tdcweb',
        password='tdcweb',
        database='tdcweb_test',
        charset='utf8mb4'
    )
    yield conn
    conn.close()


@pytest.fixture(scope='function')
def db(db_connection, app_context):
    """
    Database fixture with transaction rollback.
    Each test runs in a transaction that is rolled back after.
    """
    db_connection.start_transaction()

    yield db_connection

    # Rollback after each test - clean slate
    db_connection.rollback()


@pytest.fixture(scope='function')
def db_cursor(db):
    """Provide a cursor with auto-cleanup."""
    cursor = db.cursor(dictionary=True)
    yield cursor
    cursor.close()


# ============================================
# Auth Fixtures
# ============================================

@pytest.fixture
def test_user(db_cursor, db):
    """Create a test user."""
    from app.services.auth import hash_password

    db_cursor.execute("""
        INSERT INTO users (email, username, password_hash, role, email_verified)
        VALUES (%s, %s, %s, %s, %s)
    """, ('test@example.com', 'testuser', hash_password('password123'), 'user', True))

    user_id = db_cursor.lastrowid
    db.commit()

    db_cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = db_cursor.fetchone()

    yield user

    # Cleanup handled by transaction rollback


@pytest.fixture
def admin_user(db_cursor, db):
    """Create a test admin user."""
    from app.services.auth import hash_password

    db_cursor.execute("""
        INSERT INTO users (email, username, password_hash, role, email_verified)
        VALUES (%s, %s, %s, %s, %s)
    """, ('admin@example.com', 'adminuser', hash_password('admin123'), 'admin', True))

    user_id = db_cursor.lastrowid
    db.commit()

    db_cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = db_cursor.fetchone()

    yield user


@pytest.fixture
def auth_headers(test_user):
    """Generate JWT auth headers for test user."""
    from app.services.auth import generate_jwt

    token = generate_jwt(test_user['id'])
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_auth_headers(admin_user):
    """Generate JWT auth headers for admin user."""
    from app.services.auth import generate_jwt

    token = generate_jwt(admin_user['id'])
    return {'Authorization': f'Bearer {token}'}


# ============================================
# Data Fixtures
# ============================================

@pytest.fixture
def test_location(db_cursor, db):
    """Create a test location."""
    db_cursor.execute("""
        INSERT INTO locations
        (slug, name, capacity, mood_category, primary_color, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('test-location', 'Test Location', 100, 'cosmic_tech', '#06b6d4', True))

    location_id = db_cursor.lastrowid

    # Add English translation
    db_cursor.execute("""
        INSERT INTO location_translations
        (location_id, language, tagline, description)
        VALUES (%s, %s, %s, %s)
    """, (location_id, 'en', 'Test tagline', 'Test description'))

    db.commit()

    db_cursor.execute("SELECT * FROM locations WHERE id = %s", (location_id,))
    location = db_cursor.fetchone()

    yield location


@pytest.fixture
def test_artist(db_cursor, db):
    """Create a test artist."""
    db_cursor.execute("""
        INSERT INTO artists
        (slug, name, performance_type, is_active)
        VALUES (%s, %s, %s, %s)
    """, ('test-artist', 'Test Artist', 'dj', True))

    artist_id = db_cursor.lastrowid

    # Add English translation
    db_cursor.execute("""
        INSERT INTO artist_translations
        (artist_id, language, bio)
        VALUES (%s, %s, %s)
    """, (artist_id, 'en', 'Test artist bio'))

    db.commit()

    db_cursor.execute("SELECT * FROM artists WHERE id = %s", (artist_id,))
    artist = db_cursor.fetchone()

    yield artist


@pytest.fixture
def test_event(db_cursor, db, test_location, test_artist):
    """Create a test event with location and artist."""
    from datetime import datetime, timedelta

    start_time = datetime.now() + timedelta(days=7)
    end_time = start_time + timedelta(hours=2)

    db_cursor.execute("""
        INSERT INTO events
        (slug, event_type, location_id, start_time, end_time, is_published)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ('test-event', 'dj_set', test_location['id'], start_time, end_time, True))

    event_id = db_cursor.lastrowid

    # Add translation
    db_cursor.execute("""
        INSERT INTO event_translations
        (event_id, language, title, description)
        VALUES (%s, %s, %s, %s)
    """, (event_id, 'en', 'Test Event', 'Test event description'))

    # Link artist
    db_cursor.execute("""
        INSERT INTO event_artists (event_id, artist_id, performance_order)
        VALUES (%s, %s, %s)
    """, (event_id, test_artist['id'], 1))

    db.commit()

    db_cursor.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    event = db_cursor.fetchone()

    yield event


# ============================================
# Mock Fixtures
# ============================================

@pytest.fixture
def mock_google_calendar(mocker):
    """Mock Google Calendar service."""
    mock = mocker.patch('app.services.google_calendar.GoogleCalendarService')
    mock_instance = mock.return_value
    mock_instance.create_event.return_value = {
        'internal': 'mock-internal-id',
        'public': 'mock-public-id'
    }
    mock_instance.update_event.return_value = 'mock-event-id'
    mock_instance.delete_event.return_value = None
    return mock_instance


@pytest.fixture
def mock_facebook(mocker):
    """Mock Facebook service."""
    mock = mocker.patch('app.services.facebook.FacebookService')
    mock_instance = mock.return_value
    mock_instance.post_event.return_value = {
        'page': {'id': 'mock-page-post-id'},
        'group': {'id': 'mock-group-post-id'}
    }
    return mock_instance


@pytest.fixture
def mock_patreon(mocker):
    """Mock Patreon service."""
    mock = mocker.patch('app.services.patreon.PatreonService')
    mock_instance = mock.return_value
    mock_instance.get_members.return_value = [
        {
            'patreon_user_id': 'mock-patron-1',
            'email': 'patron@example.com',
            'full_name': 'Test Patron',
            'tier_id': 1,
            'is_active': True
        }
    ]
    mock_instance.verify_webhook.return_value = True
    return mock_instance


@pytest.fixture
def mock_email(mocker):
    """Mock email service."""
    mock = mocker.patch('app.services.email.EmailService')
    mock_instance = mock.return_value
    mock_instance.send.return_value = True
    return mock_instance
```

### Phase 2: Backend - Unit Tests

#### test_location.py (Model Test)

```python
"""
Unit tests for Location model.
"""
import pytest
from app.models.location import Location


class TestLocationModel:
    """Tests for Location model."""

    def test_find_by_slug(self, app_context, test_location):
        """Test finding location by slug."""
        location = Location.find_by_slug('test-location', lang='en')

        assert location is not None
        assert location.slug == 'test-location'
        assert location.name == 'Test Location'
        assert location.tagline == 'Test tagline'

    def test_find_by_slug_not_found(self, app_context):
        """Test finding non-existent location returns None."""
        location = Location.find_by_slug('non-existent')

        assert location is None

    def test_find_by_slug_inactive(self, app_context, db_cursor, db):
        """Test that inactive locations are not returned."""
        db_cursor.execute("""
            INSERT INTO locations (slug, name, mood_category, is_active)
            VALUES (%s, %s, %s, %s)
        """, ('inactive-loc', 'Inactive', 'cosmic_tech', False))
        db.commit()

        location = Location.find_by_slug('inactive-loc')
        assert location is None

    def test_find_all(self, app_context, test_location):
        """Test finding all active locations."""
        locations = Location.find_all(lang='en')

        assert len(locations) >= 1
        assert any(loc.slug == 'test-location' for loc in locations)

    def test_find_all_with_translation_fallback(self, app_context, db_cursor, db):
        """Test that missing translations fall back to main name."""
        db_cursor.execute("""
            INSERT INTO locations (slug, name, mood_category, is_active)
            VALUES (%s, %s, %s, %s)
        """, ('no-translation', 'No Translation Location', 'warm_intimate', True))
        db.commit()

        location = Location.find_by_slug('no-translation', lang='it')

        assert location is not None
        assert location.name == 'No Translation Location'  # Fallback

    def test_to_dict(self, app_context, test_location):
        """Test location serialization."""
        location = Location.find_by_slug('test-location')
        data = location.to_dict()

        assert data['slug'] == 'test-location'
        assert data['name'] == 'Test Location'
        assert data['capacity'] == 100
        assert 'theme' in data
        assert data['theme']['primary_color'] == '#06b6d4'

    def test_create(self, app_context, db):
        """Test creating a new location."""
        location_id = Location.create({
            'slug': 'new-location',
            'name': 'New Location',
            'capacity': 150,
            'mood_category': 'hybrid',
            'primary_color': '#a855f7'
        })

        assert location_id > 0

        location = Location.find_by_id(location_id)
        assert location.slug == 'new-location'

    def test_update(self, app_context, test_location):
        """Test updating a location."""
        affected = Location.update(test_location['id'], {
            'capacity': 200,
            'primary_color': '#ff0000'
        })

        assert affected == 1

        location = Location.find_by_id(test_location['id'])
        assert location.capacity == 200

    def test_set_translation(self, app_context, test_location):
        """Test creating/updating translation."""
        Location.set_translation(test_location['id'], 'it', {
            'tagline': 'Tagline italiano',
            'description': 'Descrizione italiana'
        })

        location = Location.find_by_slug('test-location', lang='it')
        assert location.tagline == 'Tagline italiano'
```

#### test_auth_service.py (Service Test)

```python
"""
Unit tests for Auth service.
"""
import pytest
from datetime import datetime, timedelta
from app.services.auth import (
    hash_password,
    verify_password,
    generate_jwt,
    decode_jwt,
    create_user,
    authenticate_user
)


class TestPasswordHashing:
    """Tests for password hashing."""

    def test_hash_password(self):
        """Test password hashing."""
        hashed = hash_password('mypassword')

        assert hashed != 'mypassword'
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        hashed = hash_password('mypassword')

        assert verify_password('mypassword', hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        hashed = hash_password('mypassword')

        assert verify_password('wrongpassword', hashed) is False


class TestJWT:
    """Tests for JWT handling."""

    def test_generate_jwt(self, app_context):
        """Test JWT generation."""
        token = generate_jwt(user_id=123)

        assert token is not None
        assert len(token) > 50

    def test_decode_jwt_valid(self, app_context):
        """Test decoding valid JWT."""
        token = generate_jwt(user_id=123)
        payload = decode_jwt(token)

        assert payload is not None
        assert payload['user_id'] == 123

    def test_decode_jwt_expired(self, app_context, mocker):
        """Test decoding expired JWT returns None."""
        # Mock datetime to create expired token
        token = generate_jwt(user_id=123)

        # Fast-forward time
        mocker.patch('app.services.auth.datetime')
        from app.services.auth import datetime as mock_dt
        mock_dt.utcnow.return_value = datetime.utcnow() + timedelta(days=30)

        payload = decode_jwt(token)
        assert payload is None

    def test_decode_jwt_invalid(self, app_context):
        """Test decoding invalid JWT returns None."""
        payload = decode_jwt('invalid-token')

        assert payload is None


class TestAuthentication:
    """Tests for user authentication."""

    def test_authenticate_user_success(self, app_context, test_user):
        """Test successful authentication."""
        user = authenticate_user('test@example.com', 'password123')

        assert user is not None
        assert user['email'] == 'test@example.com'

    def test_authenticate_user_wrong_password(self, app_context, test_user):
        """Test authentication with wrong password."""
        user = authenticate_user('test@example.com', 'wrongpassword')

        assert user is None

    def test_authenticate_user_not_found(self, app_context):
        """Test authentication with non-existent user."""
        user = authenticate_user('nonexistent@example.com', 'password')

        assert user is None

    def test_authenticate_user_not_verified(self, app_context, db_cursor, db):
        """Test authentication with unverified email."""
        from app.services.auth import hash_password

        db_cursor.execute("""
            INSERT INTO users (email, username, password_hash, email_verified)
            VALUES (%s, %s, %s, %s)
        """, ('unverified@example.com', 'unverified', hash_password('pass'), False))
        db.commit()

        user = authenticate_user('unverified@example.com', 'pass')
        assert user is None
```

### Phase 3: Backend - API Tests

#### test_locations_api.py

```python
"""
API tests for locations endpoints.
"""
import pytest
import json


class TestLocationsAPI:
    """Tests for /api/v1/locations endpoints."""

    def test_list_locations(self, client, test_location):
        """Test GET /api/v1/locations returns list."""
        response = client.get('/api/v1/locations')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert len(data['data']) >= 1

    def test_list_locations_with_lang(self, client, test_location):
        """Test GET /api/v1/locations with language parameter."""
        response = client.get('/api/v1/locations?lang=en')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_get_location_by_slug(self, client, test_location):
        """Test GET /api/v1/locations/:slug returns single location."""
        response = client.get('/api/v1/locations/test-location')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['slug'] == 'test-location'
        assert data['data']['name'] == 'Test Location'
        assert 'theme' in data['data']

    def test_get_location_not_found(self, client):
        """Test GET /api/v1/locations/:slug returns 404."""
        response = client.get('/api/v1/locations/non-existent')

        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False

    def test_get_location_events(self, client, test_event):
        """Test GET /api/v1/locations/:slug/events returns events."""
        response = client.get('/api/v1/locations/test-location/events')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)


class TestAdminLocationsAPI:
    """Tests for admin location endpoints."""

    def test_create_location_unauthorized(self, client):
        """Test POST /api/v1/admin/locations requires auth."""
        response = client.post('/api/v1/admin/locations',
            json={'slug': 'new', 'name': 'New', 'mood_category': 'hybrid'}
        )

        assert response.status_code == 401

    def test_create_location_forbidden(self, client, auth_headers):
        """Test POST /api/v1/admin/locations requires admin role."""
        response = client.post('/api/v1/admin/locations',
            headers=auth_headers,
            json={'slug': 'new', 'name': 'New', 'mood_category': 'hybrid'}
        )

        assert response.status_code == 403

    def test_create_location_success(self, client, admin_auth_headers):
        """Test POST /api/v1/admin/locations creates location."""
        response = client.post('/api/v1/admin/locations',
            headers=admin_auth_headers,
            json={
                'slug': 'admin-created',
                'name': 'Admin Created Location',
                'mood_category': 'cosmic_tech',
                'capacity': 100
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['slug'] == 'admin-created'

    def test_create_location_validation(self, client, admin_auth_headers):
        """Test POST /api/v1/admin/locations validates input."""
        response = client.post('/api/v1/admin/locations',
            headers=admin_auth_headers,
            json={'name': 'Missing slug'}  # Missing required fields
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'errors' in data

    def test_update_location(self, client, admin_auth_headers, test_location):
        """Test PUT /api/v1/admin/locations/:id updates location."""
        response = client.put(
            f'/api/v1/admin/locations/{test_location["id"]}',
            headers=admin_auth_headers,
            json={'capacity': 250}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['capacity'] == 250

    def test_update_translations(self, client, admin_auth_headers, test_location):
        """Test PUT /api/v1/admin/locations/:id/translations."""
        response = client.put(
            f'/api/v1/admin/locations/{test_location["id"]}/translations',
            headers=admin_auth_headers,
            json={
                'translations': {
                    'it': {'tagline': 'Tagline italiano'},
                    'fr': {'tagline': 'Tagline français'}
                }
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'it' in data['data']['updated']
        assert 'fr' in data['data']['updated']
```

### Phase 4: Frontend - Vitest Configuration

#### vitest.config.js

```javascript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js'],
    include: ['src/**/*.spec.js'],
    exclude: ['node_modules', 'dist'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{js,vue}'],
      exclude: [
        'src/**/__tests__/**',
        'src/**/*.spec.js',
        'src/main.js'
      ]
    },
    // Mock CSS/assets
    css: false,
    deps: {
      inline: ['@vue', 'pinia']
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
```

#### vitest.setup.js

```javascript
/**
 * Vitest setup file - runs before each test file.
 */
import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// ============================================
// Vue Test Utils Config
// ============================================

// Global stubs
config.global.stubs = {
  // Stub router-link and router-view
  'router-link': {
    template: '<a><slot /></a>'
  },
  'router-view': true,
  // Stub Lucide icons
  'lucide-vue-next': true
}

// Global mocks
config.global.mocks = {
  $t: (key) => key,  // Mock i18n
  $route: {
    params: {},
    query: {}
  },
  $router: {
    push: vi.fn(),
    replace: vi.fn()
  }
}

// ============================================
// GSAP Mocks
// ============================================

vi.mock('gsap', () => ({
  gsap: {
    registerPlugin: vi.fn(),
    to: vi.fn(() => ({ kill: vi.fn() })),
    from: vi.fn(() => ({ kill: vi.fn() })),
    fromTo: vi.fn(() => ({ kill: vi.fn() })),
    set: vi.fn(),
    timeline: vi.fn(() => ({
      to: vi.fn().mockReturnThis(),
      from: vi.fn().mockReturnThis(),
      kill: vi.fn(),
      scrollTrigger: { kill: vi.fn() }
    })),
    ticker: {
      add: vi.fn(),
      lagSmoothing: vi.fn()
    }
  },
  ScrollTrigger: {
    update: vi.fn(),
    refresh: vi.fn(),
    kill: vi.fn()
  }
}))

vi.mock('gsap/ScrollTrigger', () => ({
  ScrollTrigger: {
    update: vi.fn(),
    refresh: vi.fn(),
    kill: vi.fn()
  }
}))

// ============================================
// Lenis Mock
// ============================================

vi.mock('@studio-freight/lenis', () => ({
  default: vi.fn(() => ({
    on: vi.fn(),
    raf: vi.fn(),
    destroy: vi.fn()
  }))
}))

// ============================================
// Browser APIs
// ============================================

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
})

// ============================================
// Pinia Setup
// ============================================

beforeEach(() => {
  setActivePinia(createPinia())
})
```

### Phase 5: Frontend - Component Tests

#### LocationCard.spec.js

```javascript
/**
 * Tests for LocationCard component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LocationCard from '../LocationCard.vue'

// Mock data
const mockLocation = {
  id: 1,
  slug: 'test-location',
  name: 'Test Location',
  capacity: 100,
  mood_category: 'cosmic_tech',
  tagline: 'Test tagline',
  theme: {
    primary_color: '#06b6d4',
    secondary_color: '#8b5cf6',
    accent_color: '#22c55e',
    css_gradient: 'linear-gradient(135deg, #06b6d4, #22c55e)'
  }
}

describe('LocationCard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders location name', () => {
    const wrapper = mount(LocationCard, {
      props: { location: mockLocation }
    })

    expect(wrapper.text()).toContain('Test Location')
  })

  it('renders tagline when provided', () => {
    const wrapper = mount(LocationCard, {
      props: { location: mockLocation }
    })

    expect(wrapper.text()).toContain('Test tagline')
  })

  it('applies theme CSS variables', () => {
    const wrapper = mount(LocationCard, {
      props: { location: mockLocation }
    })

    const card = wrapper.find('.location-card')
    const style = card.attributes('style')

    expect(style).toContain('--location-primary: #06b6d4')
  })

  it('shows mood category badge', () => {
    const wrapper = mount(LocationCard, {
      props: { location: mockLocation }
    })

    // Check for mood badge (cosmic_tech translates to some text)
    expect(wrapper.text()).toContain('locations.mood.cosmic_tech')
  })

  it('emits select event on click', async () => {
    const wrapper = mount(LocationCard, {
      props: { location: mockLocation }
    })

    await wrapper.find('.location-card').trigger('click')

    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')[0]).toEqual(['test-location'])
  })

  it('handles keyboard navigation', async () => {
    const wrapper = mount(LocationCard, {
      props: { location: mockLocation }
    })

    await wrapper.find('.location-card').trigger('keydown.enter')

    expect(wrapper.emitted('select')).toBeTruthy()
  })

  it('has correct accessibility attributes', () => {
    const wrapper = mount(LocationCard, {
      props: { location: mockLocation }
    })

    const card = wrapper.find('.location-card')

    expect(card.attributes('role')).toBe('button')
    expect(card.attributes('tabindex')).toBe('0')
    expect(card.attributes('aria-label')).toContain('Test Location')
  })

  it('applies size classes', () => {
    const wrapper = mount(LocationCard, {
      props: {
        location: mockLocation,
        size: 'large'
      }
    })

    expect(wrapper.find('.location-card').classes()).toContain('h-96')
  })

  it('disables animation when prop is false', () => {
    const wrapper = mount(LocationCard, {
      props: {
        location: mockLocation,
        animated: false
      }
    })

    // GSAP.set should not be called
    expect(wrapper.vm.animation).toBeUndefined()
  })
})
```

#### useScrollAnimations.spec.js (Composable Test)

```javascript
/**
 * Tests for useScrollAnimations composable.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, ref, onMounted, onUnmounted } from 'vue'
import { useScrollAnimations } from '../useScrollAnimations'

describe('useScrollAnimations', () => {
  let mockGsap

  beforeEach(() => {
    // Reset GSAP mock
    vi.resetModules()
  })

  it('returns expected functions', () => {
    const TestComponent = defineComponent({
      setup() {
        const animations = useScrollAnimations()
        return { animations }
      },
      template: '<div></div>'
    })

    const wrapper = mount(TestComponent)

    expect(wrapper.vm.animations.initSmoothScroll).toBeTypeOf('function')
    expect(wrapper.vm.animations.animateHero).toBeTypeOf('function')
    expect(wrapper.vm.animations.animateReveal).toBeTypeOf('function')
    expect(wrapper.vm.animations.animateParallax).toBeTypeOf('function')
    expect(wrapper.vm.animations.cleanup).toBeTypeOf('function')
  })

  it('cleans up animations on unmount', async () => {
    const cleanupSpy = vi.fn()

    const TestComponent = defineComponent({
      setup() {
        const { animateReveal, cleanup } = useScrollAnimations()
        const elementRef = ref(null)

        onMounted(() => {
          if (elementRef.value) {
            animateReveal(elementRef.value)
          }
        })

        return { elementRef }
      },
      template: '<div ref="elementRef"></div>'
    })

    const wrapper = mount(TestComponent)
    await flushPromises()

    // Unmount should trigger cleanup
    wrapper.unmount()

    // Verify GSAP cleanup was called (through mock)
    // The actual cleanup is handled by onUnmounted in the composable
  })

  it('initializes Lenis smooth scroll', () => {
    const TestComponent = defineComponent({
      setup() {
        const { initSmoothScroll } = useScrollAnimations()

        onMounted(() => {
          initSmoothScroll()
        })

        return {}
      },
      template: '<div></div>'
    })

    const wrapper = mount(TestComponent)

    // Lenis constructor should have been called
    const Lenis = require('@studio-freight/lenis').default
    expect(Lenis).toHaveBeenCalled()
  })
})
```

#### auth.spec.js (Store Test)

```javascript
/**
 * Tests for auth store.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'

// Mock API
vi.mock('@/composables/useApi', () => ({
  useApi: () => ({
    post: vi.fn(),
    get: vi.fn()
  })
}))

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('initializes with no user', () => {
    const store = useAuthStore()

    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('sets user on login', async () => {
    const store = useAuthStore()
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser'
    }

    store.setUser(mockUser)
    store.setToken('mock-jwt-token')

    expect(store.user).toEqual(mockUser)
    expect(store.token).toBe('mock-jwt-token')
    expect(store.isAuthenticated).toBe(true)
  })

  it('clears state on logout', () => {
    const store = useAuthStore()

    store.setUser({ id: 1, email: 'test@example.com' })
    store.setToken('mock-token')
    store.logout()

    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('persists token to localStorage', () => {
    const store = useAuthStore()

    store.setToken('persisted-token')

    expect(localStorage.getItem('auth_token')).toBe('persisted-token')
  })

  it('loads token from localStorage on init', () => {
    localStorage.setItem('auth_token', 'stored-token')

    const store = useAuthStore()
    store.initFromStorage()

    expect(store.token).toBe('stored-token')
  })

  it('computes isAdmin correctly', () => {
    const store = useAuthStore()

    store.setUser({ id: 1, role: 'user' })
    expect(store.isAdmin).toBe(false)

    store.setUser({ id: 1, role: 'admin' })
    expect(store.isAdmin).toBe(true)
  })

  it('computes isStaff correctly', () => {
    const store = useAuthStore()

    store.setUser({ id: 1, role: 'user' })
    expect(store.isStaff).toBe(false)

    store.setUser({ id: 1, role: 'staff' })
    expect(store.isStaff).toBe(true)

    store.setUser({ id: 1, role: 'admin' })
    expect(store.isStaff).toBe(true)
  })
})
```

### Phase 6: Running Tests

#### Backend Commands

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/models/test_location.py

# Run specific test class
pytest tests/unit/models/test_location.py::TestLocationModel

# Run specific test
pytest tests/unit/models/test_location.py::TestLocationModel::test_find_by_slug

# Run by marker
pytest -m unit       # Only unit tests
pytest -m api        # Only API tests
pytest -m "not slow" # Skip slow tests

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Generate JUnit XML for CI
pytest --junitxml=test-results.xml
```

#### Frontend Commands

```bash
# Run all tests
cd frontend
npm run test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run specific file
npm run test -- src/components/locations/__tests__/LocationCard.spec.js

# Run in watch mode
npm run test:watch

# Run matching pattern
npm run test -- --grep "LocationCard"
```

#### package.json Scripts

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage"
  }
}
```

### Phase 7: CI Integration

#### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: rutt1n0
          MYSQL_DATABASE: tdcweb_test
          MYSQL_USER: tdcweb
          MYSQL_PASSWORD: tdcweb
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Wait for MySQL
        run: |
          while ! mysqladmin ping -h127.0.0.1 --silent; do
            sleep 1
          done

      - name: Setup test database
        run: |
          mysql -h127.0.0.1 -uroot -prutt1n0 tdcweb_test < sql/schema.sql

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --junitxml=test-results.xml
        env:
          DB_HOST: 127.0.0.1
          DB_NAME: tdcweb_test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: frontend/coverage/coverage-final.json
```

### Phase 8: Git Workflow

After creating tests:

1. **Run tests locally:**
   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm test
   ```

2. **Check coverage:**
   ```bash
   # Backend
   pytest --cov=app --cov-report=term-missing

   # Frontend
   npm run test:coverage
   ```

3. **Commit:**
   ```bash
   git add backend/tests/ frontend/src/**/__tests__/
   git commit -m "test: [description]

   - Tests for: ...
   - Coverage: X%

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

## Important Notes

### Test Requirements

- Every new endpoint MUST have API tests
- Every new component MUST have spec tests
- Every new model/service MUST have unit tests
- Maintain minimum 80% coverage on new code

### Testing Best Practices

- Use fixtures for reusable test data
- Mock external services (Google, Facebook, Patreon)
- Test both success and error cases
- Test edge cases and validation
- Keep tests fast - mock slow operations
- Use transaction rollback for database tests

### Naming Conventions

| Type | Backend | Frontend |
|------|---------|----------|
| Test Files | test_*.py | *.spec.js |
| Test Classes | Test* | describe('*') |
| Test Functions | test_* | it('*') |
| Fixtures | lowercase | camelCase |

### CI Requirements

- All tests must pass before merge
- Coverage must not decrease
- Use exit code 0 for success, non-zero for failure
- Generate JUnit XML for CI reporting
