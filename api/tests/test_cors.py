"""CORS configuration tests: both frontend origins, CRUD preflight, no wildcards."""

import pytest
from fastapi.testclient import TestClient

from platewise_api.core.config import settings
from platewise_api.main import app

client = TestClient(app)

FRONTEND_ORIGINS = ["http://localhost:3000", "http://localhost:1420"]


def test_settings_include_both_frontend_origins() -> None:
    for origin in FRONTEND_ORIGINS:
        assert origin in settings.cors_origin_list


@pytest.mark.parametrize("origin", FRONTEND_ORIGINS)
def test_simple_request_allows_frontend_origin(origin: str) -> None:
    response = client.get("/api/v1/status", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize("origin", FRONTEND_ORIGINS)
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_preflight_allows_crud_methods(origin: str, method: str) -> None:
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    allowed = response.headers["access-control-allow-methods"]
    assert method in {value.strip() for value in allowed.split(",")}


def test_unknown_origin_is_not_allowed() -> None:
    response = client.get("/api/v1/status", headers={"Origin": "http://evil.example"})

    # The request itself succeeds (CORS is a browser contract), but no
    # allow-origin header may be granted — and never a wildcard.
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_no_wildcard_origin_configured() -> None:
    assert "*" not in settings.cors_origin_list
