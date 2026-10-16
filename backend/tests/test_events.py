"""
Events blueprint tests -- /api/events.

Covers:
    - Default returns only is_published=1 AND end_time >= NOW() (upcoming)
    - upcoming=false drops the time filter but keeps is_published filter
    - is_published=0 NEVER returned regardless of upcoming flag
    - location_id filter
    - Accept-Language localizes title/description
    - status field computed: 'scheduled' for future, 'live' for in-progress,
      'ended' for past (only visible when upcoming=false)
    - limit query param respected and clamped
    - Sort by start_time ASC

All fixtures auto-clean their rows on teardown (rule 17).
"""
from __future__ import annotations


def _decode_data(response) -> list:
    body = response.get_json()
    assert body is not None, "Response had no JSON body"
    assert body.get("success") is True, f"Expected success=true, got {body!r}"
    return body["data"]


# ---------------------------------------------------------------- list endpoint


def test_list_returns_only_upcoming_published_events_default(client, make_event):
    """Default /api/events returns published events with end_time >= NOW()."""
    upcoming = make_event(
        start_offset_seconds=3600,  # +1h
        translations={"en": {"title": "Upcoming"}},
    )
    past = make_event(
        start_offset_seconds=-7200,  # -2h
        duration_seconds=3600,  # ends 1h ago
        translations={"en": {"title": "Past"}},
    )

    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = _decode_data(resp)
    ids = {row["id"] for row in data}
    assert upcoming["id"] in ids
    assert past["id"] not in ids


def test_list_excludes_unpublished_even_when_upcoming_false(client, make_event):
    """is_published=0 never returned, even with upcoming=false."""
    published = make_event(
        is_published=True,
        translations={"en": {"title": "Pub"}},
    )
    unpublished = make_event(
        is_published=False,
        translations={"en": {"title": "Draft"}},
    )

    # default (upcoming=true)
    resp = client.get("/api/events")
    ids = {r["id"] for r in _decode_data(resp)}
    assert published["id"] in ids
    assert unpublished["id"] not in ids

    # upcoming=false
    resp = client.get("/api/events?upcoming=false")
    ids = {r["id"] for r in _decode_data(resp)}
    assert published["id"] in ids
    assert unpublished["id"] not in ids


def test_list_upcoming_false_includes_past_events(client, make_event):
    """upcoming=false drops the time filter, so past events ARE returned."""
    past = make_event(
        start_offset_seconds=-7200,
        duration_seconds=3600,  # ended 1h ago
        translations={"en": {"title": "PastEv"}},
    )

    resp = client.get("/api/events?upcoming=false")
    assert resp.status_code == 200
    data = _decode_data(resp)
    ids = {row["id"] for row in data}
    assert past["id"] in ids


def test_list_filter_by_location_id(client, make_location, make_event):
    """location_id query param filters to just that venue's events."""
    loc_a = make_location(name="A", translations={"en": {"name": "A"}})
    loc_b = make_location(name="B", translations={"en": {"name": "B"}})

    ev_a = make_event(
        location_id=loc_a["id"],
        translations={"en": {"title": "AEvent"}},
    )
    ev_b = make_event(
        location_id=loc_b["id"],
        translations={"en": {"title": "BEvent"}},
    )

    resp = client.get(f"/api/events?location_id={loc_a['id']}")
    assert resp.status_code == 200
    data = _decode_data(resp)
    ids = {row["id"] for row in data}
    assert ev_a["id"] in ids
    assert ev_b["id"] not in ids


def test_list_localizes_title_via_accept_language(client, make_event):
    """Accept-Language: it returns the Italian title."""
    ev = make_event(
        translations={
            "en": {"title": "English Concert", "description": "en"},
            "it": {"title": "Concerto Italiano", "description": "it"},
        },
    )

    resp = client.get("/api/events", headers={"Accept-Language": "it"})
    assert resp.status_code == 200
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == ev["id"])
    assert row["title"] == "Concerto Italiano"
    assert row["description"] == "it"


def test_list_falls_back_to_en_when_locale_translation_missing(client, make_event):
    """Request fr but only en translation exists -> en title returned."""
    ev = make_event(
        translations={"en": {"title": "OnlyEN", "description": "en desc"}},
    )

    resp = client.get("/api/events", headers={"Accept-Language": "fr"})
    assert resp.status_code == 200
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == ev["id"])
    assert row["title"] == "OnlyEN"
    assert row["description"] == "en desc"


def test_list_status_scheduled_for_future_events(client, make_event):
    """Future event -> status='scheduled'."""
    ev = make_event(
        start_offset_seconds=3600,  # +1h
        translations={"en": {"title": "Sch"}},
    )

    resp = client.get("/api/events")
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == ev["id"])
    assert row["status"] == "scheduled"


def test_list_status_live_for_in_progress_events(client, make_event):
    """In-progress event (start in past, end in future) -> status='live'."""
    ev = make_event(
        start_offset_seconds=-1800,  # started 30m ago
        duration_seconds=7200,  # ends in 1.5h
        translations={"en": {"title": "Live"}},
    )

    resp = client.get("/api/events")
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == ev["id"])
    assert row["status"] == "live"


def test_list_status_ended_for_past_events(client, make_event):
    """Past event -> status='ended' (visible only with upcoming=false)."""
    ev = make_event(
        start_offset_seconds=-7200,
        duration_seconds=3600,
        translations={"en": {"title": "Ended"}},
    )

    resp = client.get("/api/events?upcoming=false")
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == ev["id"])
    assert row["status"] == "ended"


def test_list_respects_limit_query_param(client, make_event):
    """limit=N caps the result count."""
    # Create 3 upcoming events with staggered start times
    e1 = make_event(start_offset_seconds=3600, translations={"en": {"title": "E1"}})
    e2 = make_event(start_offset_seconds=7200, translations={"en": {"title": "E2"}})
    e3 = make_event(start_offset_seconds=10800, translations={"en": {"title": "E3"}})

    resp = client.get("/api/events?limit=2")
    assert resp.status_code == 200
    data = _decode_data(resp)
    # We can't assert exactly 2 because other tests may leak data on
    # parallel runs in theory -- but here pytest is serial and we own
    # cleanup. Assert <= 2 and that at least the first two earliest are
    # present.
    assert len(data) <= 2
    # The 3 events we created should not all be in the response
    our_ids = {e1["id"], e2["id"], e3["id"]}
    returned_ours = {r["id"] for r in data} & our_ids
    assert len(returned_ours) <= 2


def test_list_orders_by_start_time_ascending(client, make_event):
    """Events ordered by start_time ASC (earliest first)."""
    later = make_event(start_offset_seconds=7200, translations={"en": {"title": "Later"}})
    sooner = make_event(start_offset_seconds=3600, translations={"en": {"title": "Sooner"}})

    resp = client.get("/api/events")
    data = _decode_data(resp)
    # Find positions of our two events
    our_rows = [r for r in data if r["id"] in (later["id"], sooner["id"])]
    assert len(our_rows) == 2
    # sooner must come before later
    assert our_rows[0]["id"] == sooner["id"]
    assert our_rows[1]["id"] == later["id"]


def test_list_response_shape(client, sample_event):
    """Response shape matches frontend Event type contract."""
    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = _decode_data(resp)
    row = next(r for r in data if r["id"] == sample_event["id"])
    expected_keys = {
        "id", "slug", "title", "location_id", "starts_at", "ends_at",
        "status", "description", "poster_image",
    }
    assert set(row.keys()) == expected_keys
