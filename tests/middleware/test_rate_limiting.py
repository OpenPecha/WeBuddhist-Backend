from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.middleware import rate_limiting


def _make_test_app() -> FastAPI:
    app = FastAPI()
    rate_limiting.register_rate_limiting(app)

    @app.get("/limited")
    async def limited_route():
        return {"ok": True}

    @app.get("/health")
    async def health_route():
        return {"status": "up"}

    return app


@pytest.fixture
def rate_limit_settings():
    with patch.multiple(
        rate_limiting,
        _is_enabled=lambda: True,
        _authenticated_limit=lambda: "5/hour",
        _unauthenticated_limit=lambda: "2/hour",
        _storage_uri=lambda: "memory://",
        _skip_paths=lambda: frozenset({"/health"}),
        _key_prefix=lambda: "test:ratelimit:",
    ):
        rate_limiting.limiter = rate_limiting._build_limiter()
        yield


def test_health_endpoint_is_exempt_from_rate_limiting(rate_limit_settings):
    app = _make_test_app()
    client = TestClient(app)

    for _ in range(10):
        response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK


def test_unauthenticated_requests_are_rate_limited(rate_limit_settings):
    app = _make_test_app()
    client = TestClient(app)

    assert client.get("/limited").status_code == status.HTTP_200_OK
    assert client.get("/limited").status_code == status.HTTP_200_OK
    response = client.get("/limited")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Rate limit exceeded" in response.json()["error"]


def test_authenticated_requests_use_separate_higher_limit(rate_limit_settings):
    app = _make_test_app()
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

    for _ in range(5):
        response = client.get("/limited", headers=headers)
        assert response.status_code == status.HTTP_200_OK

    response = client.get("/limited", headers=headers)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    assert client.get("/limited").status_code == status.HTTP_200_OK


def test_rate_limit_key_uses_hashed_bearer_token():
    request = type(
        "Request",
        (),
        {
            "headers": {"Authorization": "Bearer secret-token"},
            "client": type("Client", (), {"host": "127.0.0.1"})(),
        },
    )()

    key = rate_limiting.rate_limit_key(request)

    assert key.startswith("auth:")
    assert "secret-token" not in key


def test_rate_limit_key_uses_client_ip_without_auth():
    request = type(
        "Request",
        (),
        {
            "headers": {},
            "client": type("Client", (), {"host": "203.0.113.10"})(),
        },
    )()

    assert rate_limiting.rate_limit_key(request) == "ip:203.0.113.10"


def test_limit_for_key_matches_cms_policy_defaults():
    with patch(
        "pecha_api.middleware.rate_limiting.get_int",
        side_effect=lambda key: {
            "RATE_LIMIT_AUTHENTICATED_PER_HOUR": 1000,
            "RATE_LIMIT_UNAUTHENTICATED_PER_HOUR": 100,
        }[key],
    ):
        assert rate_limiting.limit_for_key("auth:abc") == "1000/hour"
        assert rate_limiting.limit_for_key("ip:1.2.3.4") == "100/hour"
