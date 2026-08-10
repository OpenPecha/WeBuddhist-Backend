from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from pecha_api.auth.auth0_sms import (
    _decode_auth0_sms_token,
    extract_verified_phone_number,
    normalize_e164,
    verify_auth0_sms_token,
)


def _payload(**overrides):
    now = datetime.now(timezone.utc).timestamp()
    payload = {
        "sub": "sms|6a744811b6f40222b44b0bf3",
        "iat": now,
        "https://webuddhist.com/phone_number": "+1 (415) 555-2671",
        "https://webuddhist.com/phone_number_verified": True,
    }
    payload.update(overrides)
    return payload


def test_decode_auth0_sms_token_strictly_verifies_rs256_issuer_and_audience():
    key = {"kid": "key-1", "kty": "RSA"}
    with patch(
        "pecha_api.auth.auth0_sms.jwt.get_unverified_header",
        return_value={"alg": "RS256", "kid": "key-1"},
    ), patch(
        "pecha_api.auth.auth0_sms._get_auth0_sms_public_keys",
        return_value={"key-1": key},
    ), patch(
        "pecha_api.auth.auth0_sms.get",
        side_effect=lambda name: {
            "AUTH0_SMS_DOMAIN": "tenant.auth0.com",
            "AUTH0_SMS_AUDIENCE": "cms-api",
        }[name],
    ), patch(
        "pecha_api.auth.auth0_sms.jwt.decode",
        return_value={"sub": "sms|+14155552671"},
    ) as decode:
        _decode_auth0_sms_token("token")

    decode.assert_called_once_with(
        "token",
        key,
        algorithms=["RS256"],
        issuer="https://tenant.auth0.com/",
        audience="cms-api",
    )


def test_decode_auth0_sms_token_rejects_non_rs256_header():
    with patch(
        "pecha_api.auth.auth0_sms.jwt.get_unverified_header",
        return_value={"alg": "HS256", "kid": "key-1"},
    ):
        with pytest.raises(ValueError, match="RS256"):
            _decode_auth0_sms_token("token")


def test_verify_auth0_sms_token_returns_normalized_verified_identity():
    with patch(
        "pecha_api.auth.auth0_sms._decode_auth0_sms_token",
        return_value=_payload(),
    ):
        identity = verify_auth0_sms_token("token")

    assert identity.subject == "sms|6a744811b6f40222b44b0bf3"
    assert identity.phone_number == "+14155552671"


@pytest.mark.parametrize(
    "payload",
    [
        _payload(**{"https://webuddhist.com/phone_number_verified": False}),
        _payload(sub="auth0|abc"),
        _payload(sub="sms|"),
        _payload(**{"https://webuddhist.com/phone_number": "4155552671"}),
        _payload(iat=0),
    ],
)
def test_verify_auth0_sms_token_rejects_untrusted_claims(payload):
    with patch(
        "pecha_api.auth.auth0_sms._decode_auth0_sms_token",
        return_value=payload,
    ):
        with pytest.raises(HTTPException) as exc:
            verify_auth0_sms_token("token")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid Auth0 SMS token"


def test_extract_verified_phone_number_returns_normalized_claim():
    assert extract_verified_phone_number(_payload()) == "+14155552671"


@pytest.mark.parametrize(
    "payload",
    [
        _payload(**{"https://webuddhist.com/phone_number_verified": False}),
        _payload(**{"https://webuddhist.com/phone_number": "4155552671"}),
        {"sub": "auth0|abc", "email": "person@example.com"},
    ],
)
def test_extract_verified_phone_number_returns_none_for_unusable_claims(payload):
    assert extract_verified_phone_number(payload) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("+14155552671", "+14155552671"),
        ("+1 (415) 555-2671", "+14155552671"),
    ],
)
def test_normalize_e164(value, expected):
    assert normalize_e164(value) == expected
