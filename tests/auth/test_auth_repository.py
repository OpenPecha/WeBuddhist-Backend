import jose
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest

from pecha_api.users.users_models import Users
from pecha_api.auth.auth_repository import (
    get_hashed_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_token_data,
    decode_backend_token,
    verify_auth0_token,
    _allowed_auth0_audiences,
)
from pecha_api.users.users_service import validate_token

PECHA_JWT_ISSUER = "https://pecha.org"
PECHA_JWT_AUD = "https://pecha.org"


def test_verify_password_success():
    plain_password = "mysecretpassword"
    hashed_password = get_hashed_password(plain_password)

    assert verify_password(plain_password, hashed_password) == True


def test_verify_password_fail():
    plain_password = "mysecretpassword"
    hashed_password = get_hashed_password(plain_password)

    assert verify_password("wrongpassword", hashed_password) == False
    assert verify_password("wrongpassword", "wrongpassword") == False
    assert verify_password("wrongpassword", "") == False
    assert verify_password("wrongpassword", None) == False
    assert verify_password(None, "wrongpassword") == False
    assert verify_password("", "wrongpassword") == False
    assert verify_password("", hashed_password) == False
    assert verify_password(None, hashed_password) == False
    assert verify_password(plain_password, "") == False
    assert verify_password(plain_password, None) == False
    assert verify_password("", "") == False
    assert verify_password(None, None) == False
    assert verify_password("", None) == False
    assert verify_password(None, "") == False


def test_get_hashed_password():
    plain_password = "mysecretpassword"
    hashed_password = get_hashed_password(plain_password)

    assert hashed_password != plain_password
    assert verify_password(plain_password, hashed_password) == True


def test_get_hashed_password_empty_password():
    plain_password = ""
    hashed_password = get_hashed_password(plain_password)

    assert hashed_password == None


def test_get_hashed_password_none_password():
    plain_password = None
    hashed_password = get_hashed_password(plain_password)
    assert hashed_password == None


def test_get_hashed_password_different_passwords():
    plain_password1 = "mysecretpassword"
    plain_password2 = "anotherpassword"
    hashed_password1 = get_hashed_password(plain_password1)
    hashed_password2 = get_hashed_password(plain_password2)

    assert hashed_password1 != hashed_password2
    assert verify_password(plain_password1, hashed_password1) == True
    assert verify_password(plain_password2, hashed_password2) == True
    assert verify_password(plain_password1, hashed_password2) == False
    assert verify_password(plain_password2, hashed_password1) == False


def test_verify_password_with_valid_password():
    plain_password = "validpassword"
    hashed_password = get_hashed_password(plain_password)

    assert verify_password(plain_password, hashed_password) == True


def test_verify_password_with_invalid():
    plain_password = "validpassword"
    hashed_password = get_hashed_password(plain_password)

    assert verify_password("", hashed_password) == False
    assert verify_password("invalidpassword", hashed_password) == False
    assert verify_password(None, hashed_password) == False
    assert verify_password(plain_password, "") == False
    assert verify_password(plain_password, None) == False
    assert verify_password("", "") == False
    assert verify_password(None, None) == False
    assert verify_password("", None) == False
    assert verify_password(None, "") == False


def test_create_access_token():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)

    assert token is not None
    decoded_data = validate_token(token)
    assert decoded_data["email"] == "test@example.com"
    assert "exp" in decoded_data


