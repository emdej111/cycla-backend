from datetime import date


def test_export_returns_all_user_data(client, auth_headers):
    client.post("/cycles/start", json={"start_date": date.today().isoformat()}, headers=auth_headers)
    client.post("/checkins/", json={"date": date.today().isoformat(), "energy_level": 5}, headers=auth_headers)

    response = client.get("/user/export", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "test@cycla.app"
    assert len(body["cycles"]) == 1
    assert len(body["checkins"]) == 1


def test_delete_user_removes_account_and_cascades(client, auth_headers):
    client.post("/cycles/start", json={"start_date": date.today().isoformat()}, headers=auth_headers)

    response = client.delete("/user/", headers=auth_headers)
    assert response.status_code == 204

    me = client.get("/auth/me", headers=auth_headers)
    assert me.status_code == 401

    login = client.post("/auth/login", json={"email": "test@cycla.app", "password": "supersecret123"})
    assert login.status_code == 401


def test_export_and_delete_require_authentication(client):
    assert client.get("/user/export").status_code == 401
    assert client.delete("/user/").status_code == 401
