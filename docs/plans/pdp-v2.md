# Project Development Plan (PDP) v2.0
# The Dreamer's Cave - Virtual Music Club Website

**Version:** 2.0  
**Date:** January 2025  
**Domain:** thedreamerscave.club  
**Hosting:** mioh1 (Hetzner Frankfurt, Ubuntu)

---

## 1. Executive Summary

The Dreamer's Cave is a unique virtual music club in Second Life, established in 2019. The club spans two adjacent sims (capacity: 200+ concurrent visitors), features 10+ themed locations with custom-developed multimedia technology that synchronizes visual effects with live music. The club's motto is "You Can See The Music."

This PDP outlines the development of a professional website that:
- Showcases the club's unique visual identity and locations
- Provides an immersive landing page experience (Apple-style)
- Manages events with Google Calendar integration
- Automates social media posting (Facebook)
- Supports a Patreon-based revenue model with exclusive content
- Offers user registration with personalized notifications
- Serves as an API endpoint for in-world Second Life displays

---

## 2. Technology Stack

### 2.1 Backend
| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Python 3.11+ / Flask | RESTful API architecture |
| Database | MySQL 8.x | Using mysql-connector-python (NO SQLAlchemy) |
| Authentication | Flask-Login + JWT | Session for web, JWT for API |
| OAuth | Authlib | Google, Discord, Facebook providers |
| Email | SMTP (self-hosted) | iRedMail server already configured |
| Task Queue | Celery + Redis | Async tasks (email, social posting) |
| Caching | Redis | Session store + query cache |

### 2.2 Frontend
| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | Vue.js 3 | Composition API |
| Build Tool | Vite | Fast HMR, optimized builds |
| Styling | Tailwind CSS | Utility-first, custom theme |
| Animations | GSAP + ScrollTrigger | Apple-style scroll animations |
| Smooth Scroll | Lenis | Smooth scrolling library |
| Icons | Lucide Vue | Consistent icon set |
| State | Pinia | Vue 3 state management |
| i18n | Vue I18n | Multilingual support |
| WYSIWYG | TipTap | Rich text editor for blog |

### 2.3 Infrastructure
| Component | Technology | Notes |
|-----------|------------|-------|
| Server | Ubuntu 22.04 | mioh1 @ Hetzner Frankfurt |
| Web Server | Nginx | Reverse proxy + static files |
| SSL | Let's Encrypt | Auto-renewal with certbot |
| Process Manager | Gunicorn + systemd | Production WSGI |
| Containerization | Docker (optional) | For easier deployment |

---

## 3. Database Schema

### 3.1 Core Tables

