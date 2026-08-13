from src.main import app

EXPECTED_ROUTES = {
    ("POST", "/auth/register"),
    ("POST", "/auth/login"),
    ("GET", "/auth/me"),
    ("POST", "/cycles/start"),
    ("GET", "/cycles/current"),
    ("GET", "/cycles/history"),
    ("POST", "/checkins/"),
    ("GET", "/checkins/{checkin_date}"),
    ("GET", "/checkins/history"),
    ("GET", "/insights/today"),
    ("GET", "/insights/weekly"),
    ("GET", "/insights/patterns"),
    ("POST", "/chat/"),
    ("GET", "/chat/history"),
    ("POST", "/documents/upload"),
    ("GET", "/documents/"),
    ("GET", "/documents/{document_id}/analysis"),
    ("GET", "/user/export"),
    ("DELETE", "/user/"),
}


def _registered_routes() -> set[tuple[str, str]]:
    routes = set()
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if methods and path:
            for method in methods:
                if method != "HEAD":
                    routes.add((method, path))
    return routes


def test_all_expected_routes_are_registered():
    registered = _registered_routes()
    missing = EXPECTED_ROUTES - registered
    assert not missing, f"Missing routes: {missing}"


def test_health_check_route(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_schema_generates_without_error(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Cycla API"
