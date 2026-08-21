import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from fastapi import HTTPException
from jose import JWTError
from pydantic import BaseModel
from starlette import status

from pecha_api.auth.auth0_google import (
    _claim_string,
    _decode_auth0_google_token as _decode_auth0_token,
    _extract_names,
)
from pecha_api.auth.auth_repository import _extract_email_from_auth0_payload
from pecha_api.config import get, get_int


AUTH0_EMAIL_PROVIDER = "auth0_email"
# Auth0 database (email/password) connection subjects are "auth0|<opaque user id>".
EMAIL_SUBJECT_PREFIX = "auth0|"


class Auth0EmailIdentity(BaseModel):
    subject: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


def verify_auth0_email_token(token: str) -> Auth0EmailIdentity:
    try:
        payload = _decode_auth0_token(token)
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.startswith(EMAIL_SUBJECT_PREFIX):
            raise ValueError("Auth0 email subject is not from the database connection")
        if not subject[len(EMAIL_SUBJECT_PREFIX):].strip():
            raise ValueError("Auth0 email subject is missing a user identifier")

        email_claim = get("AUTH0_GOOGLE_EMAIL_CLAIM").strip()
        verified_claim = get("AUTH0_GOOGLE_EMAIL_VERIFIED_CLAIM").strip()
        email = _claim_string(payload, email_claim) or _extract_email_from_auth0_payload(
            payload
        )
        if not email:
            raise ValueError("Auth0 email claim is missing")

        email_verified = payload.get(verified_claim)
        if email_verified is None:
            email_verified = payload.get("email_verified")
        if email_verified is not True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your email address is not verified yet. Please check your inbox for a verification email and try again.",
            )

        issued_at = payload.get("iat")
        if not isinstance(issued_at, (int, float)):
            raise ValueError("Auth0 email token is missing iat")
        token_age = datetime.now(timezone.utc).timestamp() - issued_at
        if token_age < -60 or token_age > get_int("AUTH0_SMS_TOKEN_MAX_AGE_SECONDS"):
            raise ValueError("Auth0 email token is not fresh")

        first_name, last_name = _extract_names(payload)
        return Auth0EmailIdentity(
            subject=subject,
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
        )
    except (JWTError, KeyError, TypeError, ValueError, requests.RequestException) as exception:
        logging.warning("Auth0 email token rejected: %s", exception)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Auth0 email token",
        )
