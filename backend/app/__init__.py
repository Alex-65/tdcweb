"""
Flask application factory for The Dreamer's Cave.
"""
from flask import Flask, jsonify
from flask_cors import CORS
import logging

from app.config import get_config
from app.utils.db import init_pool, close_connection


def create_app(config_class=None):
    """
    Flask application factory.

    Args:
        config_class: Configuration class (default: auto-detect from FLASK_ENV)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if app.config.get('DEBUG') else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting TDC Backend v{app.config.get('APP_VERSION', 'unknown')}")

    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://localhost:3000",
                       "https://thedreamerscave.club", "https://www.thedreamerscave.club"],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True
        }
    })

    # Initialize database pool
    with app.app_context():
        try:
            init_pool(app)
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't raise - allow app to start even if DB is unavailable
            # Health check will report the issue

    # Register teardown for database connections
    app.teardown_appcontext(close_connection)

    # Register blueprints
    from app.routes.api import register_api_routes
    register_api_routes(app)

    # Register error handlers
    register_error_handlers(app)

    logger.info("TDC Backend initialized successfully")
    return app


def register_error_handlers(app):
    """
    Register global error handlers.

    Args:
        app: Flask application instance
    """
    from app.utils.responses import error, not_found, server_error

    @app.errorhandler(400)
    def handle_400(e):
        return error(str(e.description) if hasattr(e, 'description') else "Bad request", 400)

    @app.errorhandler(401)
    def handle_401(e):
        return error("Unauthorized", 401)

    @app.errorhandler(403)
    def handle_403(e):
        return error("Forbidden", 403)

    @app.errorhandler(404)
    def handle_404(e):
        return not_found("Resource not found")

    @app.errorhandler(405)
    def handle_405(e):
        return error("Method not allowed", 405)

    @app.errorhandler(500)
    def handle_500(e):
        app.logger.error(f"Internal server error: {e}")
        return server_error("Internal server error")

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.exception(f"Unhandled exception: {e}")
        return server_error("An unexpected error occurred")
