"""
Health check endpoints for monitoring and load balancer health checks.
"""
from flask import Blueprint
from datetime import datetime, timezone
from app.config import Config
from app.utils.responses import success, error
from app.utils.db import test_connection

bp = Blueprint('health', __name__)


@bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.

    Returns:
        JSON with status, version, and timestamp

    Example Response:
        {
            "success": true,
            "data": {
                "status": "ok",
                "version": "0.1.0",
                "timestamp": "2025-01-08T20:00:00.000Z"
            }
        }
    """
    return success({
        "status": "ok",
        "version": Config.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@bp.route('/health/db', methods=['GET'])
def health_check_db():
    """
    Database connectivity health check.

    Returns:
        JSON with database connection status

    Example Response (success):
        {
            "success": true,
            "data": {
                "status": "ok",
                "database": "connected",
                "timestamp": "2025-01-08T20:00:00.000Z"
            }
        }

    Example Response (failure):
        {
            "success": false,
            "error": "Database connection failed"
        }
    """
    db_ok = test_connection()

    if db_ok:
        return success({
            "status": "ok",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        return error("Database connection failed", 503)


@bp.route('/health/full', methods=['GET'])
def health_check_full():
    """
    Full system health check including all dependencies.

    Returns:
        JSON with status of all system components

    Example Response:
        {
            "success": true,
            "data": {
                "status": "ok",
                "version": "0.1.0",
                "components": {
                    "database": "ok",
                    "redis": "ok"
                },
                "timestamp": "2025-01-08T20:00:00.000Z"
            }
        }
    """
    components = {
        "database": "ok" if test_connection() else "error"
    }

    # TODO: Add Redis health check when Celery is configured
    # components["redis"] = "ok" if redis_ok else "error"

    overall_status = "ok" if all(v == "ok" for v in components.values()) else "degraded"

    return success({
        "status": overall_status,
        "version": Config.APP_VERSION,
        "components": components,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
