from datetime import date, timedelta


def test_start_cycle_and_get_current(client, auth_headers):
    start = date.today() - timedelta(days=3)
    response = client.post("/cycles/start", json={"start_date": start.isoformat()}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["phase"] == "menstrual"

    current = client.get("/cycles/current", headers=auth_headers)
    assert current.status_code == 200
    body = current.json()
    assert body["current_day"] == 4
    assert body["current_phase"] == "menstrual"
    assert body["cycle"]["start_date"] == start.isoformat()


def test_starting_second_cycle_closes_the_first_and_updates_average(client, auth_headers):
    first_start = date.today() - timedelta(days=30)
    second_start = date.today()

    client.post("/cycles/start", json={"start_date": first_start.isoformat()}, headers=auth_headers)
    response = client.post("/cycles/start", json={"start_date": second_start.isoformat()}, headers=auth_headers)
    assert response.status_code == 201

    history = client.get("/cycles/history", headers=auth_headers).json()
    assert history["total"] == 2
    closed = next(c for c in history["cycles"] if c["end_date"] is not None)
    assert closed["cycle_length"] == 30

    me = client.get("/auth/me", headers=auth_headers).json()
    assert me["tracked_cycles_count"] == 1
    assert me["average_cycle_length"] == 30


def test_get_current_cycle_404_when_none_started(client, auth_headers):
    response = client.get("/cycles/current", headers=auth_headers)
    assert response.status_code == 404


def test_new_cycle_start_date_must_be_after_open_cycle(client, auth_headers):
    start = date.today()
    client.post("/cycles/start", json={"start_date": start.isoformat()}, headers=auth_headers)
    response = client.post(
        "/cycles/start",
        json={"start_date": (start - timedelta(days=1)).isoformat()},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_create_and_fetch_checkin(client, auth_headers):
    today = date.today()
    client.post("/cycles/start", json={"start_date": today.isoformat()}, headers=auth_headers)

    response = client.post(
        "/checkins/",
        json={
            "date": today.isoformat(),
            "energy_level": 6,
            "pain_level": 3,
            "mood": ["happy", "calm"],
            "symptoms": ["bloating"],
            "journal_text": "Feeling okay today.",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["energy_level"] == 6
    assert body["journal_text"] == "Feeling okay today."
    assert body["cycle_id"] is not None

    fetched = client.get(f"/checkins/{today.isoformat()}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["mood"] == ["happy", "calm"]


def test_checkin_upsert_on_same_date(client, auth_headers):
    today = date.today()
    client.post("/checkins/", json={"date": today.isoformat(), "energy_level": 4}, headers=auth_headers)
    response = client.post("/checkins/", json={"date": today.isoformat(), "energy_level": 9}, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["energy_level"] == 9

    history = client.get("/checkins/history", headers=auth_headers).json()
    assert history["total"] == 1


def test_checkin_not_found_for_missing_date(client, auth_headers):
    response = client.get("/checkins/2020-01-01", headers=auth_headers)
    assert response.status_code == 404


def test_journal_text_is_encrypted_at_rest(client, auth_headers):
    """The plaintext journal entry should never appear verbatim in the raw
    database row — only the encrypted token should be stored.
    """
    import sqlite3

    today = date.today()
    client.post(
        "/checkins/",
        json={"date": today.isoformat(), "journal_text": "a very private secret"},
        headers=auth_headers,
    )

    conn = sqlite3.connect("test.db")
    row = conn.execute("SELECT journal_text FROM daily_checkins LIMIT 1").fetchone()
    conn.close()

    assert row is not None
    assert row[0] != "a very private secret"