def test_create_access_token_with_custom_expiry():
    data = {
        "email": "test@example.com",
        "name": "John Doe ",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    expires_delta = timedelta(minutes=10)
    token = create_access_token(data, expires_delta)

    assert token is not None
    decoded_data = validate_token(token)
    assert decoded_data["email"] == "test@example.com"
    assert "exp" in decoded_data
    assert decoded_data["exp"] == int((datetime.now(timezone.utc) + expires_delta).timestamp())



def test_create_refresh_token():
    data = {
        "email": "test@example.com",
        "name": "John Doe ",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    token = create_refresh_token(data)

    assert token is not None
    decoded_data = validate_token(token)
    assert decoded_data["email"] == "test@example.com"
    assert "exp" in decoded_data


def test_create_refresh_token_with_custom_expiry():
    data = {
        "email": "test@example.com",
        "name": "John Doe ",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    expires_delta = timedelta(days=10)
    token = create_refresh_token(data, expires_delta)

    assert token is not None
    decoded_data = validate_token(token)
    assert decoded_data["email"] == "test@example.com"
    assert "exp" in decoded_data
    assert decoded_data["exp"] == int((datetime.now(timezone.utc) + expires_delta).timestamp())



def test_generate_token_data_success():
    user = Users(
        email="test@example.com",
        firstname="John",
        lastname="Doe",
        registration_source="email"
    )
    token_data = generate_token_data(user)

    assert token_data is not None
    assert token_data["email"] == "test@example.com"
    assert token_data["name"] == "John Doe"
    assert token_data["iss"] == PECHA_JWT_ISSUER
    assert token_data["aud"] == PECHA_JWT_AUD
    assert "iat" in token_data


def test_generate_token_data_missing_email():
    # Create a valid user first, then modify the email to None
    user = Users(
        email="test@example.com",
        firstname="John",
        lastname="Doe",
        registration_source="email"
    )
    # Simulate missing email by setting it to None after creation
    user.email = None
    token_data = generate_token_data(user)

    assert token_data is None


def test_generate_token_data_missing_firstname():
    # Create a valid user first, then modify the firstname to None
    user = Users(
        email="test@example.com",
        firstname="John",
        lastname="Doe",
        registration_source="email"
    )
    # Simulate missing firstname by setting it to None after creation
    user.firstname = None
    token_data = generate_token_data(user)

    assert token_data is None


def test_generate_token_data_missing_lastname():
    user = Users(
        email="test@example.com",
        firstname="John",
        lastname=None,
        registration_source="email"
    )
    token_data = generate_token_data(user)

    assert token_data is None


def test_generate_token_data_all_fields_missing():
    # Create a valid user first, then modify fields to None
    user = Users(
        email="test@example.com",
        firstname="John",
        lastname="Doe",
        registration_source="email"
    )
    # Simulate missing fields by setting them to None after creation
    user.email = None
    user.firstname = None
    user.lastname = None
    token_data = generate_token_data(user)

    assert token_data is None


def test_decode_token_success():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)
    decoded_data = validate_token(token)

    assert decoded_data is not None
    assert decoded_data["email"] == "test@example.com"
    assert decoded_data["name"] == "John Doe"
    assert decoded_data["iss"] == PECHA_JWT_ISSUER
    assert decoded_data["aud"] == PECHA_JWT_AUD
    assert "exp" in decoded_data


def test_decode_token_invalid_signature():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)
    invalid_token = token + "invalid"

    try:
        validate_token(invalid_token)
        assert False, "Expected jose.exceptions.JWSSignatureError"
    except jose.exceptions.JWSSignatureError:
        pass
    except jose.exceptions.JWTError:
        pass


def test_decode_token_expired():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    expires_delta = timedelta(seconds=-1)
    token = create_access_token(data, expires_delta)

    try:
        validate_token(token)
        assert False, "Expected jose.exceptions.ExpiredSignatureError"
    except jose.exceptions.ExpiredSignatureError:
        pass


def test_decode_token_invalid_audience():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": "invalid_audience",
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)
    try:
        validate_token(token)
        assert False, "Expected jwt.exceptions.InvalidAudienceError"
    except jose.exceptions.JWTClaimsError:
        pass


def test_decode_token_invalid_issuer():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": "invalid_issuer",
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)

    try:
        validate_token(token)
    except jwt.exceptions.InvalidIssuerError:
        assert False, "Expected jwt.exceptions.InvalidIssuerError"


def test_decode_backend_token_success():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)
    decoded_data = decode_backend_token(token)

    assert decoded_data is not None
    assert decoded_data["email"] == "test@example.com"
    assert decoded_data["name"] == "John Doe"
    assert decoded_data["iss"] == PECHA_JWT_ISSUER
    assert decoded_data["aud"] == PECHA_JWT_AUD
    assert "exp" in decoded_data


def test_decode_backend_token_invalid_signature():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)
    invalid_token = token + "invalid"

    try:
        decode_backend_token(invalid_token)
        assert False, "Expected jose.exceptions.JWSSignatureError"
    except jose.exceptions.JWSSignatureError:
        pass
    except jose.exceptions.JWTError:
        pass


def test_decode_backend_token_expired():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": PECHA_JWT_AUD,
        "iat": datetime.now(timezone.utc)
    }
    expires_delta = timedelta(seconds=-1)
    token = create_access_token(data, expires_delta)

    try:
        decode_backend_token(token)
        assert False, "Expected jose.exceptions.ExpiredSignatureError"
    except jose.exceptions.ExpiredSignatureError:
        pass


def test_decode_backend_token_invalid_audience():
    data = {
        "email": "test@example.com",
        "name": "John Doe",
        "iss": PECHA_JWT_ISSUER,
        "aud": "invalid_audience",
        "iat": datetime.now(timezone.utc)
    }
    token = create_access_token(data)
    try:
        decode_backend_token(token)
        assert False, "Expected jwt.exceptions.InvalidAudienceError"
    except jose.exceptions.JWTClaimsError:
        pass
