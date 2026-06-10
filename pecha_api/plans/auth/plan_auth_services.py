import secrets
from .plan_auth_enums import AuthorStatus
from .plan_auth_models import CreateAuthorRequest, AuthorDetails, TokenPayload, \
    AuthorVerificationResponse, ResponseError, TokenResponse, AuthorLoginResponse, AuthorInfo, EmailReVerificationResponse, RefreshTokenResponse
from pecha_api.plans.authors.plan_authors_model import Author, AuthorPasswordReset
from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_repository import save_author, get_author_by_email, update_author, check_author_exists
from pecha_api.auth.auth_repository import get_hashed_password, verify_password, create_access_token, create_refresh_token
from pecha_api.auth.password_reset_repository import save_password_reset, get_password_reset_by_token_for_author
from pecha_api.auth.auth_service import send_reset_email
from fastapi import HTTPException
from starlette import status
from datetime import datetime, timedelta, timezone
from jose import jwt
from pecha_api.config import get
from pecha_api.notification.email_provider import send_email
from jinja2 import Template
from pathlib import Path
from typing import Dict, Any
from pecha_api.plans.response_message import (
    PASSWORD_EMPTY,
    PASSWORD_LENGTH_INVALID,
    TOKEN_EXPIRED,
    TOKEN_INVALID,
    EMAIL_VERIFIED_SUCCESS, 
    EMAIL_ALREADY_VERIFIED,
    REGISTRATION_MESSAGE,
    AUTHOR_NOT_VERIFIED,
    AUTHOR_NOT_ACTIVE,
    INVALID_EMAIL_PASSWORD,
    AUTHOR_NOT_FOUND,
    BAD_REQUEST,
    EMAIL_IS_SENT
)

def _get_author_full_name(author: Author) -> str:
    """Helper function to get author's full name"""
    return f"{author.first_name} {author.last_name}"


def _execute_with_session(operation):
    """Helper function to execute database operations with session management"""
    with SessionLocal() as db_session:
        return operation(db_session)


def register_author(create_user_request: CreateAuthorRequest) -> AuthorDetails:
    # Check for existing author to return required error shape on duplicates
    _execute_with_session(lambda db: check_author_exists(db=db, email=create_user_request.email))
    registered_user = _create_user(
        create_user_request=create_user_request
    )
    return registered_user

def _create_user(create_user_request: CreateAuthorRequest) -> AuthorDetails:
    new_author = Author(**create_user_request.model_dump())
    new_author.created_by = create_user_request.email
    _validate_password(new_author.password)
    hashed_password = get_hashed_password(new_author.password)
    new_author.password = hashed_password
    saved_author = _execute_with_session(lambda db: save_author(db=db, author=new_author))
    _send_verification_email(email=saved_author.email)
    return AuthorDetails(
        first_name=saved_author.first_name,
        last_name=saved_author.last_name,
        email=saved_author.email,
        status=AuthorStatus.PENDING_VERIFICATION,
        message=REGISTRATION_MESSAGE
    )

def _validate_password(password: str):
    if not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PASSWORD_EMPTY)
    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PASSWORD_LENGTH_INVALID)


def _generate_author_verification_token(email: str) -> str:
    expires_delta = timedelta(hours=24)
    expire = datetime.now(timezone.utc) + expires_delta

    payload = TokenPayload(
        email=email,
        iss=get("JWT_ISSUER"),
        aud=get("JWT_AUD"),
        iat=datetime.now(timezone.utc),
        exp=expire,
        typ="author_email_verification"
    )
    return jwt.encode(payload.model_dump(), get("JWT_SECRET_KEY"), algorithm=get("JWT_ALGORITHM"))

def _send_verification_email(email: str) -> None:
    token = _generate_author_verification_token(email=email)
    frontend_endpoint = get("WEBUDDHIST_STUDIO_BASE_URL")       
    verify_link = f"{frontend_endpoint}/verify-email?token={token}"

    template_path = Path(__file__).parent / "templates" / "verify_email_template.html"
    with open(template_path, "r") as f:
        template = Template(f.read())
    html_content = template.render(verify_link=verify_link)
    send_email(
        to_email=email,
        subject="Verify your Pecha account",
        message=html_content
    )




