def test_register_creates_user_and_returns_token(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "new@cycla.app",
            "password": "supersecret123",
            "name": "New User",
            "cycle_goal": "fertility",
            "language": "hr",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "new@cycla.app"
    assert body["user"]["tracked_cycles_count"] == 0
    assert body["user"]["average_cycle_length"] == 29  # default


def test_register_duplicate_email_rejected(client, registered_user):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@cycla.app",
            "password": "anotherpassword",
            "name": "Duplicate",
        },
    )
    assert response.status_code == 409


def test_login_success(client, registered_user):
    response = client.post(
        "/auth/login", json={"email": "test@cycla.app", "password": "supersecret123"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_rejected(client, registered_user):
    response = client.post(
        "/auth/login", json={"email": "test@cycla.app", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@cycla.app"
