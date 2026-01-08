-- ============================================
-- MIGRATION 001: Initial Schema
-- THE DREAMER'S CAVE - DATABASE
-- Version: 1.0.0
-- Date: January 2025
-- ============================================

-- This migration creates the initial database schema
-- Run with: mysql -u tdcweb -p tdcweb < 001_initial.sql

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    avatar_name VARCHAR(255),
    role ENUM('user', 'staff', 'admin') DEFAULT 'user',
    language VARCHAR(10) DEFAULT 'en',
    email_verified BOOLEAN DEFAULT FALSE,
    email_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS oauth_accounts (
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

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_token (session_token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- LOCATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    capacity INT DEFAULT 100,
    slurl VARCHAR(500),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    mood_category ENUM('cosmic_tech', 'warm_intimate', 'hybrid') NOT NULL,
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    accent_color VARCHAR(7),
    dark_color VARCHAR(7),
    css_gradient TEXT,
    mood_keywords VARCHAR(500),
    hero_image_url VARCHAR(500),
    gallery_images JSON,
    video_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_slug (slug),
    INDEX idx_active (is_active),
    INDEX idx_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS location_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    name VARCHAR(255),
    tagline VARCHAR(500),
    description TEXT,
    architecture_notes TEXT,
    atmosphere_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
    UNIQUE KEY unique_location_lang (location_id, language),
    INDEX idx_language (language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- ARTISTS
-- ============================================

CREATE TABLE IF NOT EXISTS artists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    avatar_name VARCHAR(255),
    performance_type ENUM('live_singer', 'dj', 'tribute', 'other') NOT NULL,
    profile_image_url VARCHAR(500),
    social_links JSON,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_slug (slug),
    INDEX idx_performance_type (performance_type),
    INDEX idx_featured (is_featured),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS artist_translations (
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

CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    avatar_name VARCHAR(255),
    role VARCHAR(100) NOT NULL,
    profile_image_url VARCHAR(500),
    contact_email VARCHAR(255),
    is_owner BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_active (is_active),
    INDEX idx_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS staff_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    staff_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    role_title VARCHAR(100),
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

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(150) NOT NULL UNIQUE,
    event_type ENUM('live_singer', 'tribute_concert', 'dj_set', 'special', 'other') NOT NULL,
    location_id INT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    timezone VARCHAR(50) DEFAULT 'Europe/Rome',
    google_calendar_id_internal VARCHAR(500),
    google_calendar_id_public VARCHAR(500),
    facebook_event_id VARCHAR(255),
    poster_image_url VARCHAR(500),
    video_url VARCHAR(500),
    is_featured BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT FALSE,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    INDEX idx_event_type (event_type),
    INDEX idx_published (is_published),
    INDEX idx_featured (is_featured),
    INDEX idx_location (location_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS event_translations (
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

CREATE TABLE IF NOT EXISTS event_artists (
    event_id INT NOT NULL,
    artist_id INT NOT NULL,
    performance_order INT DEFAULT 0,
    set_time TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, artist_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- BLOG / NEWS
-- ============================================

CREATE TABLE IF NOT EXISTS blog_posts (
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

CREATE TABLE IF NOT EXISTS blog_post_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    excerpt TEXT,
    content LONGTEXT,
    meta_description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_post_lang (post_id, language),
    INDEX idx_language (language),
    FULLTEXT INDEX ft_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blog_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blog_category_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    language VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES blog_categories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_cat_lang (category_id, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS blog_post_categories (
    post_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (post_id, category_id),
    FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES blog_categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- MEDIA LIBRARY
-- ============================================

CREATE TABLE IF NOT EXISTS media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    mime_type VARCHAR(100) NOT NULL,
    file_size INT,
    width INT,
    height INT,
    url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    alt_text VARCHAR(255),
    uploaded_by INT,
    folder VARCHAR(100) DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_folder (folder),
    INDEX idx_mime_type (mime_type),
    INDEX idx_uploaded_by (uploaded_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PATREON INTEGRATION
-- ============================================

CREATE TABLE IF NOT EXISTS patreon_tiers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patreon_tier_id VARCHAR(255) UNIQUE,
    name VARCHAR(100) NOT NULL,
    amount_cents INT NOT NULL,
    benefits JSON,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS patreon_supporters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    patreon_user_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    full_name VARCHAR(255),
    avatar_name VARCHAR(255),
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
    INDEX idx_active (is_active),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS exclusive_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(150) NOT NULL UNIQUE,
    content_type ENUM('video', 'gallery', 'article', 'download') NOT NULL,
    min_tier_id INT,
    featured_image_url VARCHAR(500),
    media_url VARCHAR(500),
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (min_tier_id) REFERENCES patreon_tiers(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_published (is_published),
    INDEX idx_content_type (content_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS exclusive_content_translations (
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

CREATE TABLE IF NOT EXISTS user_notification_preferences (
    user_id INT PRIMARY KEY,
    notify_new_events BOOLEAN DEFAULT TRUE,
    notify_event_reminders BOOLEAN DEFAULT TRUE,
    reminder_hours_before INT DEFAULT 24,
    notify_new_blog_posts BOOLEAN DEFAULT TRUE,
    notify_exclusive_content BOOLEAN DEFAULT TRUE,
    weekly_digest BOOLEAN DEFAULT FALSE,
    favorite_locations JSON,
    favorite_artists JSON,
    favorite_event_types JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    entity_type ENUM('location', 'artist', 'event') NOT NULL,
    entity_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_favorite (user_id, entity_type, entity_id),
    INDEX idx_user_id (user_id),
    INDEX idx_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notification_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    notification_type ENUM('event_reminder', 'new_event', 'new_blog', 'exclusive_content', 'weekly_digest', 'system') NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body_html TEXT,
    body_text TEXT,
    related_entity_type VARCHAR(50),
    related_entity_id INT,
    scheduled_for TIMESTAMP NOT NULL,
    sent_at TIMESTAMP NULL,
    status ENUM('pending', 'sent', 'failed', 'cancelled') DEFAULT 'pending',
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_scheduled (scheduled_for),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- INTEGRATION LOGS & SETTINGS
-- ============================================

CREATE TABLE IF NOT EXISTS integration_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    integration_name VARCHAR(50) NOT NULL UNIQUE,
    settings JSON,
    is_enabled BOOLEAN DEFAULT FALSE,
    last_sync TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS integration_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    integration_name VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
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

CREATE TABLE IF NOT EXISTS site_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT,
    setting_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    description VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS supported_languages (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    native_name VARCHAR(50) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- AUDIT LOG
-- ============================================

CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- SCHEMA MIGRATIONS TRACKING
-- ============================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_version (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- INITIAL DATA
-- ============================================

-- Supported languages
INSERT INTO supported_languages (code, name, native_name, is_default, sort_order) VALUES
('en', 'English', 'English', TRUE, 1),
('it', 'Italian', 'Italiano', FALSE, 2),
('fr', 'French', 'Français', FALSE, 3),
('es', 'Spanish', 'Español', FALSE, 4)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Default integration settings
INSERT INTO integration_settings (integration_name, settings, is_enabled) VALUES
('google_calendar', '{}', FALSE),
('facebook', '{}', FALSE),
('patreon', '{}', FALSE)
ON DUPLICATE KEY UPDATE integration_name = VALUES(integration_name);

-- Default site settings
INSERT INTO site_settings (setting_key, setting_value, setting_type, description) VALUES
('site_name', 'The Dreamer''s Cave', 'string', 'Website name'),
('site_tagline', 'You Can See The Music', 'string', 'Website tagline/motto'),
('site_description', 'Virtual music club in Second Life', 'string', 'Website description for SEO'),
('timezone', 'Europe/Rome', 'string', 'Default timezone'),
('events_per_page', '12', 'number', 'Events shown per page'),
('blog_posts_per_page', '10', 'number', 'Blog posts shown per page'),
('maintenance_mode', 'false', 'boolean', 'Enable maintenance mode'),
('registration_enabled', 'true', 'boolean', 'Allow new user registration'),
('social_facebook_url', 'https://www.facebook.com/dreamvision.sl', 'string', 'Facebook page URL'),
('social_patreon_url', 'https://www.patreon.com/thedreamerscave', 'string', 'Patreon page URL')
ON DUPLICATE KEY UPDATE setting_key = VALUES(setting_key);

-- Initial locations (from mood guide)
INSERT INTO locations (slug, name, capacity, mood_category, primary_color, secondary_color, accent_color, dark_color, css_gradient, mood_keywords, sort_order) VALUES
('dreamerscave', 'The Dreamer''s Cave', 100, 'cosmic_tech', '#0891b2', '#06b6d4', '#22c55e', '#0c1222', 'linear-gradient(135deg, #0891b2, #22c55e, #eab308)', 'immersive,hexagonal,cosmic,technological', 1),
('dreamerscave2', 'The Dreamer''s Cave 2', 100, 'cosmic_tech', '#1e3a8a', '#3b82f6', '#8b5cf6', '#0f172a', 'linear-gradient(135deg, #1e3a8a, #8b5cf6, #ec4899)', 'urban,futuristic,loft,neon', 2),
('dreamvision', 'DreamVision', 150, 'cosmic_tech', '#06b6d4', '#22c55e', '#facc15', '#020617', 'linear-gradient(135deg, #06b6d4, #22c55e, #facc15)', '360,explosive,monumental,immersive', 3),
('evanescence', 'Evanescence', 100, 'cosmic_tech', '#fbbf24', '#0ea5e9', '#06b6d4', '#0c1222', 'radial-gradient(ellipse at center, #fef3c7, #fbbf24, #0ea5e9, #0c1222)', 'transcendent,golden,portal,ethereal', 4),
('livemagic', 'Live Magic', 80, 'hybrid', '#dc2626', '#f97316', '#8b5cf6', '#030712', 'linear-gradient(135deg, #dc2626, #f97316, #8b5cf6)', 'space,fire,stars,energy', 5),
('lounge', 'The Lounge', 60, 'hybrid', '#a855f7', '#ec4899', '#f59e0b', '#1c1917', 'linear-gradient(135deg, #a855f7, #ec4899, #f59e0b)', 'brutalist,berlin,underground,concrete', 6),
('arquipelago', 'Arquipélago', 80, 'warm_intimate', '#14b8a6', '#92400e', '#f97316', '#134e4a', 'linear-gradient(135deg, #14b8a6, #06b6d4, #f97316)', 'tropical,bioluminescent,natural,water', 7),
('noahsark', 'Noah''s Ark', 80, 'warm_intimate', '#d97706', '#92400e', '#14b8a6', '#451a03', 'linear-gradient(135deg, #d97706, #fbbf24, #14b8a6)', 'fairytale,wooden,ship,warm', 8),
('jazzclub', 'Jazz Club', 50, 'warm_intimate', '#92400e', '#78350f', '#14b8a6', '#1c1917', 'linear-gradient(135deg, #92400e, #991b1b, #14b8a6)', 'speakeasy,1920s,intimate,jazz', 9),
('chiringuito', 'Chiringuito', 60, 'warm_intimate', '#f97316', '#0ea5e9', '#fbbf24', '#1e3a5f', 'linear-gradient(135deg, #f97316, #fbbf24, #0ea5e9)', 'beach,summer,relaxed,sunset', 10),
('tributestage', 'Tribute Stage', 120, 'hybrid', '#dc2626', '#7c3aed', '#fbbf24', '#0a0a0f', 'linear-gradient(135deg, #dc2626, #7c3aed, #fbbf24)', 'concert,rock,tribute,stage', 11)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Location translations (English)
INSERT INTO location_translations (location_id, language, tagline, description, architecture_notes, atmosphere_notes)
SELECT l.id, 'en',
    CASE l.slug
        WHEN 'dreamerscave' THEN 'Where Dreams Take Shape'
        WHEN 'dreamerscave2' THEN 'Urban Dreams, Infinite Possibilities'
        WHEN 'dreamvision' THEN 'The Ultimate 360° Experience'
        WHEN 'evanescence' THEN 'Beyond the Golden Portal'
        WHEN 'livemagic' THEN 'Where Fire Meets the Stars'
        WHEN 'lounge' THEN 'Berlin Underground Spirit'
        WHEN 'arquipelago' THEN 'Tropical Bioluminescent Paradise'
        WHEN 'noahsark' THEN 'A Fairy Tale Journey'
        WHEN 'jazzclub' THEN 'Step Back to the 1920s'
        WHEN 'chiringuito' THEN 'Endless Summer Vibes'
        WHEN 'tributestage' THEN 'Legends Never Die'
    END,
    CASE l.slug
        WHEN 'dreamerscave' THEN 'The original venue where it all began. An immersive hexagonal architecture creates a cosmic atmosphere where technology and art merge seamlessly.'
        WHEN 'dreamerscave2' THEN 'A futuristic urban loft with neon accents and cutting-edge visual technology. The perfect space for electronic music and modern performances.'
        WHEN 'dreamvision' THEN 'Our flagship 360-degree venue offering the most immersive visual experience in Second Life. Monumental scale meets explosive visuals.'
        WHEN 'evanescence' THEN 'A transcendent space where golden light flows through ethereal portals. Experience music in a realm between worlds.'
        WHEN 'livemagic' THEN 'A space station floating among the stars, where fire effects dance with cosmic energy. High-intensity performances welcome.'
        WHEN 'lounge' THEN 'Inspired by Berlin''s legendary underground clubs. Brutalist concrete meets vibrant neon in this intimate yet powerful space.'
        WHEN 'arquipelago' THEN 'An enchanted tropical island with bioluminescent vegetation. Nature and technology create an unforgettable atmosphere.'
        WHEN 'noahsark' THEN 'Set aboard a magical wooden ship, this venue brings fairy tale warmth to every performance. Cozy, intimate, enchanting.'
        WHEN 'jazzclub' THEN 'A tribute to the speakeasy era. Dim lights, rich wood, and the timeless atmosphere of 1920s jazz clubs.'
        WHEN 'chiringuito' THEN 'Your beachside escape with sunset views and summer energy. The perfect venue for laid-back performances.'
        WHEN 'tributestage' THEN 'A professional concert stage designed for tribute shows and rock performances. Full arena experience.'
    END,
    'Custom architecture designed for The Dreamer''s Cave',
    'Unique atmosphere enhanced by synchronized visual effects'
FROM locations l
ON DUPLICATE KEY UPDATE tagline = VALUES(tagline);

-- Default blog categories
INSERT INTO blog_categories (slug, sort_order) VALUES
('news', 1),
('events', 2),
('artists', 3),
('technology', 4),
('community', 5)
ON DUPLICATE KEY UPDATE slug = VALUES(slug);

-- Blog category translations (English)
INSERT INTO blog_category_translations (category_id, language, name, description)
SELECT bc.id, 'en',
    CASE bc.slug
        WHEN 'news' THEN 'News'
        WHEN 'events' THEN 'Events'
        WHEN 'artists' THEN 'Artists'
        WHEN 'technology' THEN 'Technology'
        WHEN 'community' THEN 'Community'
    END,
    CASE bc.slug
        WHEN 'news' THEN 'Latest news and announcements'
        WHEN 'events' THEN 'Event highlights and recaps'
        WHEN 'artists' THEN 'Artist spotlights and interviews'
        WHEN 'technology' THEN 'Behind the scenes of our visual tech'
        WHEN 'community' THEN 'Community stories and features'
    END
FROM blog_categories bc
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Register this migration
INSERT INTO schema_migrations (version, name) VALUES ('001', 'initial')
ON DUPLICATE KEY UPDATE executed_at = CURRENT_TIMESTAMP;
