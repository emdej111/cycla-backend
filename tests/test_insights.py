from datetime import date, timedelta


def test_today_insight_is_generic_before_3_cycles(client, auth_headers):
    client.post("/cycles/start", json={"start_date": date.today().isoformat()}, headers=auth_headers)
    response = client.get("/insights/today", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["is_personalized"] is False
    assert body["type"] == "daily"
    assert len(body["content"]["recommendations"]) > 0


def test_today_insight_without_any_cycle_still_returns_generic(client, auth_headers):
    response = client.get("/insights/today", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_personalized"] is False


def test_today_insight_is_personalized_after_3_cycles(client, auth_headers, three_cycles_of_history, monkeypatch):
    monkeypatch.setattr(
        "src.services.claude_service.get_personalized_insight",
        lambda **kwargs: {
            "summary": "You tend to feel low energy on day 3 of your period.",
            "recommendations": ["Rest more on day 2-3 of your cycle."],
            "patterns_detected": ["low energy around day 3"],
        },
    )
    response = client.get("/insights/today", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["is_personalized"] is True
    assert "low energy" in body["content"]["phase_info"]["summary"] or body["content"]["recommendations"]


def test_today_insight_falls_back_to_generic_when_claude_fails(
    client, auth_headers, three_cycles_of_history, monkeypatch
):
    def _boom(**kwargs):
        raise RuntimeError("Claude API unavailable")

    monkeypatch.setattr("src.services.claude_service.get_personalized_insight", _boom)
    response = client.get("/insights/today", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_personalized"] is False


def test_weekly_insight_aggregates_checkins(client, auth_headers):
    today = date.today()
    client.post("/cycles/start", json={"start_date": today.isoformat()}, headers=auth_headers)
    client.post(
        "/checkins/",
        json={"date": today.isoformat(), "energy_level": 4, "symptoms": ["cramps"]},
        headers=auth_headers,
    )
    client.post(
        "/checkins/",
        json={
            "date": (today - timedelta(days=1)).isoformat(),
            "energy_level": 8,
            "symptoms": ["cramps"],
        },
        headers=auth_headers,
    )

    response = client.get("/insights/weekly", headers=auth_headers)
    assert response.status_code == 200
    content = response.json()["content"]
    assert content["days_logged"] == 2
    assert content["avg_energy_level"] == 6.0
    assert "cramps" in content["top_symptoms"]


def test_patterns_insufficient_data_before_3_cycles(client, auth_headers):
    response = client.get("/insights/patterns", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["sufficient_data"] is False
    assert body["patterns"] == []


def test_patterns_detected_after_3_cycles(client, auth_headers, three_cycles_of_history):
    response = client.get("/insights/patterns", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["sufficient_data"] is True
    assert any(p["symptom"] == "cramps" for p in body["patterns"])
