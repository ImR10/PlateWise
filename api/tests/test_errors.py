"""Standard API error envelope tests: shape, codes, and handler coverage."""

import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from platewise_api.core.errors import ApiError, register_exception_handlers
from platewise_api.main import app as real_app


def build_test_app() -> FastAPI:
    """A tiny app exercising the handlers without adding routes to the real API."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/boom")
    def boom() -> None:
        raise ApiError(
            "teapot_unavailable",
            "The teapot is short and stout.",
            status_code=418,
            context={"teapot_id": "t-1"},
        )

    @test_app.get("/needs-count")
    def needs_count(count: int) -> dict[str, int]:
        return {"count": count}

    @test_app.get("/unexpected")
    def unexpected() -> None:
        raise RuntimeError("sensitive database password")

    @test_app.get("/authenticate")
    def authenticate() -> None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return test_app


client = TestClient(build_test_app())
safe_client = TestClient(build_test_app(), raise_server_exceptions=False)
real_client = TestClient(real_app)


def test_api_error_serializes_to_standard_envelope() -> None:
    response = client.get("/boom")

    assert response.status_code == 418
    assert response.json() == {
        "error": {
            "code": "teapot_unavailable",
            "message": "The teapot is short and stout.",
            "details": None,
            "context": {"teapot_id": "t-1"},
        }
    }


def test_validation_error_carries_field_details() -> None:
    response = client.get("/needs-count", params={"count": "not-a-number"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed."
    details = body["error"]["details"]
    assert len(details) == 1
    assert details[0]["loc"] == ["query", "count"]
    assert details[0]["type"] == "int_parsing"


def test_missing_parameter_is_a_validation_error() -> None:
    response = client.get("/needs-count")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unexpected_error_uses_safe_json_envelope(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.ERROR, logger="platewise_api.core.errors"):
        response = safe_client.get("/unexpected")

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred.",
            "details": None,
            "context": None,
        }
    }
    assert "sensitive database password" not in response.text
    assert "unexpected_api_error" in caplog.text


def test_http_exception_preserves_headers_and_envelope() -> None:
    response = client.get("/authenticate")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


def test_real_app_unknown_route_uses_envelope() -> None:
    response = real_client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert isinstance(body["error"]["message"], str)


def test_real_app_method_not_allowed_uses_envelope() -> None:
    response = real_client.delete("/api/v1/status")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_real_app_success_paths_are_unchanged() -> None:
    response = real_client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
