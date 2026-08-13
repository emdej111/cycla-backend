import os
from collections.abc import Generator
from datetime import date, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENCRYPTION_KEY", "z3nJZ7q1s0m3sM6f6f6QeXGz3nJZ7q1s0m3sM6f6f4=")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.models  # noqa: F401  registers all models on Base.metadata
from src.db.database import Base, get_db
from src.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(autouse=True)
def _fresh_database() -> Generator[None, None, None]:
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    app.dependency_overrides.clear()
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": "test@cycla.app",
            "password": "supersecret123",
            "name": "Test User",
            "age": 28,
            "cycle_goal": "health",
            "language": "en",
            "average_cycle_length": 28,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def auth_headers(registered_user: dict) -> dict:
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture
def three_cycles_of_history(client: TestClient, auth_headers: dict) -> None:
    """Backfills 3 completed cycles + check-ins with a recurring symptom on
    the same cycle day, so personalization/pattern-detection paths can be
    exercised without hitting the live Claude API.
    """
    today = date.today()
    start = today - timedelta(days=28 * 4)
    for _ in range(4):
        client.post("/cycles/start", json={"start_date": start.isoformat()}, headers=auth_headers)
        client.post(
            "/checkins/",
            json={
                "date": (start + timedelta(days=2)).isoformat(),
                "energy_level": 3,
                "symptoms": ["cramps", "fatigue"],
            },
            headers=auth_headers,
        )
        start = start + timedelta(days=28)