```sql
-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255),  -- NULL if OAuth-only user
    avatar_name VARCHAR(255),     -- Second Life avatar name
    role ENUM('user', 'staff', 'admin') DEFAULT 'user',
    language VARCHAR(10) DEFAULT 'en',
    email_verified BOOLEAN DEFAULT FALSE,
    email_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE oauth_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    provider ENUM('google', 'discord', 'facebook') NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_provider_account (provider, provider_user_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- LOCATIONS
-- ============================================

CREATE TABLE locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,  -- URL-friendly identifier
    name VARCHAR(255) NOT NULL,
    capacity INT DEFAULT 100,
    slurl VARCHAR(500),                  -- Second Life URL
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    -- Visual identity (from mood guide)
    mood_category ENUM('cosmic_tech', 'warm_intimate', 'hybrid') NOT NULL,
    primary_color VARCHAR(7),            -- Hex color
    secondary_color VARCHAR(7),
    accent_color VARCHAR(7),
    dark_color VARCHAR(7),
    css_gradient TEXT,                   -- Custom gradient CSS
    mood_keywords VARCHAR(500),          -- Comma-separated keywords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_slug (slug),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE location_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,       -- 'en', 'it', 'fr', 'es', etc.
    name VARCHAR(255),                   -- Translated name (if different)
    tagline VARCHAR(500),                -- Short description
    description TEXT,                    -- Full description
    architecture_notes TEXT,             -- Architectural details
    atmosphere_notes TEXT,               -- Atmosphere description
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
    UNIQUE KEY unique_location_lang (location_id, language),
    INDEX idx_language (language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- ARTISTS
-- ============================================

CREATE TABLE artists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    avatar_name VARCHAR(255),
    performance_type ENUM('live_singer', 'dj', 'tribute', 'other') NOT NULL,
    profile_image_url VARCHAR(500),
    social_links JSON,                   -- {"facebook": "...", "instagram": "...", "youtube": "..."}
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_slug (slug),
    INDEX idx_performance_type (performance_type),
    INDEX idx_featured (is_featured)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE artist_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artist_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    bio TEXT,
    performance_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    UNIQUE KEY unique_artist_lang (artist_id, language),
    INDEX idx_language (language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- STAFF
-- ============================================

CREATE TABLE staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,                         -- Link to user account if exists
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    avatar_name VARCHAR(255),
    role VARCHAR(100) NOT NULL,          -- 'Owner', 'Manager', 'Host', 'DJ', etc.
    profile_image_url VARCHAR(500),
    contact_email VARCHAR(255),
    is_owner BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE staff_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    role_title VARCHAR(100),             -- Translated role
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
    UNIQUE KEY unique_staff_lang (staff_id, language),
    INDEX idx_language (language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- EVENTS
-- ============================================

CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(150) NOT NULL UNIQUE,
    event_type ENUM('live_singer', 'tribute_concert', 'dj_set', 'special', 'other') NOT NULL,
    location_id INT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Europe/Rome',
    -- External integrations
    google_calendar_id_internal VARCHAR(500),  -- Staff calendar event ID
    google_calendar_id_public VARCHAR(500),    -- Public calendar event ID
    facebook_event_id VARCHAR(255),
    -- Media
    poster_image_url VARCHAR(500),
    video_url VARCHAR(500),
    -- Status
    is_featured BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_start_time (start_time),
    INDEX idx_event_type (event_type),
    INDEX idx_published (is_published),
    INDEX idx_featured (is_featured)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE event_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE KEY unique_event_lang (event_id, language),
    INDEX idx_language (language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE event_artists (
    event_id INT NOT NULL,
    artist_id INT NOT NULL,
    performance_order INT DEFAULT 0,     -- Order of appearance
    set_time TIME,                       -- Optional specific set time
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, artist_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- BLOG / NEWS
-- ============================================

CREATE TABLE blog_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(200) NOT NULL UNIQUE,
    author_id INT,
    featured_image_url VARCHAR(500),
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    published_at TIMESTAMP NULL,
    is_featured BOOLEAN DEFAULT FALSE,
    view_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_status (status),
    INDEX idx_published_at (published_at),
    INDEX idx_featured (is_featured)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blog_post_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    excerpt TEXT,                        -- Short preview
    content LONGTEXT,                    -- Full HTML content from WYSIWYG
    meta_description VARCHAR(500),       -- SEO
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_post_lang (post_id, language),
    INDEX idx_language (language),
    FULLTEXT INDEX ft_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blog_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blog_category_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES blog_categories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_cat_lang (category_id, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blog_post_categories (
    post_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (post_id, category_id),
    FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES blog_categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- MEDIA LIBRARY
-- ============================================

CREATE TABLE media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    mime_type VARCHAR(100) NOT NULL,
    file_size INT,                       -- Bytes
    width INT,                           -- For images/videos
    height INT,
    url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    alt_text VARCHAR(255),
    uploaded_by INT,
    folder VARCHAR(100) DEFAULT 'general',  -- 'locations', 'events', 'artists', 'blog', 'general'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_folder (folder),
    INDEX idx_mime_type (mime_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PATREON INTEGRATION
-- ============================================

CREATE TABLE patreon_tiers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patreon_tier_id VARCHAR(255) UNIQUE,  -- Patreon's tier ID
    name VARCHAR(100) NOT NULL,
    amount_cents INT NOT NULL,            -- Monthly amount in cents
    benefits JSON,                        -- List of benefits
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE patreon_supporters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,                          -- Link to site user if registered
    patreon_user_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    full_name VARCHAR(255),
    avatar_name VARCHAR(255),             -- Second Life name if provided
    tier_id INT,
    lifetime_support_cents INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    patron_since DATE,
    last_charge_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (tier_id) REFERENCES patreon_tiers(id) ON DELETE SET NULL,
    INDEX idx_patreon_user_id (patreon_user_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE exclusive_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(150) NOT NULL UNIQUE,
    content_type ENUM('video', 'gallery', 'article', 'download') NOT NULL,
    min_tier_id INT,                      -- Minimum tier required (NULL = all supporters)
    featured_image_url VARCHAR(500),
    media_url VARCHAR(500),               -- Video/download URL
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (min_tier_id) REFERENCES patreon_tiers(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_published (is_published)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE exclusive_content_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES exclusive_content(id) ON DELETE CASCADE,
    UNIQUE KEY unique_content_lang (content_id, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- USER PREFERENCES & NOTIFICATIONS
-- ============================================

CREATE TABLE user_notification_preferences (
    user_id INT PRIMARY KEY,
    notify_new_events BOOLEAN DEFAULT TRUE,
    notify_event_reminders BOOLEAN DEFAULT TRUE,
    reminder_hours_before INT DEFAULT 24,
    notify_new_blog_posts BOOLEAN DEFAULT TRUE,
    notify_exclusive_content BOOLEAN DEFAULT TRUE,
    weekly_digest BOOLEAN DEFAULT FALSE,
    favorite_locations JSON,              -- Array of location IDs
    favorite_artists JSON,                -- Array of artist IDs
    favorite_event_types JSON,            -- Array of event types
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE notification_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    notification_type ENUM('event_reminder', 'new_event', 'new_blog', 'exclusive_content', 'weekly_digest', 'system') NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body_html TEXT,
    body_text TEXT,
    related_entity_type VARCHAR(50),      -- 'event', 'blog_post', 'exclusive_content'
    related_entity_id INT,
    scheduled_for TIMESTAMP NOT NULL,
    sent_at TIMESTAMP NULL,
    status ENUM('pending', 'sent', 'failed', 'cancelled') DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_scheduled (scheduled_for),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- INTEGRATION LOGS & SETTINGS
-- ============================================

CREATE TABLE integration_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    integration_name VARCHAR(50) NOT NULL UNIQUE,  -- 'google_calendar', 'facebook', 'patreon'
    settings JSON,                        -- Encrypted sensitive data
    is_enabled BOOLEAN DEFAULT FALSE,
    last_sync TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE integration_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    integration_name VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,         -- 'create_event', 'sync', 'webhook_received', etc.
    status ENUM('success', 'error', 'warning') NOT NULL,
    request_data JSON,
    response_data JSON,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_integration (integration_name),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- SITE SETTINGS & TRANSLATIONS
-- ============================================

CREATE TABLE site_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT,
    setting_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE supported_languages (
    code VARCHAR(10) PRIMARY KEY,         -- 'en', 'it', 'fr', 'es'
    name VARCHAR(50) NOT NULL,            -- 'English', 'Italiano', etc.
    native_name VARCHAR(50) NOT NULL,     -- 'English', 'Italiano', etc.
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Initial language data
INSERT INTO supported_languages (code, name, native_name, is_default, sort_order) VALUES
('en', 'English', 'English', TRUE, 1),
('it', 'Italian', 'Italiano', FALSE, 2),
('fr', 'French', 'Français', FALSE, 3),
('es', 'Spanish', 'Español', FALSE, 4);
```

