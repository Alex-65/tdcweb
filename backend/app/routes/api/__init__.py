"""
Public API routes blueprint.
All endpoints under /api/

Note: prefix dropped from /api/v1/ to /api/ during Phase 4B.2 to align with
the architectural intent in spec / plan / CLAUDE.md / pdp-v3 (all reference
/api/auth/**, /api/revalidate, /api/** without versioning). Frontend BFF
(Phase 4 Tasks 4.1-4.2) calls Flask at /api/auth/* directly. Versioning is
deferred to a future phase if/when API surface needs explicit versioning.
"""
from flask import Blueprint

# Main API blueprint -- /api/ prefix matches frontend BFF + arch spec.
api_bp = Blueprint('api', __name__, url_prefix='/api')


def register_api_routes(app):
    """
    Register all API route blueprints.

    Args:
        app: Flask application instance
    """
    from app.routes.api import auth, events, health, locations

    # Register sub-blueprints
    api_bp.register_blueprint(health.bp)
    api_bp.register_blueprint(auth.bp)
    api_bp.register_blueprint(locations.bp)
    api_bp.register_blueprint(events.bp)

    # Register main API blueprint with app
    app.register_blueprint(api_bp)
