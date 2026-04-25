"""
Locations endpoints under /api/locations.

GET /api/locations            -- list active locations (or all with ?include_inactive=true)
GET /api/locations/<slug>     -- single location by slug

Locale resolution: reads Accept-Language header (en|it|fr|es), defaults to 'en'.
Translation fallback chain: requested locale -> en -> base table value.

Response shape: every endpoint goes through `app.utils.responses.success`,
which wraps the payload as { "success": true, "data": <payload> }. The
frontend BFF adapter unwraps `.data` before returning to the client.

Field mapping (DB -> frontend type contract):
    mood_category enum   -> mood string ('cosmic_tech'->'cosmic',
                            'warm_intimate'->'warm', 'hybrid'->'hybrid')
    hero_image_url       -> hero_image
    name (translated)    -> name
    description (translated) -> description

Sort: sort_order ASC, then name ASC.
"""
from flask import Blueprint, request

from app.utils.db import fetch_all, fetch_one
from app.utils.responses import not_found, success

bp = Blueprint("locations", __name__, url_prefix="/locations")


# ---------------------------------------------------------------- helpers


_SUPPORTED_LANGS = ("en", "it", "fr", "es")

_MOOD_MAP = {
    "cosmic_tech": "cosmic",
    "warm_intimate": "warm",
    "hybrid": "hybrid",
}


def _resolve_language(req) -> str:
    """Pick the best-supported locale from Accept-Language; default 'en'."""
    accept = req.headers.get("Accept-Language", "en")
    primary = accept.split(",")[0].split("-")[0].strip().lower()
    return primary if primary in _SUPPORTED_LANGS else "en"


def _serialize_location(row: dict) -> dict:
    """
    Map a JOINed DB row to the frontend Location interface.

    Row is expected to contain (from the SQL below):
        id, slug, capacity, mood_category, hero_image_url, created_at,
        base_name, t_name, en_name,
        base_description (None - locations have no base description),
        t_description, en_description
    """
    name = row.get("t_name") or row.get("en_name") or row.get("base_name")
    description = row.get("t_description") or row.get("en_description")
    mood = _MOOD_MAP.get(row.get("mood_category"), row.get("mood_category"))

    created_at = row.get("created_at")
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": name,
        "mood": mood,
        "capacity": row.get("capacity") or 0,
        "hero_image": row.get("hero_image_url"),
        "description": description,
        "created_at": created_at.isoformat() if created_at else None,
    }


# Shared SELECT clause -- two LEFT JOINs against location_translations:
#   t = requested locale, en = English fallback
_LOCATIONS_SELECT = """
    SELECT
        l.id,
        l.slug,
        l.capacity,
        l.mood_category,
        l.hero_image_url,
        l.is_active,
        l.sort_order,
        l.created_at,
        l.name AS base_name,
        t.name AS t_name,
        t.description AS t_description,
        en.name AS en_name,
        en.description AS en_description
    FROM locations l
    LEFT JOIN location_translations t
        ON t.location_id = l.id AND t.language = %s
    LEFT JOIN location_translations en
        ON en.location_id = l.id AND en.language = 'en'
"""


# ---------------------------------------------------------------- endpoints


@bp.route("", methods=["GET"])
def list_locations():
    """
    List locations.

    Query params:
        include_inactive (str): 'true' to include is_active=0 rows; default false.

    Response 200: { success: true, data: [<Location>, ...] }
    """
    lang = _resolve_language(request)
    include_inactive = request.args.get("include_inactive", "").lower() == "true"

    if include_inactive:
        sql = _LOCATIONS_SELECT + " ORDER BY l.sort_order ASC, l.name ASC"
        rows = fetch_all(sql, (lang,))
    else:
        sql = (
            _LOCATIONS_SELECT
            + " WHERE l.is_active = 1 ORDER BY l.sort_order ASC, l.name ASC"
        )
        rows = fetch_all(sql, (lang,))

    return success([_serialize_location(r) for r in rows])


@bp.route("/<slug>", methods=["GET"])
def get_location(slug: str):
    """
    Get a single location by slug.

    Returns 404 if the slug doesn't exist OR if the location is inactive
    (inactive locations are not browsable -- admin would use a separate
    admin endpoint, not this public read endpoint).

    Response 200: { success: true, data: <Location> }
    Response 404: { success: false, error: "Location not found" }
    """
    lang = _resolve_language(request)
    sql = _LOCATIONS_SELECT + " WHERE l.slug = %s AND l.is_active = 1 LIMIT 1"
    row = fetch_one(sql, (lang, slug))
    if row is None:
        return not_found("Location not found")
    return success(_serialize_location(row))