---

## 4. API Structure

### 4.1 Public API Endpoints

```
/api/v1
│
├── /auth
│   ├── POST   /register              # Email registration
│   ├── POST   /login                 # Email/password login
│   ├── POST   /logout                # Logout (invalidate session)
│   ├── POST   /forgot-password       # Request password reset
│   ├── POST   /reset-password        # Reset with token
│   ├── GET    /oauth/{provider}      # OAuth redirect (google, discord, facebook)
│   ├── GET    /oauth/{provider}/callback  # OAuth callback
│   └── GET    /me                    # Current user info
│
├── /locations
│   ├── GET    /                      # List all locations
│   ├── GET    /{slug}                # Single location details
│   └── GET    /{slug}/events         # Upcoming events at location
│
├── /artists
│   ├── GET    /                      # List all artists
│   ├── GET    /featured              # Featured artists only
│   ├── GET    /{slug}                # Single artist details
│   └── GET    /{slug}/events         # Artist's upcoming events
│
├── /events
│   ├── GET    /                      # List events (filterable)
│   ├── GET    /upcoming              # Next N events
│   ├── GET    /calendar              # Calendar view data
│   ├── GET    /{slug}                # Single event details
│   └── GET    /featured              # Featured events
│
├── /blog
│   ├── GET    /                      # List posts (paginated)
│   ├── GET    /featured              # Featured posts
│   ├── GET    /categories            # List categories
│   ├── GET    /category/{slug}       # Posts by category
│   └── GET    /{slug}                # Single post
│
├── /staff
│   └── GET    /                      # List staff members
│
├── /support
│   ├── GET    /tiers                 # Patreon tiers info
│   └── GET    /supporters            # Wall of fame (public names)
│
├── /sl                               # Second Life Integration
│   ├── GET    /events                # Events for in-world panels
│   ├── GET    /events/next           # Next event only
│   └── GET    /events/today          # Today's events
│
└── /i18n
    ├── GET    /languages             # Available languages
    └── GET    /translations/{lang}   # UI translations
```

### 4.2 Protected User Endpoints

```
/api/v1/user (requires authentication)
│
├── GET    /profile                   # Get profile
├── PUT    /profile                   # Update profile
├── PUT    /password                  # Change password
├── GET    /notifications             # List notifications
├── PUT    /notifications/preferences # Update preferences
├── GET    /favorites                 # Get favorites
├── POST   /favorites/{type}/{id}     # Add favorite
├── DELETE /favorites/{type}/{id}     # Remove favorite
│
└── /patreon
    ├── GET    /status                # Patreon link status
    ├── POST   /link                  # Link Patreon account
    ├── DELETE /link                  # Unlink Patreon
    └── GET    /exclusive             # Access exclusive content
```

### 4.3 Admin API Endpoints

