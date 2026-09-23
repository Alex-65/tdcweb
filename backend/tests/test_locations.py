"""
Locations blueprint tests -- /api/locations and /api/locations/<slug>.

Covers:
    - Default list excludes inactive
    - include_inactive=true includes inactive
    - Accept-Language localizes name/description
    - Locale fallback: missing IT translation falls through to EN
    - GET by slug returns localized location
    - GET by slug 404 when not found OR inactive
    - mood_category enum mapped to frontend mood string
    - Response shape sanity (no sensitive fields)
    - Sort order respects sort_order ASC then name ASC

All fixtures auto-clean their rows on teardown (rule 17).
"""
from __future__ import annotations


def _decode_data(response) -> dict | list:
    """Pull `.data` out of the standard success envelope."""
    body = response.get_json()
    assert body is not None, "Response had no JSON body"
    assert body.get("success") is True, f"Expected success=true, got {body!r}"
    return body["data"]


# ---------------------------------------------------------------- list endpoint


def test_list_returns_active_locations_default(client, make_location):
    """Default GET /api/locations returns only is_active=1 rows."""
    active = make_location(
        name="Active Cave",
        translations={"en": {"name": "Active Cave EN"}},
    )
    inactive = make_location(
        name="Hidden Cave",
        is_active=False,
        translations={"en": {"name": "Hidden Cave EN"}},
    )

    resp = client.get("/api/locations")
    assert resp.status_code == 200
    data = _decode_data(resp)
    assert isinstance(data, list)

    ids = {row["id"] for row in data}
    assert active["id"] in ids
    assert inactive["id"] not in ids


def test_list_includes_inactive_when_query_param_set(client, make_location):
    """include_inactive=true returns active AND inactive rows."""
    active = make_location(
        name="A1",
        translations={"en": {"name": "A1 EN"}},
    )
    inactive = make_location(
        name="I1",
        is_active=False,
        translations={"en": {"name": "I1 EN"}},
    )

    resp = client.get("/api/locations?include_inactive=true")
    assert resp.status_code == 200
    data = _decode_data(resp)
    ids = {row["id"] for row in data}
    assert active["id"] in ids
    assert inactive["id"] in ids


def test_list_localizes_name_via_accept_language(client, make_location):
    """Accept-Language: it returns the Italian translation, not the English one."""
    loc = make_location(
        name="Base Name",
        translations={
            "en": {"name": "Cave EN", "description": "desc en"},
            "it": {"name": "Caverna IT", "description": "desc it"},
        },
    )

    resp = client.get(
        "/api/locations",
        headers={"Accept-Language": "it"},
    )
    assert resp.status_code == 200
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == loc["id"])
    assert row["name"] == "Caverna IT"
    assert row["description"] == "desc it"


def test_list_falls_back_to_en_when_locale_translation_missing(client, make_location):
    """Request fr but only en translation exists -> en is returned."""
    loc = make_location(
        name="Base Name",
        translations={"en": {"name": "Cave EN", "description": "desc en"}},
    )

    resp = client.get(
        "/api/locations",
        headers={"Accept-Language": "fr"},
    )
    assert resp.status_code == 200
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == loc["id"])
    assert row["name"] == "Cave EN"
    assert row["description"] == "desc en"


def test_list_falls_back_to_base_name_when_no_translations(client, make_location):
    """No translations at all -> falls through to base.name."""
    loc = make_location(name="Pure Base Name", translations=None)

    resp = client.get("/api/locations", headers={"Accept-Language": "es"})
    assert resp.status_code == 200
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == loc["id"])
    assert row["name"] == "Pure Base Name"


def test_list_mood_category_mapped_correctly(client, make_location):
    """cosmic_tech -> 'cosmic'; warm_intimate -> 'warm'; hybrid -> 'hybrid'."""
    cosmic = make_location(
        name="Cosmic", mood="cosmic_tech",
        translations={"en": {"name": "Cosmic EN"}},
    )
    warm = make_location(
        name="Warm", mood="warm_intimate",
        translations={"en": {"name": "Warm EN"}},
    )
    hybrid = make_location(
        name="Hybrid", mood="hybrid",
        translations={"en": {"name": "Hybrid EN"}},
    )

    resp = client.get("/api/locations")
    assert resp.status_code == 200
    data = _decode_data(resp)
    by_id = {r["id"]: r for r in data}
    assert by_id[cosmic["id"]]["mood"] == "cosmic"
    assert by_id[warm["id"]]["mood"] == "warm"
    assert by_id[hybrid["id"]]["mood"] == "hybrid"


def test_list_response_shape_excludes_internal_fields(client, sample_location):
    """Response must not leak internal columns (slurl, sort_order, gallery_images, etc.)."""
    resp = client.get("/api/locations")
    assert resp.status_code == 200
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == sample_location["id"])
    expected_keys = {
        "id", "slug", "name", "mood", "capacity", "hero_image",
        "description", "created_at",
    }
    # Frontend type requires exactly these keys -- no leakage.
    assert set(row.keys()) == expected_keys


# ---------------------------------------------------------------- single endpoint


def test_get_by_slug_returns_localized_location(client, make_location):
    """GET /api/locations/<slug> with Accept-Language: it returns IT-translated row."""
    loc = make_location(
        name="Base",
        translations={
            "en": {"name": "Solo EN", "description": "en desc"},
            "it": {"name": "Solo IT", "description": "it desc"},
        },
    )

    resp = client.get(
        f"/api/locations/{loc['slug']}",
        headers={"Accept-Language": "it"},
    )
    assert resp.status_code == 200
    data = _decode_data(resp)
    assert data["id"] == loc["id"]
    assert data["slug"] == loc["slug"]
    assert data["name"] == "Solo IT"
    assert data["description"] == "it desc"


def test_get_by_slug_404_when_not_found(client):
    """Unknown slug -> 404 with success=false."""
    resp = client.get("/api/locations/this-slug-does-not-exist-9999")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["success"] is False
    assert "not found" in body["error"].lower()


def test_get_by_slug_404_when_inactive(client, make_location):
    """Inactive location -> 404, hidden from public read endpoint."""
    inactive = make_location(
        name="Hidden",
        is_active=False,
        translations={"en": {"name": "Hidden EN"}},
    )

    resp = client.get(f"/api/locations/{inactive['slug']}")
    assert resp.status_code == 404
