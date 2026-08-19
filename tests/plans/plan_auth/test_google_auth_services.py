from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.auth.auth0_google import Auth0GoogleIdentity
from pecha_api.plans.auth.plan_auth_enums import AuthorStatus
from pecha_api.plans.auth.plan_auth_models import GoogleExchangeRequest, TokenResponse
from pecha_api.plans.auth.plan_auth_services import exchange_google_token
from pecha_api.plans.auth.plan_auth_models import AuthorLoginResponse, AuthorInfo as AuthAuthorInfo


def _session(mock_session_local):
    db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = db
    return db


def _author(*, is_active=True, is_verified=True, email="ada@example.com"):
    author = MagicMock()
    author.id = uuid4()
    author.first_name = "Ada"
    author.last_name = "Lovelace"
    author.email = email
    author.phone_number = None
    author.image_url = None
    author.is_verified = is_verified
    author.is_active = is_active
    return author


@patch("pecha_api.plans.auth.plan_auth_services.SessionLocal")
@patch("pecha_api.plans.auth.plan_auth_services.verify_auth0_google_token")
def test_exchange_creates_verified_inactive_google_profile(
    verify_google,
    session_local,
):
    verify_google.return_value = Auth0GoogleIdentity(
        subject="google-oauth2|123",
        email="ada@example.com",
        first_name=None,
        last_name=None,
    )
    db = _session(session_local)
    saved_author = _author(is_active=False)

    with patch(
        "pecha_api.plans.auth.plan_auth_services.find_author_by_email",
        return_value=None,
    ), patch(
        "pecha_api.plans.auth.plan_auth_services.save_google_author",
        return_value=saved_author,
    ) as save, patch(
        "pecha_api.plans.auth.plan_auth_services.notify_pending_group_invites",
    ) as mock_notify:
        response = exchange_google_token(
            GoogleExchangeRequest(
                auth0_token="auth0-token",
                first_name=" Ada ",
                last_name=" Lovelace ",
            )
        )

    author_arg = save.call_args.kwargs["author"]
    assert save.call_args.kwargs["db"] is db
    assert author_arg.first_name == "Ada"
    assert author_arg.last_name == "Lovelace"
    assert author_arg.email == "ada@example.com"
    assert author_arg.password is None
    assert author_arg.is_verified is True
    assert author_arg.is_active is False
    assert response.status == AuthorStatus.INACTIVE
    assert response.auth is None
    assert response.email == "ada@example.com"
    mock_notify.assert_called_once_with(saved_author)


@patch("pecha_api.plans.auth.plan_auth_services.SessionLocal")
@patch("pecha_api.plans.auth.plan_auth_services.verify_auth0_google_token")
def test_exchange_uses_names_from_token_when_present(
    verify_google,
    session_local,
):
    verify_google.return_value = Auth0GoogleIdentity(
        subject="google-oauth2|123",
        email="ada@example.com",
        first_name="Ada",
        last_name="Lovelace",
    )
    _session(session_local)
    saved_author = _author(is_active=False)

    with patch(
        "pecha_api.plans.auth.plan_auth_services.find_author_by_email",
        return_value=None,
    ), patch(
        "pecha_api.plans.auth.plan_auth_services.save_google_author",
        return_value=saved_author,
    ) as save:
        exchange_google_token(GoogleExchangeRequest(auth0_token="auth0-token"))

    author_arg = save.call_args.kwargs["author"]
    assert author_arg.first_name == "Ada"
    assert author_arg.last_name == "Lovelace"


def test_exchange_new_profile_requires_both_names():
    google_identity = Auth0GoogleIdentity(
        subject="google-oauth2|123",
        email="ada@example.com",
    )
    with patch(
        "pecha_api.plans.auth.plan_auth_services.verify_auth0_google_token",
        return_value=google_identity,
    ), patch(
        "pecha_api.plans.auth.plan_auth_services.SessionLocal",
    ) as session_local, patch(
        "pecha_api.plans.auth.plan_auth_services.find_author_by_email",
        return_value=None,
    ):
        _session(session_local)
        with pytest.raises(HTTPException) as exc:
            exchange_google_token(
                GoogleExchangeRequest(auth0_token="auth0-token", first_name="Ada")
            )

    assert exc.value.status_code == 422


@patch("pecha_api.plans.auth.plan_auth_services.generate_token_author")
@patch("pecha_api.plans.auth.plan_auth_services.SessionLocal")
@patch("pecha_api.plans.auth.plan_auth_services.verify_auth0_google_token")
def test_exchange_existing_active_author_returns_tokens(
    verify_google,
    session_local,
    generate_token,
):
    verify_google.return_value = Auth0GoogleIdentity(
        subject="google-oauth2|123",
        email="ada@example.com",
    )
    _session(session_local)
    author = _author(is_active=True, is_verified=True)
    token_response = AuthorLoginResponse(
        user=AuthAuthorInfo(name="Ada Lovelace"),
        auth=TokenResponse(
            access_token="access",
            refresh_token="refresh",
            token_type="Bearer",
        ),
    )
    generate_token.return_value = token_response

    with patch(
        "pecha_api.plans.auth.plan_auth_services.find_author_by_email",
        return_value=author,
    ), patch(
        "pecha_api.plans.auth.plan_auth_services.notify_pending_group_invites",
    ) as mock_notify:
        response = exchange_google_token(
            GoogleExchangeRequest(auth0_token="auth0-token")
        )

    assert response.status == AuthorStatus.ACTIVE
    assert response.auth is not None
    assert response.auth.access_token == "access"
    mock_notify.assert_not_called()


@patch("pecha_api.plans.auth.plan_auth_services.SessionLocal")
@patch("pecha_api.plans.auth.plan_auth_services.verify_auth0_google_token")
def test_exchange_first_verification_of_existing_author_notifies_pending_invites(
    verify_google,
    session_local,
):
    verify_google.return_value = Auth0GoogleIdentity(
        subject="google-oauth2|123",
        email="ada@example.com",
    )
    _session(session_local)
    author = _author(is_active=False, is_verified=False)

    with patch(
        "pecha_api.plans.auth.plan_auth_services.find_author_by_email",
        return_value=author,
    ), patch(
        "pecha_api.plans.auth.plan_auth_services.update_author",
        return_value=author,
    ) as mock_update, patch(
        "pecha_api.plans.auth.plan_auth_services.notify_pending_group_invites",
    ) as mock_notify:
        exchange_google_token(GoogleExchangeRequest(auth0_token="auth0-token"))

    assert author.is_verified is True
    mock_update.assert_called_once()
    mock_notify.assert_called_once_with(author)