```
/api/v1/admin (requires admin/staff role)
│
├── /dashboard
│   ├── GET    /stats                 # Overview statistics
│   └── GET    /activity              # Recent activity log
│
├── /locations
│   ├── POST   /                      # Create location
│   ├── PUT    /{id}                  # Update location
│   ├── DELETE /{id}                  # Delete location
│   └── PUT    /{id}/translations     # Update translations
│
├── /artists
│   ├── POST   /                      # Create artist
│   ├── PUT    /{id}                  # Update artist
│   ├── DELETE /{id}                  # Delete artist
│   └── PUT    /{id}/translations     # Update translations
│
├── /events
│   ├── POST   /                      # Create event
│   ├── PUT    /{id}                  # Update event
│   ├── DELETE /{id}                  # Delete event
│   ├── POST   /{id}/publish          # Publish event
│   ├── POST   /{id}/sync-calendar    # Sync to Google Calendar
│   └── POST   /{id}/post-facebook    # Post to Facebook
│
├── /blog
│   ├── POST   /                      # Create post
│   ├── PUT    /{id}                  # Update post
│   ├── DELETE /{id}                  # Delete post
│   ├── POST   /{id}/publish          # Publish post
│   └── /categories                   # CRUD categories
│
├── /media
│   ├── GET    /                      # List media
│   ├── POST   /upload                # Upload file
│   ├── DELETE /{id}                  # Delete file
│   └── GET    /folders               # List folders
│
├── /staff
│   ├── POST   /                      # Add staff member
│   ├── PUT    /{id}                  # Update staff
│   └── DELETE /{id}                  # Remove staff
│
├── /users
│   ├── GET    /                      # List users
│   ├── GET    /{id}                  # User details
│   ├── PUT    /{id}/role             # Change role
│   └── DELETE /{id}                  # Delete user
│
├── /patreon
│   ├── GET    /supporters            # List all supporters
│   ├── POST   /sync                  # Sync with Patreon
│   ├── /exclusive                    # CRUD exclusive content
│   └── /tiers                        # Manage tiers
│
├── /integrations
│   ├── GET    /                      # List integrations
│   ├── PUT    /{name}                # Update settings
│   ├── POST   /{name}/test           # Test connection
│   └── GET    /{name}/logs           # View logs
│
├── /notifications
│   ├── GET    /queue                 # View queue
│   ├── POST   /send                  # Send manual notification
│   └── POST   /test                  # Send test email
│
└── /settings
    ├── GET    /                      # All settings
    ├── PUT    /                      # Update settings
    └── /languages                    # Manage languages
```

---

## 5. Frontend Architecture

### 5.1 Page Structure

```
/                           # Landing page (immersive)
├── /locations              # Locations overview
│   └── /:slug              # Single location
├── /events                 # Events calendar
│   └── /:slug              # Single event
├── /artists                # Artists gallery
│   └── /:slug              # Artist profile
├── /staff                  # Staff page
├── /technology             # About our tech
├── /support                # Patreon page
├── /blog                   # Blog/News
│   ├── /category/:slug     # Category filter
│   └── /:slug              # Single post
├── /login                  # Login page
├── /register               # Registration
├── /profile                # User profile (protected)
│   ├── /settings           # User settings
│   ├── /notifications      # Notification prefs
│   └── /favorites          # User favorites
├── /exclusive              # Patreon exclusive (protected)
└── /admin                  # Admin dashboard (protected)
    ├── /locations          # Manage locations
    ├── /artists            # Manage artists
    ├── /events             # Manage events
    ├── /blog               # Manage blog
    ├── /media              # Media library
    ├── /staff              # Manage staff
    ├── /users              # User management
    ├── /patreon            # Patreon management
    ├── /integrations       # Integration settings
    └── /settings           # Site settings
```

### 5.2 Component Architecture

```
src/
├── assets/
│   ├── images/
│   ├── videos/
│   └── fonts/
│
├── components/
│   ├── common/
│   │   ├── AppHeader.vue
│   │   ├── AppFooter.vue
│   │   ├── AppNav.vue
│   │   ├── LanguageSwitcher.vue
│   │   ├── LoadingSpinner.vue
│   │   ├── Modal.vue
│   │   ├── Toast.vue
│   │   └── ...
│   │
│   ├── landing/
│   │   ├── HeroSection.vue          # Video hero with scroll animations
│   │   ├── LocationsPreview.vue     # Animated location cards
│   │   ├── EventsCarousel.vue       # Upcoming events
│   │   ├── TechShowcase.vue         # "You Can See The Music" section
│   │   ├── PatreonCTA.vue           # Support callout
│   │   └── ...
│   │
│   ├── locations/
│   │   ├── LocationCard.vue         # With mood-based theming
│   │   ├── LocationGallery.vue
│   │   ├── LocationMap.vue          # Visual map of all locations
│   │   └── ...
│   │
│   ├── events/
│   │   ├── EventCard.vue
│   │   ├── EventCalendar.vue
│   │   ├── EventCountdown.vue
│   │   └── ...
│   │
│   ├── artists/
│   │   ├── ArtistCard.vue
│   │   ├── ArtistGallery.vue
│   │   └── ...
│   │
│   ├── blog/
│   │   ├── PostCard.vue
│   │   ├── PostContent.vue
│   │   └── ...
│   │
│   ├── auth/
│   │   ├── LoginForm.vue
│   │   ├── RegisterForm.vue
│   │   ├── OAuthButtons.vue
│   │   └── ...
│   │
│   ├── user/
│   │   ├── ProfileForm.vue
│   │   ├── NotificationSettings.vue
│   │   └── ...
│   │
│   └── admin/
│       ├── AdminSidebar.vue
│       ├── AdminHeader.vue
│       ├── DataTable.vue
│       ├── FormBuilder.vue
│       ├── MediaPicker.vue
│       ├── WysiwygEditor.vue        # TipTap wrapper
│       └── ...
│
├── composables/
│   ├── useAuth.js
│   ├── useApi.js
│   ├── useScrollAnimations.js       # GSAP ScrollTrigger hooks
│   ├── useTheme.js                  # Location-based theming
│   ├── useI18n.js
│   └── ...
│
├── stores/
│   ├── auth.js
│   ├── locations.js
│   ├── events.js
│   ├── artists.js
│   ├── ui.js
│   └── ...
│
├── views/
│   ├── LandingPage.vue
│   ├── LocationsPage.vue
│   ├── LocationDetailPage.vue
│   ├── EventsPage.vue
│   ├── EventDetailPage.vue
│   ├── ArtistsPage.vue
│   ├── ArtistDetailPage.vue
│   ├── StaffPage.vue
│   ├── TechnologyPage.vue
│   ├── SupportPage.vue
│   ├── BlogPage.vue
│   ├── BlogPostPage.vue
│   ├── LoginPage.vue
│   ├── RegisterPage.vue
│   ├── ProfilePage.vue
│   ├── ExclusivePage.vue
│   └── admin/
│       ├── DashboardPage.vue
│       ├── LocationsAdminPage.vue
│       └── ...
│
├── router/
│   └── index.js
│
├── i18n/
│   ├── en.json
│   ├── it.json
│   ├── fr.json
│   ├── es.json
│   └── index.js
│
├── styles/
│   ├── main.css
│   ├── animations.css               # GSAP custom styles
│   └── themes/
│       ├── base.css                 # Core dark theme
│       └── locations.css            # Location-specific CSS vars
│
├── utils/
│   ├── api.js
│   ├── date.js
│   ├── validators.js
│   └── ...
│
├── App.vue
└── main.js
```

