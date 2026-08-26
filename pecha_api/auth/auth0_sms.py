import logging
import re
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette import status

from pecha_api.config import get, get_int


AUTH0_SMS_PROVIDER = "auth0_sms"
AUTH0_SMS_CONNECTION = "sms"
_E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class Auth0SMSIdentity(BaseModel):
    subject: str
    phone_number: str


def normalize_e164(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Phone number claim must be a string")
    normalized = re.sub(r"[\s().-]", "", value)
    if not _E164_PATTERN.fullmatch(normalized):
        raise ValueError("Phone number claim is not valid E.164")
    return normalized


def _get_auth0_sms_public_keys() -> dict[str, dict[str, Any]]:
    domain = get("AUTH0_SMS_DOMAIN").strip()
    if not domain:
        raise ValueError("Auth0 SMS domain is not configured")
    response = requests.get(
        f"https://{domain}/.well-known/jwks.json",
        timeout=5,
    )
    response.raise_for_status()
    return {key["kid"]: key for key in response.json()["keys"]}


def verified_phone_number(payload: dict[str, Any]) -> str:
    phone_claim = get("AUTH0_SMS_PHONE_CLAIM").strip()
    verified_claim = get("AUTH0_SMS_PHONE_VERIFIED_CLAIM").strip()
    if not phone_claim or not verified_claim:
        raise ValueError("Auth0 SMS phone claims are not configured")
    if payload.get(verified_claim) is not True:
        raise ValueError("Auth0 SMS phone number is not verified")
    return normalize_e164(payload.get(phone_claim))


def extract_verified_phone_number(payload: dict[str, Any]) -> str | None:
    try:
        return verified_phone_number(payload)
    except (TypeError, ValueError):
        return None


def _decode_auth0_sms_token(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    if header.get("alg") != "RS256":
        raise ValueError("Auth0 SMS token must use RS256")
    kid = header.get("kid")
    if not kid:
        raise ValueError("Auth0 SMS token is missing kid")
    rsa_key = _get_auth0_sms_public_keys().get(kid)
    if rsa_key is None:
        raise ValueError("Auth0 SMS signing key was not found")

    domain = get("AUTH0_SMS_DOMAIN").strip()
    audience = get("AUTH0_SMS_AUDIENCE").strip()
    if not audience:
        raise ValueError("Auth0 SMS audience is not configured")
    return jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        issuer=f"https://{domain}/",
        audience=audience,
    )


def verify_auth0_sms_token(token: str) -> Auth0SMSIdentity:
    try:
        payload = _decode_auth0_sms_token(token)
        phone_number = verified_phone_number(payload)
        subject = payload.get("sub")
        # Auth0 passwordless SMS subjects are "sms|<opaque user id>", not "sms|<E.164>".
        if not isinstance(subject, str) or not subject.startswith(f"{AUTH0_SMS_CONNECTION}|"):
            raise ValueError("Auth0 SMS subject is not from the SMS connection")
        if not subject[len(AUTH0_SMS_CONNECTION) + 1 :].strip():
            raise ValueError("Auth0 SMS subject is missing a user identifier")

        issued_at = payload.get("iat")
        if not isinstance(issued_at, (int, float)):
            raise ValueError("Auth0 SMS token is missing iat")
        token_age = datetime.now(timezone.utc).timestamp() - issued_at
        if token_age < -60 or token_age > get_int("AUTH0_SMS_TOKEN_MAX_AGE_SECONDS"):
            raise ValueError("Auth0 SMS token is not fresh")

        return Auth0SMSIdentity(subject=subject, phone_number=phone_number)
    except (JWTError, KeyError, TypeError, ValueError, requests.RequestException) as exception:
        logging.warning("Auth0 SMS token rejected: %s", exception)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Auth0 SMS token",
        )
