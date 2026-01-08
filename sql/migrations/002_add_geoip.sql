-- ============================================
-- MIGRATION 002: GeoIP Support
-- THE DREAMER'S CAVE - DATABASE
-- Version: 1.0.1
-- Date: January 2025
-- Description: Add GeoIP Lite 2 support for geolocation and language detection
-- ============================================

-- Run with: mysql -u tdcweb -p tdcweb < 002_add_geoip.sql

SET NAMES utf8mb4;

-- ============================================
-- ADD COLUMNS TO USERS TABLE
-- ============================================

-- Add country_code for user's detected country
ALTER TABLE users
ADD COLUMN country_code CHAR(2) NULL AFTER language,
ADD COLUMN detected_language VARCHAR(10) NULL AFTER country_code,
ADD INDEX idx_country_code (country_code);

-- ============================================
-- CREATE ACCESS_LOGS TABLE
-- For tracking requests with GeoIP data
-- ============================================

CREATE TABLE IF NOT EXISTS access_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(45) NOT NULL,              -- IPv4 or IPv6
    country_code CHAR(2),
    city VARCHAR(100),
    user_id INT NULL,                     -- NULL for anonymous visitors
    endpoint VARCHAR(255) NOT NULL,       -- API endpoint or page path
    method VARCHAR(10) DEFAULT 'GET',     -- HTTP method
    status_code SMALLINT,                 -- HTTP response status
    user_agent TEXT,
    referer VARCHAR(500),
    response_time_ms INT,                 -- Response time in milliseconds
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_ip (ip),
    INDEX idx_country_code (country_code),
    INDEX idx_user_id (user_id),
    INDEX idx_endpoint (endpoint),
    INDEX idx_created_at (created_at),
    INDEX idx_country_created (country_code, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- CREATE COUNTRY_LANGUAGE_MAP TABLE
-- Maps country codes to default languages
-- ============================================

CREATE TABLE IF NOT EXISTS country_language_map (
    country_code CHAR(2) PRIMARY KEY,
    default_language VARCHAR(10) NOT NULL,
    country_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- POPULATE COUNTRY_LANGUAGE_MAP
-- Primary language mappings for supported languages (en, it, fr, es)
-- ============================================

INSERT INTO country_language_map (country_code, default_language, country_name) VALUES
-- Italian (it)
('IT', 'it', 'Italy'),
('SM', 'it', 'San Marino'),
('VA', 'it', 'Vatican City'),
('CH', 'it', 'Switzerland'),  -- Italian is official, could also be fr/de

-- French (fr)
('FR', 'fr', 'France'),
('BE', 'fr', 'Belgium'),
('LU', 'fr', 'Luxembourg'),
('MC', 'fr', 'Monaco'),
('SN', 'fr', 'Senegal'),
('CI', 'fr', 'Ivory Coast'),
('ML', 'fr', 'Mali'),
('BF', 'fr', 'Burkina Faso'),
('NE', 'fr', 'Niger'),
('TG', 'fr', 'Togo'),
('BJ', 'fr', 'Benin'),
('GA', 'fr', 'Gabon'),
('CG', 'fr', 'Republic of the Congo'),
('CD', 'fr', 'Democratic Republic of the Congo'),
('CM', 'fr', 'Cameroon'),
('MG', 'fr', 'Madagascar'),
('HT', 'fr', 'Haiti'),
('RE', 'fr', 'Réunion'),
('MQ', 'fr', 'Martinique'),
('GP', 'fr', 'Guadeloupe'),
('GF', 'fr', 'French Guiana'),
('PF', 'fr', 'French Polynesia'),
('NC', 'fr', 'New Caledonia'),

-- Spanish (es)
('ES', 'es', 'Spain'),
('MX', 'es', 'Mexico'),
('AR', 'es', 'Argentina'),
('CO', 'es', 'Colombia'),
('PE', 'es', 'Peru'),
('VE', 'es', 'Venezuela'),
('CL', 'es', 'Chile'),
('EC', 'es', 'Ecuador'),
('GT', 'es', 'Guatemala'),
('CU', 'es', 'Cuba'),
('BO', 'es', 'Bolivia'),
('DO', 'es', 'Dominican Republic'),
('HN', 'es', 'Honduras'),
('PY', 'es', 'Paraguay'),
('SV', 'es', 'El Salvador'),
('NI', 'es', 'Nicaragua'),
('CR', 'es', 'Costa Rica'),
('PA', 'es', 'Panama'),
('UY', 'es', 'Uruguay'),
('PR', 'es', 'Puerto Rico'),
('GQ', 'es', 'Equatorial Guinea'),

-- English (en) - Primary English-speaking countries
('US', 'en', 'United States'),
('GB', 'en', 'United Kingdom'),
('CA', 'en', 'Canada'),
('AU', 'en', 'Australia'),
('NZ', 'en', 'New Zealand'),
('IE', 'en', 'Ireland'),
('ZA', 'en', 'South Africa'),
('JM', 'en', 'Jamaica'),
('TT', 'en', 'Trinidad and Tobago'),
('BB', 'en', 'Barbados'),
('BS', 'en', 'Bahamas'),
('GY', 'en', 'Guyana'),
('BZ', 'en', 'Belize'),
('MT', 'en', 'Malta'),
('SG', 'en', 'Singapore'),
('PH', 'en', 'Philippines'),
('IN', 'en', 'India'),
('PK', 'en', 'Pakistan'),
('NG', 'en', 'Nigeria'),
('GH', 'en', 'Ghana'),
('KE', 'en', 'Kenya'),
('UG', 'en', 'Uganda'),
('TZ', 'en', 'Tanzania'),
('ZW', 'en', 'Zimbabwe'),
('ZM', 'en', 'Zambia'),
('BW', 'en', 'Botswana'),
('MW', 'en', 'Malawi'),
('NA', 'en', 'Namibia'),
('FJ', 'en', 'Fiji'),
('HK', 'en', 'Hong Kong'),
('MY', 'en', 'Malaysia'),

-- English fallback for other European countries
('DE', 'en', 'Germany'),
('NL', 'en', 'Netherlands'),
('SE', 'en', 'Sweden'),
('NO', 'en', 'Norway'),
('DK', 'en', 'Denmark'),
('FI', 'en', 'Finland'),
('AT', 'en', 'Austria'),
('PL', 'en', 'Poland'),
('CZ', 'en', 'Czech Republic'),
('HU', 'en', 'Hungary'),
('RO', 'en', 'Romania'),
('BG', 'en', 'Bulgaria'),
('GR', 'en', 'Greece'),
('PT', 'en', 'Portugal'),
('SK', 'en', 'Slovakia'),
('HR', 'en', 'Croatia'),
('SI', 'en', 'Slovenia'),
('RS', 'en', 'Serbia'),
('BA', 'en', 'Bosnia and Herzegovina'),
('AL', 'en', 'Albania'),
('MK', 'en', 'North Macedonia'),
('ME', 'en', 'Montenegro'),
('XK', 'en', 'Kosovo'),
('EE', 'en', 'Estonia'),
('LV', 'en', 'Latvia'),
('LT', 'en', 'Lithuania'),
('UA', 'en', 'Ukraine'),
('BY', 'en', 'Belarus'),
('MD', 'en', 'Moldova'),
('RU', 'en', 'Russia'),

-- English fallback for Asian countries
('JP', 'en', 'Japan'),
('KR', 'en', 'South Korea'),
('CN', 'en', 'China'),
('TW', 'en', 'Taiwan'),
('TH', 'en', 'Thailand'),
('VN', 'en', 'Vietnam'),
('ID', 'en', 'Indonesia'),
('BD', 'en', 'Bangladesh'),
('LK', 'en', 'Sri Lanka'),
('NP', 'en', 'Nepal'),
('MM', 'en', 'Myanmar'),
('KH', 'en', 'Cambodia'),
('LA', 'en', 'Laos'),

-- English fallback for Middle East
('IL', 'en', 'Israel'),
('AE', 'en', 'United Arab Emirates'),
('SA', 'en', 'Saudi Arabia'),
('QA', 'en', 'Qatar'),
('KW', 'en', 'Kuwait'),
('BH', 'en', 'Bahrain'),
('OM', 'en', 'Oman'),
('JO', 'en', 'Jordan'),
('LB', 'en', 'Lebanon'),
('TR', 'en', 'Turkey'),
('EG', 'en', 'Egypt'),
('MA', 'en', 'Morocco'),
('DZ', 'en', 'Algeria'),
('TN', 'en', 'Tunisia'),

-- English fallback for South America (non-Spanish)
('BR', 'en', 'Brazil'),
('SR', 'en', 'Suriname')

ON DUPLICATE KEY UPDATE default_language = VALUES(default_language);

-- ============================================
-- Record migration
-- ============================================

INSERT INTO schema_migrations (version, name) VALUES ('002', 'add_geoip')
ON DUPLICATE KEY UPDATE executed_at = CURRENT_TIMESTAMP;