### 5.3 Animation System

#### Landing Page Sections (Apple-style)

```javascript
// Example: useScrollAnimations.js composable
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from '@studio-freight/lenis'

gsap.registerPlugin(ScrollTrigger)

export function useScrollAnimations() {
  let lenis = null

  const initSmoothScroll = () => {
    lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    })

    function raf(time) {
      lenis.raf(time)
      requestAnimationFrame(raf)
    }
    requestAnimationFrame(raf)
  }

  const animateHero = (element) => {
    gsap.timeline({
      scrollTrigger: {
        trigger: element,
        start: 'top top',
        end: 'bottom top',
        scrub: true,
      }
    })
    .to(element.querySelector('.hero-video'), { scale: 1.2, opacity: 0 })
    .to(element.querySelector('.hero-text'), { y: -100, opacity: 0 }, 0)
  }

  const animateReveal = (elements, options = {}) => {
    gsap.from(elements, {
      y: 100,
      opacity: 0,
      duration: 1,
      stagger: 0.2,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: elements[0],
        start: 'top 80%',
        ...options
      }
    })
  }

  // Parallax effect for location cards
  const animateParallax = (element, speed = 0.5) => {
    gsap.to(element, {
      y: () => window.innerHeight * speed,
      ease: 'none',
      scrollTrigger: {
        trigger: element,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true
      }
    })
  }

  return {
    initSmoothScroll,
    animateHero,
    animateReveal,
    animateParallax
  }
}
```

#### Location Theming System

