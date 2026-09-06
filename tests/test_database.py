import app.database as database


def test_init_save_get_and_dedupe(tmp_path, monkeypatch):
    test_db = tmp_path / "events_test.db"

    monkeypatch.setattr(
        database,
        "DB_PATH",
        test_db,
    )

    database.init_db()

    saved = database.save_event(
        delivery_id="delivery-1",
        event="issues",
        action="opened",
        issue_number=1,
        timestamp="2026-09-06T00:00:00+00:00",
    )

    assert saved is True

    duplicate = database.save_event(
        delivery_id="delivery-1",
        event="issues",
        action="opened",
        issue_number=1,
        timestamp="2026-09-06T00:00:01+00:00",
    )

    assert duplicate is False

    events = database.get_events(limit=10)

    assert len(events) == 1
    assert events[0]["delivery_id"] == "delivery-1"
    assert events[0]["event"] == "issues"
    assert events[0]["action"] == "opened"
    assert events[0]["issue_number"] == 1


def test_get_events_limit(tmp_path, monkeypatch):
    test_db = tmp_path / "events_limit.db"

    monkeypatch.setattr(
        database,
        "DB_PATH",
        test_db,
    )

    database.init_db()

    database.save_event(
        delivery_id="delivery-a",
        event="issues",
        action="opened",
        issue_number=1,
        timestamp="2026-09-06T00:00:00+00:00",
    )

    database.save_event(
        delivery_id="delivery-b",
        event="issue_comment",
        action="created",
        issue_number=1,
        timestamp="2026-09-06T00:00:01+00:00",
    )

    events = database.get_events(limit=1)

    assert len(events) == 1

