from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..db import database
from starlette import status
from .auth_service import authenticate_and_generate_tokens, refresh_access_token, register_user_with_source, \
    request_reset_password, update_password, create_user, exchange_phone_token, link_phone_identity
from .auth_models import CreateUserRequest, UserLoginRequest, RefreshTokenRequest, PasswordResetRequest, \
    ResetPasswordRequest, UserLoginResponse, RefreshTokenResponse, CreateSocialUserRequest, \
    PhoneExchangeRequest, PhoneExchangeResponse, PhoneLinkRequest, PhoneLinkResponse
from .auth_enums import RegistrationSource
from typing import Annotated

oauth2_scheme = HTTPBearer()
auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentications"],
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(create_user_request: CreateUserRequest) -> UserLoginResponse:
    registration_source = RegistrationSource.EMAIL
    return register_user_with_source(
        create_user_request=create_user_request,
        registration_source=registration_source
    )

@auth_router.post("/social_register", status_code=status.HTTP_201_CREATED)
def register_user(create_social_user_request: CreateSocialUserRequest):
    registration_source = RegistrationSource.EMAIL
    if create_social_user_request.platform:
        registration_source =  create_social_user_request.platform
    return create_user(
        create_user_request=create_social_user_request.create_user_request,
        registration_source=registration_source
    )

@auth_router.post("/login", status_code=status.HTTP_200_OK)
def login_user(user_login_request: UserLoginRequest) -> UserLoginResponse:
    return authenticate_and_generate_tokens(
        email=user_login_request.email,
        password=user_login_request.password
    )


@auth_router.post("/phone/exchange", status_code=status.HTTP_200_OK)
def phone_exchange(request: PhoneExchangeRequest) -> PhoneExchangeResponse:
    return exchange_phone_token(request)


@auth_router.post("/phone/link", status_code=status.HTTP_200_OK)
def phone_link(
    request: PhoneLinkRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> PhoneLinkResponse:
    return link_phone_identity(
        backend_token=authentication_credential.credentials,
        auth0_token=request.auth0_token,
    )


@auth_router.post("/refresh-token", status_code=status.HTTP_200_OK)
def refresh_token(refresh_token_request: RefreshTokenRequest) -> RefreshTokenResponse:
    return refresh_access_token(refresh_token_request.token)


@auth_router.post("/request-reset-password", status_code=status.HTTP_202_ACCEPTED)
def password_reset_request(reset_request: PasswordResetRequest):
    request_reset_password(email=reset_request.email)


@auth_router.post("/reset-password", status_code=status.HTTP_200_OK)
def password_reset(reset_password_request: ResetPasswordRequest,
                   authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
    update_password(token=authentication_credential.credentials, password=reset_password_request.password)
