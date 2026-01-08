"""
Public API routes blueprint.
All endpoints under /api/v1/
"""
from flask import Blueprint

# Main API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def register_api_routes(app):
    """
    Register all API route blueprints.

    Args:
        app: Flask application instance
    """
    from app.routes.api import health

    # Register sub-blueprints
    api_bp.register_blueprint(health.bp)

    # Register main API blueprint with app
    app.register_blueprint(api_bp)
