from collections.abc import Generator

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


class HealthySession:
    def execute(self, _statement: object) -> None:
        return None


def override_get_db() -> Generator[HealthySession, None, None]:
    yield HealthySession()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_reports_api_and_database() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "api": "ok", "database": "ok"}


def test_status_reports_service_metadata() -> None:
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "UniDine API"
    assert body["status"] == "ok"
    assert body["environment"] == "development"
