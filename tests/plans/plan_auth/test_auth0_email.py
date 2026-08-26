from contextlib import AbstractContextManager
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from pecha_api.auth.auth0_email import verify_auth0_email_token


def _payload(**overrides: Any) -> dict:
    base = {
        "sub": "auth0|abc123",
        "aud": "webuddhist-backend",
        "https://webuddhist.com/email": "ada@example.com",
        "https://webuddhist.com/email_verified": True,
        "https://webuddhist.com/given_name": "Ada",
        "https://webuddhist.com/family_name": "Lovelace",
        "iat": datetime.now(timezone.utc).timestamp(),
    }
    base.update(overrides)
    return base


def _config_patches() -> tuple[AbstractContextManager, AbstractContextManager]:
    return (
        patch(
            "pecha_api.auth.auth0_email.get",
            side_effect=lambda key: {
                "AUTH0_GOOGLE_EMAIL_CLAIM": "https://webuddhist.com/email",
                "AUTH0_GOOGLE_EMAIL_VERIFIED_CLAIM": "https://webuddhist.com/email_verified",
            }.get(key, ""),
        ),
        patch(
            "pecha_api.auth.auth0_email.get_int",
            return_value=300,
        ),
    )


def test_verify_auth0_email_token_returns_normalized_identity() -> None:
    get_mock, get_int_mock = _config_patches()
    with patch(
        "pecha_api.auth.auth0_email._decode_auth0_token",
        return_value=_payload(),
    ), get_mock, get_int_mock:
        identity = verify_auth0_email_token("token")

    assert identity.subject == "auth0|abc123"
    assert identity.email == "ada@example.com"
    assert identity.first_name == "Ada"
    assert identity.last_name == "Lovelace"


@pytest.mark.parametrize(
    "payload",
    [
        _payload(sub="google-oauth2|abc"),
        _payload(sub="sms|abc"),
        _payload(sub="auth0|"),
        _payload(**{"https://webuddhist.com/email": None, "email": None}),
        _payload(iat=None),
    ],
)
def test_verify_auth0_email_token_rejects_untrusted_claims(payload: dict) -> None:
    get_mock, get_int_mock = _config_patches()
    with patch(
        "pecha_api.auth.auth0_email._decode_auth0_token",
        return_value=payload,
    ), get_mock, get_int_mock:
        with pytest.raises(HTTPException) as exc:
            verify_auth0_email_token("token")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid Auth0 email token"


def test_verify_auth0_email_token_rejects_unverified_email_with_clear_message() -> None:
    get_mock, get_int_mock = _config_patches()
    with patch(
        "pecha_api.auth.auth0_email._decode_auth0_token",
        return_value=_payload(**{"https://webuddhist.com/email_verified": False}),
    ), get_mock, get_int_mock:
        with pytest.raises(HTTPException) as exc:
            verify_auth0_email_token("token")

    assert exc.value.status_code == 403
    assert "not verified" in exc.value.detail
