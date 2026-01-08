"""
Flask application configuration.
Loads settings from environment variables with sensible defaults.
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

    # Database
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'tdcweb')
    DB_USER = os.environ.get('DB_USER', 'tdcweb')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'tdcweb')
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))

    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@thedreamerscave.club')

    # OAuth - Google
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # OAuth - Discord
    DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
    DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')

    # OAuth - Facebook
    FACEBOOK_CLIENT_ID = os.environ.get('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.environ.get('FACEBOOK_CLIENT_SECRET')

    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS_PATH = os.environ.get('GOOGLE_CALENDAR_CREDENTIALS_PATH')
    GOOGLE_CALENDAR_INTERNAL_ID = os.environ.get('GOOGLE_CALENDAR_INTERNAL_ID')
    GOOGLE_CALENDAR_PUBLIC_ID = os.environ.get('GOOGLE_CALENDAR_PUBLIC_ID')

    # Facebook Integration
    FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN')
    FACEBOOK_PAGE_ID = os.environ.get('FACEBOOK_PAGE_ID')
    FACEBOOK_GROUP_ID = os.environ.get('FACEBOOK_GROUP_ID')

    # Patreon
    PATREON_CLIENT_ID = os.environ.get('PATREON_CLIENT_ID')
    PATREON_CLIENT_SECRET = os.environ.get('PATREON_CLIENT_SECRET')
    PATREON_CREATOR_ACCESS_TOKEN = os.environ.get('PATREON_CREATOR_ACCESS_TOKEN')
    PATREON_WEBHOOK_SECRET = os.environ.get('PATREON_WEBHOOK_SECRET')

    # File Storage
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/data1/tdcweb/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

    # Application
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'en')
    SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'en,it,fr,es').split(',')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    # App version
    APP_VERSION = '0.1.0'


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True
    DB_NAME = os.environ.get('DB_NAME_TEST', 'tdcweb_test')


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
