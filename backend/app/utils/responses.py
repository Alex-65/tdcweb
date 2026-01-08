"""
Standard API response helpers.
All endpoints MUST use these for consistent response format.

Response Format:
    Success: {"success": true, "data": {...}, "meta": {...}}
    Error:   {"success": false, "error": "...", "errors": {...}}
"""
from flask import jsonify
from typing import Any, Optional


def success(data: Any = None, meta: dict = None, status_code: int = 200):
    """
    Return success response.

    Args:
        data: Response payload (any JSON-serializable type)
        meta: Optional metadata (pagination, etc.)
        status_code: HTTP status code (default: 200)

    Returns:
        tuple: (Response, status_code)

    Example:
        return success({"user": user_dict})
        return success(items, meta={"pagination": {...}})
    """
    response = {"success": True, "data": data}
    if meta:
        response["meta"] = meta
    return jsonify(response), status_code


def error(message: str, status_code: int = 400, errors: dict = None):
    """
    Return error response.

    Args:
        message: Human-readable error message
        status_code: HTTP status code (default: 400)
        errors: Optional field-level errors for validation

    Returns:
        tuple: (Response, status_code)

    Example:
        return error("Invalid request")
        return error("Validation failed", 400, {"email": ["Invalid format"]})
    """
    response = {"success": False, "error": message}
    if errors:
        response["errors"] = errors
    return jsonify(response), status_code


def created(data: Any = None):
    """
    Return 201 Created response.

    Args:
        data: Created resource data

    Returns:
        tuple: (Response, 201)
    """
    return success(data, status_code=201)


def no_content():
    """
    Return 204 No Content response.

    Returns:
        tuple: ('', 204)
    """
    return '', 204


def paginated(items: list, page: int, per_page: int, total: int):
    """
    Return paginated response with meta.

    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        per_page: Items per page
        total: Total items count

    Returns:
        tuple: (Response with pagination meta, 200)

    Example:
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
                "pages": (total + per_page - 1) // per_page if per_page > 0 else 0
            }
        }
    )


# ============================================
# Common error responses
# ============================================

def not_found(message: str = "Resource not found"):
    """
    Return 404 Not Found response.

    Args:
        message: Error message (default: "Resource not found")

    Returns:
        tuple: (Response, 404)
    """
    return error(message, 404)


def unauthorized(message: str = "Unauthorized"):
    """
    Return 401 Unauthorized response.

    Args:
        message: Error message (default: "Unauthorized")

    Returns:
        tuple: (Response, 401)
    """
    return error(message, 401)


def forbidden(message: str = "Forbidden"):
    """
    Return 403 Forbidden response.

    Args:
        message: Error message (default: "Forbidden")

    Returns:
        tuple: (Response, 403)
    """
    return error(message, 403)


def bad_request(message: str, errors: dict = None):
    """
    Return 400 Bad Request response.

    Args:
        message: Error message
        errors: Optional field-level validation errors

    Returns:
        tuple: (Response, 400)
    """
    return error(message, 400, errors)


def server_error(message: str = "Internal server error"):
    """
    Return 500 Internal Server Error response.

    Args:
        message: Error message (default: "Internal server error")

    Returns:
        tuple: (Response, 500)
    """
    return error(message, 500)


def conflict(message: str = "Resource conflict"):
    """
    Return 409 Conflict response.

    Args:
        message: Error message (default: "Resource conflict")

    Returns:
        tuple: (Response, 409)
    """
    return error(message, 409)


def unprocessable_entity(message: str, errors: dict = None):
    """
    Return 422 Unprocessable Entity response.

    Args:
        message: Error message
        errors: Optional field-level validation errors

    Returns:
        tuple: (Response, 422)
    """
    return error(message, 422, errors)
