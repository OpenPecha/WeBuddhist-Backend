from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.auth.auth_enums import RegistrationSource
from pecha_api.auth.auth_models import (
    PhoneExchangeRequest,
    TokenResponse,
    UserInfo,
    UserLoginResponse,
)
from pecha_api.auth.auth_repository import generate_token_data
from pecha_api.auth.auth_service import (
    exchange_phone_token,
    link_phone_identity,
    resolve_user_from_backend_payload,
)
from pecha_api.auth.auth0_sms import Auth0SMSIdentity
from pecha_api.users.users_service import resolve_user_from_token_payload


def _session(mock_session_local):
    db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = db
    return db


def _user():
    user = MagicMock()
    user.id = uuid4()
    user.firstname = "Tashi"
    user.lastname = "Dolma"
    user.email = None
    user.phone_number = None
    user.avatar_url = None
    user.is_active = True
    return user


def _login_response():
    return UserLoginResponse(
        user=UserInfo(name="Tashi Dolma"),
        auth=TokenResponse(
            access_token="access",
            refresh_token="refresh",
            token_type="Bearer",
        ),
    )


@patch("pecha_api.auth.auth_service.SessionLocal")
@patch("pecha_api.auth.auth_service.verify_auth0_sms_token")
def test_exchange_creates_active_phone_user_with_backend_tokens(
    verify_sms,
    session_local,
):
    verify_sms.return_value = Auth0SMSIdentity(
        subject="sms|+14155552671",
        phone_number="+14155552671",
    )
    db = _session(session_local)
    saved_user = _user()
    saved_user.phone_number = "+14155552671"

    with patch(
        "pecha_api.auth.auth_service.get_user_by_phone",
        return_value=None,
    ), patch(
        "pecha_api.auth.auth_service.generate_and_validate_username",
        return_value="tashi_dolma.1234",
    ), patch(
        "pecha_api.auth.auth_service.save_phone_user",
        return_value=saved_user,
    ) as save, patch(
        "pecha_api.auth.auth_service.generate_token_user",
        return_value=_login_response(),
    ):
        response = exchange_phone_token(
            PhoneExchangeRequest(
                auth0_token="auth0-token",
                first_name=" Tashi ",
                last_name=" Dolma ",
            )
        )

    user_arg = save.call_args.kwargs["user"]
    assert save.call_args.kwargs["db"] is db
    assert user_arg.firstname == "Tashi"
    assert user_arg.lastname == "Dolma"
    assert user_arg.username == "tashi_dolma.1234"
    assert user_arg.email is None
    assert user_arg.password is None
    assert user_arg.phone_number == "+14155552671"
    assert user_arg.registration_source == RegistrationSource.PHONE.value
    assert user_arg.is_active is True
    assert response.auth.access_token == "access"


def test_exchange_new_phone_user_requires_names():
    with patch(
        "pecha_api.auth.auth_service.verify_auth0_sms_token",
        return_value=Auth0SMSIdentity(
            subject="sms|+14155552671",
            phone_number="+14155552671",
        ),
    ), patch(
        "pecha_api.auth.auth_service.SessionLocal",
    ) as session_local, patch(
        "pecha_api.auth.auth_service.get_user_by_phone",
        return_value=None,
    ):
        _session(session_local)
        with pytest.raises(HTTPException) as exc:
            exchange_phone_token(
                PhoneExchangeRequest(auth0_token="auth0-token", first_name="Tashi")
            )

    assert exc.value.status_code == 422


def test_link_verified_phone_to_existing_user():
    user = _user()
    with patch(
        "pecha_api.auth.auth_service._validate_backend_token",
        return_value={"sub": str(user.id)},
    ), patch(
        "pecha_api.auth.auth_service.verify_auth0_sms_token",
        return_value=Auth0SMSIdentity(
            subject="sms|+14155552671",
            phone_number="+14155552671",
        ),
    ), patch(
        "pecha_api.auth.auth_service.SessionLocal",
    ) as session_local, patch(
        "pecha_api.auth.auth_service.resolve_user_from_backend_payload",
        return_value=user,
    ), patch(
        "pecha_api.auth.auth_service.get_user_by_phone",
        return_value=None,
    ), patch(
        "pecha_api.auth.auth_service.link_user_phone",
    ) as link:
        _session(session_local)
        response = link_phone_identity("backend-token", "auth0-token")

    assert response.user_id == user.id
    link.assert_called_once()
    assert link.call_args.kwargs["phone_number"] == "+14155552671"


def test_link_rejects_phone_owned_by_another_user():
    user = _user()
    conflicting_user = MagicMock(id=uuid4())
    with patch(
        "pecha_api.auth.auth_service._validate_backend_token",
        return_value={"sub": str(user.id)},
    ), patch(
        "pecha_api.auth.auth_service.verify_auth0_sms_token",
        return_value=Auth0SMSIdentity(
            subject="sms|+14155552671",
            phone_number="+14155552671",
        ),
    ), patch(
        "pecha_api.auth.auth_service.SessionLocal",
    ) as session_local, patch(
        "pecha_api.auth.auth_service.resolve_user_from_backend_payload",
        return_value=user,
    ), patch(
        "pecha_api.auth.auth_service.get_user_by_phone",
        return_value=conflicting_user,
    ):
        _session(session_local)
        with pytest.raises(HTTPException) as exc:
            link_phone_identity("backend-token", "auth0-token")

    assert exc.value.status_code == 409


def test_regular_token_data_uses_stable_uuid_without_email():
    user = _user()
    with patch(
        "pecha_api.auth.auth_repository.get",
        side_effect=lambda key: {"JWT_ISSUER": "issuer", "JWT_AUD": "audience"}[key],
    ):
        payload = generate_token_data(user)

    assert payload["sub"] == str(user.id)
    assert "email" not in payload


def test_backend_and_protected_route_resolution_support_uuid_and_legacy_email():
    db = MagicMock()
    user = _user()
    for resolver, module in (
        (resolve_user_from_backend_payload, "pecha_api.auth.auth_service"),
        (resolve_user_from_token_payload, "pecha_api.users.users_service"),
    ):
        with patch(f"{module}.get_user_by_id", return_value=user) as by_id:
            assert resolver(db, {"sub": str(user.id)}) is user
            by_id.assert_called_once_with(db=db, user_id=user.id)

        with patch(f"{module}.get_user_by_email", return_value=user) as by_email:
            assert resolver(db, {"email": "legacy@example.com"}) is user
            by_email.assert_called_once_with(db=db, email="legacy@example.com")
