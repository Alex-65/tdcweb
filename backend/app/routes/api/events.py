"""
Events endpoints under /api/events.

GET /api/events    -- list published events (default: upcoming only)

Locale resolution: reads Accept-Language (en|it|fr|es), defaults to 'en'.
Translation fallback: requested locale -> en. Events have NO base title;
title lives ONLY in event_translations. If even the en row is missing
(should not happen in practice), title falls through as None and the
client renders an empty string.

Response shape: { "success": true, "data": [<Event>, ...] }. The BFF
adapter unwraps `.data` before returning to the client.

Field mapping (DB -> frontend type contract):
    event_translations.title        -> title
    start_time                      -> starts_at
    end_time                        -> ends_at
    poster_image_url                -> poster_image
    location_id (NULL allowed in DB) -> 0 (frontend type is non-nullable)

Status (computed):
    NOW() < start_time              -> 'scheduled'
    start_time <= NOW() <= end_time -> 'live'
    end_time < NOW()                -> 'ended'

Filters:
    upcoming=true|false  (default true) -- end_time >= NOW()
    location_id=<int>                   -- filter by venue
    limit=<int>          (default 50, max 200)

Sort: start_time ASC.
Only is_published=1 rows are returned (admin endpoint would include drafts).
"""
from datetime import datetime

from flask import Blueprint, request

from app.utils.db import fetch_all
from app.utils.responses import success

bp = Blueprint("events", __name__, url_prefix="/events")


# ---------------------------------------------------------------- helpers


_SUPPORTED_LANGS = ("en", "it", "fr", "es")

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200


def _resolve_language(req) -> str:
    """Pick the best-supported locale from Accept-Language; default 'en'."""
    accept = req.headers.get("Accept-Language", "en")
    primary = accept.split(",")[0].split("-")[0].strip().lower()
    return primary if primary in _SUPPORTED_LANGS else "en"


def _parse_int(raw: str | None, default: int, minimum: int = 1, maximum: int | None = None) -> int:
    """Best-effort int parser with clamping. Falls back to default on garbage input."""
    if raw is None or raw == "":
        return default
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return default
    if n < minimum:
        n = minimum
    if maximum is not None and n > maximum:
        n = maximum
    return n


def _compute_status(start: datetime | None, end: datetime | None, now: datetime) -> str:
    """Return 'scheduled' | 'live' | 'ended' based on start/end vs now.

    Defensive: if either bound is missing, treat as 'scheduled' (least-bad
    default for the frontend, which lists upcoming events first).
    """
    if start is None or end is None:
        return "scheduled"
    if now < start:
        return "scheduled"
    if start <= now <= end:
        return "live"
    return "ended"


def _serialize_event(row: dict, now: datetime) -> dict:
    """
    Map a JOINed DB row to the frontend Event interface.

    Row contains: id, slug, location_id, start_time, end_time,
    poster_image_url, t_title, t_description, en_title, en_description.
    """
    title = row.get("t_title") or row.get("en_title")
    description = row.get("t_description") or row.get("en_description")

    start = row.get("start_time")
    end = row.get("end_time")

    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": title,
        # NOTE: TS frontend type marks location_id as non-nullable number.
        # DB allows NULL (location-less events). We coerce NULL -> 0 to
        # respect the type, and flag this as TECH_DEBT for type alignment.
        "location_id": row.get("location_id") if row.get("location_id") is not None else 0,
        "starts_at": start.isoformat() if start else None,
        "ends_at": end.isoformat() if end else None,
        "status": _compute_status(start, end, now),
        "description": description,
        "poster_image": row.get("poster_image_url"),
    }


_EVENTS_SELECT = """
    SELECT
        e.id,
        e.slug,
        e.location_id,
        e.start_time,
        e.end_time,
        e.poster_image_url,
        e.is_published,
        t.title AS t_title,
        t.description AS t_description,
        en.title AS en_title,
        en.description AS en_description
    FROM events e
    LEFT JOIN event_translations t
        ON t.event_id = e.id AND t.language = %s
    LEFT JOIN event_translations en
        ON en.event_id = e.id AND en.language = 'en'
"""


# ---------------------------------------------------------------- endpoints


@bp.route("", methods=["GET"])
def list_events():
    """
    List published events.

    Query params:
        upcoming=true|false   (default true)  -- end_time >= NOW()
        location_id=<int>     (optional)      -- filter by venue
        limit=<int>           (default 50, max 200)

    Response 200: { success: true, data: [<Event>, ...] }
    """
    lang = _resolve_language(request)
    upcoming_raw = request.args.get("upcoming", "true").lower()
    upcoming = upcoming_raw != "false"  # default true; only 'false' disables filter
    location_id = _parse_int(request.args.get("location_id"), default=0, minimum=0)
    limit = _parse_int(
        request.args.get("limit"), default=_DEFAULT_LIMIT, minimum=1, maximum=_MAX_LIMIT
    )

    where_clauses = ["e.is_published = 1"]
    params: list = [lang]

    if upcoming:
        where_clauses.append("e.end_time >= NOW()")
    if location_id > 0:
        where_clauses.append("e.location_id = %s")
        params.append(location_id)

    sql = (
        _EVENTS_SELECT
        + " WHERE "
        + " AND ".join(where_clauses)
        + " ORDER BY e.start_time ASC LIMIT %s"
    )
    params.append(limit)

    rows = fetch_all(sql, tuple(params))
    now = datetime.now()  # naive, matches DATETIME column comparison
    return success([_serialize_event(r, now) for r in rows])