def verify_author_email(token: str) -> AuthorVerificationResponse:
    try:
        payload = jwt.decode(
            token,
            get("JWT_SECRET_KEY"),
            algorithms=[get("JWT_ALGORITHM")],
            audience=get("JWT_AUD")
        )
        if payload.get("typ") != "author_email_verification":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=TOKEN_INVALID)
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=TOKEN_INVALID)
        with SessionLocal() as db_session:
            author = get_author_by_email(db=db_session, email=email) # need validation for author
            if not author.is_verified:
                author.is_verified = True
                update_author(db=db_session, author=author)
                message = EMAIL_VERIFIED_SUCCESS
            else:
                message = EMAIL_ALREADY_VERIFIED
            return AuthorVerificationResponse(
                email=author.email,
                status=AuthorStatus.INACTIVE,
                message=message
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=TOKEN_EXPIRED)
    except HTTPException as e:
        # Re-raise expected HTTP errors (type/payload validation) without masking
        raise e
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=TOKEN_INVALID)


def authenticate_author(email: str, password: str):
    import logging
    logger = logging.getLogger(__name__)
    with SessionLocal() as db_session:
        author = get_author_by_email(db=db_session, email=email)
        logger.info(f"Login attempt for email: {email}")
        logger.info(f"Author found: {author.email}, has password: {author.password is not None}")
        password_valid = verify_password(
            plain_password=password,
            hashed_password=author.password
        )
        logger.info(f"Password verification result: {password_valid}")
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=INVALID_EMAIL_PASSWORD
            )
        check_verified_author(author=author)
        return author

def check_verified_author(author: Author) -> bool:
    if not author.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = AUTHOR_NOT_VERIFIED)
    elif not author.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = AUTHOR_NOT_ACTIVE)    
    

def authenticate_and_generate_tokens(email: str, password: str):
    author = authenticate_author(email=email, password=password)
    return generate_token_author(author)

def generate_author_token_data(author: Author):
    if not all([author.email, author.first_name, author.last_name]):
        return None
    data = {
        "email": author.email,
        "name": _get_author_full_name(author),
        "iss": get("JWT_ISSUER"),
        "aud": get("JWT_AUD"),
        "iat": datetime.now(timezone.utc)
    }
    return data

def generate_token_author(author: Author):
    data = generate_author_token_data(author)
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )
    return AuthorLoginResponse(
        user=AuthorInfo(
            name=_get_author_full_name(author),
            image_url=author.image_url
        ),
        auth=token_response
    )


def request_reset_password(email: str):
    with SessionLocal() as db_session:
        current_user = get_author_by_email(
            db=db_session,
            email=email
        )
        reset_token = secrets.token_urlsafe(32)
        token_expiry = datetime.now(timezone.utc) + timedelta(minutes=30)
        password_reset = AuthorPasswordReset(
            email=current_user.email,
            reset_token=reset_token,
            token_expiry=token_expiry
        )
        save_password_reset(
            db=db_session,
            password_reset=password_reset
        )
        reset_link = f"{get('WEBUDDHIST_STUDIO_BASE_URL')}/reset-password?token={reset_token}&email={email}"
        send_reset_email(email=email, reset_link=reset_link)
        return {"message": "If the email exists in our system, a password reset email has been sent."}


def update_password(token: str, password: str):
    with SessionLocal() as db_session:
        reset_entry = get_password_reset_by_token_for_author(
            db=db_session,
            token=token
        )
        if reset_entry is None or reset_entry.token_expiry < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
        current_user = get_author_by_email(
            db=db_session,
            email=reset_entry.email
        )
        _validate_password(password)
        hashed_password = get_hashed_password(password)
        current_user.password = hashed_password
        updated_user = update_author(db=db_session, author=current_user)
        return updated_user

def re_verify_email(email: str) -> EmailReVerificationResponse:
    with SessionLocal() as db_session:
        author = get_author_by_email(db=db_session, email=email)
        if not author:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=AUTHOR_NOT_FOUND).model_dump())
        _send_verification_email(email=email)
    return EmailReVerificationResponse(message=EMAIL_IS_SENT)


def refresh_access_token(refresh_token: str):
    try:
        payload = _validate_token(refresh_token)
        author_email = payload.get("email")
        if author_email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        with SessionLocal() as db_session:
            author = get_author_by_email(
                db=db_session,
                email=author_email
            )
            data = generate_author_token_data(author)
            access_token = create_access_token(data=data)
            return RefreshTokenResponse(
                access_token=access_token,
                token_type="Bearer"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

def _validate_token(token: str):
    return jwt.decode(
        token,
        get("JWT_SECRET_KEY"),
        algorithms=[get("JWT_ALGORITHM")],
        audience=get("JWT_AUD")
    )