```css
/* styles/themes/locations.css */

/* Base dark theme */
:root {
  --color-bg: #0a0a0f;
  --color-surface: #141420;
  --color-text: #ffffff;
  --color-text-muted: #a0a0b0;
  --color-primary: #06b6d4;
  --color-secondary: #8b5cf6;
  --color-accent: #22c55e;
}

/* COSMIC/TECH */
[data-location="dreamerscave"] {
  --color-primary: #0891b2;
  --color-secondary: #06b6d4;
  --color-accent: #22c55e;
  --color-accent-warm: #eab308;
  --color-dark: #0c1222;
  --gradient-hero: linear-gradient(135deg, #0891b2, #22c55e, #eab308);
}

[data-location="dreamerscave2"] {
  --color-primary: #1e3a8a;
  --color-secondary: #3b82f6;
  --color-accent: #8b5cf6;
  --color-accent-warm: #ec4899;
  --color-dark: #0f172a;
  --gradient-hero: linear-gradient(135deg, #1e3a8a, #8b5cf6, #ec4899);
}

[data-location="dreamvision"] {
  --color-primary: #06b6d4;
  --color-secondary: #22c55e;
  --color-accent: #facc15;
  --color-glow: #ffffff;
  --color-dark: #020617;
  --gradient-hero: linear-gradient(135deg, #06b6d4, #22c55e, #facc15);
}

[data-location="evanescence"] {
  --color-primary: #fbbf24;
  --color-secondary: #0ea5e9;
  --color-accent: #06b6d4;
  --color-glow: #fef3c7;
  --color-dark: #0c1222;
  --gradient-hero: radial-gradient(ellipse at center, #fef3c7, #fbbf24, #0ea5e9, #0c1222);
}

/* HYBRID */
[data-location="livemagic"] {
  --color-primary: #dc2626;
  --color-secondary: #f97316;
  --color-accent-cool: #8b5cf6;
  --color-accent-green: #22c55e;
  --color-dark: #030712;
  --gradient-hero: linear-gradient(135deg, #dc2626, #f97316, #8b5cf6);
}

[data-location="lounge"] {
  --color-primary: #a855f7;
  --color-secondary: #ec4899;
  --color-accent: #f59e0b;
  --color-concrete: #57534e;
  --color-dark: #1c1917;
  --gradient-hero: linear-gradient(135deg, #a855f7, #ec4899, #f59e0b);
}

/* WARM/INTIMATE */
[data-location="arquipelago"] {
  --color-primary: #14b8a6;
  --color-secondary: #92400e;
  --color-accent: #f97316;
  --color-water: #06b6d4;
  --color-dark: #134e4a;
  --gradient-hero: linear-gradient(135deg, #14b8a6, #06b6d4, #f97316);
}

[data-location="noahsark"] {
  --color-primary: #d97706;
  --color-secondary: #92400e;
  --color-accent: #14b8a6;
  --color-gold: #fbbf24;
  --color-dark: #451a03;
  --gradient-hero: linear-gradient(135deg, #d97706, #fbbf24, #14b8a6);
}

[data-location="jazzclub"] {
  --color-primary: #92400e;
  --color-secondary: #78350f;
  --color-accent-red: #991b1b;
  --color-accent-teal: #14b8a6;
  --color-gold: #d97706;
  --color-dark: #1c1917;
  --gradient-hero: linear-gradient(135deg, #92400e, #991b1b, #14b8a6);
}

/* PENDING */
[data-location="chiringuito"] {
  --color-primary: #f97316;
  --color-secondary: #0ea5e9;
  --color-accent: #fbbf24;
  --color-dark: #1e3a5f;
  --gradient-hero: linear-gradient(135deg, #f97316, #fbbf24, #0ea5e9);
}

[data-location="tributestage"] {
  --color-primary: #dc2626;
  --color-secondary: #7c3aed;
  --color-accent: #fbbf24;
  --color-dark: #0a0a0f;
  --gradient-hero: linear-gradient(135deg, #dc2626, #7c3aed, #fbbf24);
}

---

## 6. External Integrations

### 6.1 Google Calendar Integration

**Two calendars:**
1. **Internal (Staff)** - Full event details, private
2. **Public** - Published events only

**Sync strategy:**
- Events created in website → pushed to both calendars
- Manual sync button for admins
- Webhook support for external changes (optional)

```python
# services/google_calendar.py
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleCalendarService:
    def __init__(self, credentials_path, calendar_ids):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.internal_calendar_id = calendar_ids['internal']
        self.public_calendar_id = calendar_ids['public']
    
    def create_event(self, event_data, calendars=['internal', 'public']):
        """Create event on specified calendars"""
        results = {}
        for cal_type in calendars:
            calendar_id = getattr(self, f'{cal_type}_calendar_id')
            result = self.service.events().insert(
                calendarId=calendar_id,
                body=self._format_event(event_data)
            ).execute()
            results[cal_type] = result.get('id')
        return results
    
    def update_event(self, event_id, event_data, calendar_type='both'):
        """Update existing event"""
        pass
    
    def delete_event(self, event_id, calendar_type='both'):
        """Delete event from calendars"""
        pass
```

### 6.2 Facebook Integration

**Targets:**
- Facebook Page: DreamVision
- Facebook Group: The Dreamer's Cave

**Posting strategy:**
- Manual trigger from admin dashboard
- Optional: Automatic posting on event publish
- Configurable templates per event type

```python
# services/facebook.py
import facebook

class FacebookService:
    def __init__(self, page_access_token, group_id, page_id):
        self.graph = facebook.GraphAPI(access_token=page_access_token)
        self.group_id = group_id
        self.page_id = page_id
    
    def post_event(self, event_data, targets=['page', 'group']):
        """Post event announcement to Facebook"""
        message = self._format_event_post(event_data)
        results = {}
        
        if 'page' in targets:
            results['page'] = self.graph.put_object(
                self.page_id, 'feed',
                message=message,
                link=event_data.get('url')
            )
        
        if 'group' in targets:
            results['group'] = self.graph.put_object(
                self.group_id, 'feed',
                message=message,
                link=event_data.get('url')
            )
        
        return results
    
    def _format_event_post(self, event_data):
        """Format event data into Facebook post"""
        # Templates based on event_type
        pass
```

### 6.3 Patreon Integration

**Webhook events to handle:**
- `members:pledge:create` - New supporter
- `members:pledge:update` - Tier change
- `members:pledge:delete` - Cancelled support

```python
# services/patreon.py
import patreon

class PatreonService:
    def __init__(self, creator_access_token):
        self.api = patreon.API(creator_access_token)
    
    def get_campaign(self):
        """Get campaign details and tiers"""
        pass
    
    def get_members(self):
        """Get all active patrons"""
        pass
    
    def verify_webhook(self, request):
        """Verify Patreon webhook signature"""
        pass
    
    def process_webhook(self, event_type, data):
        """Handle webhook events"""
        handlers = {
            'members:pledge:create': self._handle_new_pledge,
            'members:pledge:update': self._handle_pledge_update,
            'members:pledge:delete': self._handle_pledge_delete,
        }
        handler = handlers.get(event_type)
        if handler:
            return handler(data)
