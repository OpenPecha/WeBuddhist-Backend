import logging
from typing import Dict, Any

from jose import jwt
import requests
from jose import JWTError
import bcrypt
from datetime import datetime, timedelta, timezone

from ..config import get_float, get
from ..users.users_models import Users


def get_hashed_password(password):
    if not password:
        return None
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password, hashed_password):
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exception:
        logging.error(exception)
        return False


def create_access_token(data: dict, expires_delta: timedelta = None):
    if data is not None:
        if expires_delta is None:
            expires_delta = timedelta(minutes=get_float("ACCESS_TOKEN_EXPIRE_MINUTES"))
        return _generate_token(data, expires_delta)
    return None


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    if data is not None:
        if expires_delta is None:
            expires_delta = timedelta(days=get_float("REFRESH_TOKEN_EXPIRE_DAYS"))
        return _generate_token(data, expires_delta)
    return None


def _generate_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get("JWT_SECRET_KEY"), algorithm=get("JWT_ALGORITHM"))
    return encoded_jwt

def validate_token(token: str) -> Dict[str, Any]:
    if get("DOMAIN_NAME") in jwt.get_unverified_claims(token=token)["iss"]:
        return verify_auth0_token(token)
    else:
        return decode_backend_token(token)

def generate_token_data(user: Users):
    if not all([user.email, user.firstname, user.lastname]):
        return None
    data = {
        "email": user.email,
        "name": user.firstname + " " + user.lastname,
        "iss": get("JWT_ISSUER"),
        "aud": get("JWT_AUD"),
        "iat": datetime.now(timezone.utc)
    }
    return data


def decode_backend_token(token: str):
    return jwt.decode(token, get("JWT_SECRET_KEY"), algorithms=[get("JWT_ALGORITHM")], audience=get("JWT_AUD"))


def get_auth0_public_key():
    jwks_url = f"https://{get('DOMAIN_NAME')}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    return {key["kid"]: key for key in jwks["keys"]}


def verify_auth0_token(token: str):
    try:
        jwks = get_auth0_public_key()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = jwks.get(unverified_header["kid"])

        if not rsa_key:
            raise ValueError("Unable to find appropriate key")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=get("CLIENT_ID"),
            issuer=f"https://{get('DOMAIN_NAME')}/"
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Token validation failed: {e}")