```

### 6.4 Second Life API

Simple JSON API for in-world displays:

```python
# routes/sl_api.py
@bp.route('/api/v1/sl/events')
def sl_events():
    """Events for Second Life panels"""
    events = Event.query.filter(
        Event.is_published == True,
        Event.start_time >= datetime.now()
    ).order_by(Event.start_time).limit(10).all()
    
    return jsonify([{
        'title': e.get_translation('en').title,
        'date': e.start_time.strftime('%Y-%m-%d'),
        'time': e.start_time.strftime('%H:%M'),
        'location': e.location.name if e.location else '',
        'type': e.event_type,
        'slurl': e.location.slurl if e.location else ''
    } for e in events])

@bp.route('/api/v1/sl/events/next')
def sl_next_event():
    """Single next event for countdown displays"""
    event = Event.query.filter(
        Event.is_published == True,
        Event.start_time >= datetime.now()
    ).order_by(Event.start_time).first()
    
    if not event:
        return jsonify({'event': None})
    
    return jsonify({
        'title': event.get_translation('en').title,
        'start_time': event.start_time.isoformat(),
        'location': event.location.name if event.location else ''
    })
```

---

## 7. Implementation Phases

### Phase 1: Foundation (4-6 weeks)

**Backend:**
- [ ] Project setup (Flask, MySQL, folder structure)
- [ ] Database implementation
- [ ] Authentication system (local + OAuth)
- [ ] Core API endpoints (locations, artists, staff)
- [ ] Admin authentication & authorization
- [ ] Media upload system

**Frontend:**
- [ ] Vue 3 + Vite project setup
- [ ] Tailwind configuration with custom theme
- [ ] Router setup with auth guards
- [ ] Base components (header, footer, nav)
- [ ] Authentication pages (login, register)
- [ ] i18n setup with EN, IT, FR, ES

**DevOps:**
- [ ] Server configuration on mioh1
- [ ] Nginx setup
- [ ] SSL certificates
- [ ] Development workflow

### Phase 2: Core Features (6-8 weeks)

**Backend:**
- [ ] Events CRUD with translations
- [ ] Blog/News system with WYSIWYG content
- [ ] User profiles and preferences
- [ ] Notification queue system
- [ ] Email service integration

**Frontend:**
- [ ] Landing page with scroll animations
- [ ] Locations pages with theming
- [ ] Events calendar and detail pages
- [ ] Artists gallery and profiles
- [ ] Staff page
- [ ] Blog listing and single post
- [ ] User profile pages

**Admin Dashboard:**
- [ ] Dashboard home with stats
- [ ] Locations management
- [ ] Artists management
- [ ] Events management
- [ ] Blog management
- [ ] Media library

### Phase 3: Integrations (4-6 weeks)

**Backend:**
- [ ] Google Calendar sync (both calendars)
- [ ] Facebook posting integration
- [ ] Patreon webhook handler
- [ ] Patreon supporter sync
- [ ] Second Life API endpoints

**Frontend:**
- [ ] Patreon support page
- [ ] Exclusive content area
- [ ] Notification preferences UI
- [ ] Integration status in admin

**Admin Dashboard:**
- [ ] Integration settings panel
- [ ] Manual sync triggers
- [ ] Facebook posting UI
- [ ] Patreon management

### Phase 4: Polish & Launch (2-4 weeks)

- [ ] Performance optimization
- [ ] SEO implementation
- [ ] Accessibility audit
- [ ] Security audit
- [ ] Load testing
- [ ] Bug fixes
- [ ] Documentation
- [ ] Content population
- [ ] Beta testing
- [ ] Launch

---

## 8. Location Visual Identity Reference

Based on the mood guide, each location has a distinct visual identity:

| Location | Category | Primary | Secondary | Accent | Mood |
|----------|----------|---------|-----------|--------|------|
| The Dreamer's Cave | Cosmic/Tech | #0891b2 | #06b6d4 | #22c55e | Immersive, hexagonal, cosmic |
| The Dreamer's Cave 2 | Cosmic/Tech | #1e3a8a | #3b82f6 | #8b5cf6 | Urban, futuristic, loft |
| DreamVision | Cosmic/Tech | #06b6d4 | #22c55e | #facc15 | 360°, explosive, monumental |
| Evanescence | Cosmic/Tech | #fbbf24 | #0ea5e9 | #06b6d4 | Transcendent, golden portal |
| Live Magic | Hybrid | #dc2626 | #f97316 | #8b5cf6 | Space station, fire, stars |
| The Lounge | Hybrid | #a855f7 | #ec4899 | #f59e0b | Brutalist, Berlin club |
| Arquipélago | Warm/Intimate | #14b8a6 | #92400e | #f97316 | Tropical, bioluminescent |
| Noah's Ark | Warm/Intimate | #d97706 | #92400e | #14b8a6 | Fairy tale, wooden ship |
| Jazz Club | Warm/Intimate | #92400e | #78350f | #14b8a6 | Speakeasy, 1920s |
| Chiringuito | TBD | TBD | TBD | TBD | Beach bar (pending) |
| Tribute Stage | TBD | TBD | TBD | TBD | Concert stage (pending) |

---

## 9. Security Considerations

### 9.1 Authentication
- Password hashing with bcrypt (min 12 rounds)
- JWT tokens with short expiry (15 min access, 7 day refresh)
- OAuth state parameter validation
- CSRF protection for all forms
- Rate limiting on auth endpoints

### 9.2 Data Protection
- All database connections over SSL
- Sensitive settings encrypted at rest
- PII handling compliance (GDPR)
- Secure password reset flow
- Session invalidation on password change

### 9.3 API Security
- API rate limiting (per IP and per user)
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)
- CORS configuration

### 9.4 Infrastructure
- Regular security updates
- Firewall configuration (UFW)
- Fail2ban for brute force protection
- HTTPS everywhere
- Regular backups with encryption

---

## 10. File Structure

```
thedreamerscave/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask app factory
│   │   ├── config.py                # Configuration classes
│   │   ├── extensions.py            # Flask extensions init
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── location.py
│   │   │   ├── artist.py
│   │   │   ├── event.py
│   │   │   ├── blog.py
│   │   │   ├── media.py
│   │   │   ├── patreon.py
│   │   │   └── ...
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── locations.py
│   │   │   │   ├── artists.py
│   │   │   │   ├── events.py
│   │   │   │   ├── blog.py
│   │   │   │   ├── users.py
│   │   │   │   ├── sl.py            # Second Life API
│   │   │   │   └── ...
│   │   │   └── admin/
│   │   │       ├── __init__.py
│   │   │       └── ...
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── email.py
│   │   │   ├── google_calendar.py
│   │   │   ├── facebook.py
│   │   │   ├── patreon.py
│   │   │   └── media.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── db.py                # mysql-connector helpers
│   │   │   ├── validators.py
│   │   │   ├── decorators.py
│   │   │   └── helpers.py
│   │   │
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── notifications.py
│   │       └── sync.py
│   │
│   ├── migrations/
│   │   └── ...
│   │
│   ├── tests/
│   │   └── ...
│   │
│   ├── requirements.txt
│   ├── wsgi.py
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   └── ... (see Frontend Architecture)
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── ...
│
├── nginx/
│   └── thedreamerscave.conf
│
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── ...
│
├── docker-compose.yml (optional)
├── README.md
└── .gitignore
```

---

## 11. Development Notes for Claude Code

### Key Implementation Guidelines

1. **Database Access**: Use `mysql-connector-python` directly, NOT SQLAlchemy. Create a utility module (`utils/db.py`) with helper functions for common operations.

2. **Translations**: All user-facing content has a separate `*_translations` table. Always query with language parameter.

3. **Authentication Flow**:
   - Session-based for web UI
   - JWT for API endpoints
   - OAuth providers: Google, Discord, Facebook

4. **File Uploads**: Store in `/var/www/thedreamerscave/uploads/` with subfolders per type. Generate thumbnails for images.

5. **Email**: Use the existing iRedMail server. Configure SMTP in environment variables.

6. **Animations**: GSAP with ScrollTrigger for all scroll-based animations. Use Lenis for smooth scrolling.

7. **Theming**: Each location should be able to "theme" the page it's displayed on using CSS custom properties.

8. **i18n Strategy**: 
   - UI strings in JSON files
   - Content in database with `*_translations` tables
   - Language detection: URL param > cookie > browser preference > default (EN)

9. **API Responses**: Always wrap in consistent format:
   ```json
   {
     "success": true,
     "data": {...},
     "meta": {"pagination": {...}}
   }
   ```

10. **Error Handling**: Use custom exception classes, return proper HTTP status codes with error details in development.

---

## Appendix: Environment Variables

```env
# Flask
FLASK_APP=wsgi.py
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=dreamerscave
DB_USER=dreamerscave
DB_PASSWORD=your-db-password

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
MAIL_SERVER=mail.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=noreply@thedreamerscave.club
MAIL_PASSWORD=your-mail-password
MAIL_DEFAULT_SENDER=The Dreamer's Cave <noreply@thedreamerscave.club>

# OAuth - Google
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OAuth - Discord
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret

# OAuth - Facebook
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_CALENDAR_INTERNAL_ID=internal-calendar-id
GOOGLE_CALENDAR_PUBLIC_ID=public-calendar-id

# Facebook Page/Group
FACEBOOK_PAGE_ACCESS_TOKEN=your-page-token
FACEBOOK_PAGE_ID=your-page-id
FACEBOOK_GROUP_ID=your-group-id

# Patreon
PATREON_CLIENT_ID=your-patreon-client-id
PATREON_CLIENT_SECRET=your-patreon-client-secret
PATREON_CREATOR_ACCESS_TOKEN=your-creator-token
PATREON_WEBHOOK_SECRET=your-webhook-secret

# File Storage
UPLOAD_FOLDER=/var/www/thedreamerscave/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

---

*Document Version: 2.0*
*Created: January 2025*
*For: The Dreamer's Cave Virtual Music Club*
