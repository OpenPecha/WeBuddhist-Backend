from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from pecha_api.plans.auth.cms_auth_deps import get_cms_author_token
from .plan_auth_models import (
    AuthorDetails,
    AuthorLoginRequest,
    AuthorLoginResponse,
    AuthorVerificationResponse,
    CreateAuthorRequest,
    EmailReVerificationResponse,
    PasswordResetRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResetPasswordRequest,
)
from .plan_auth_services import (
    authenticate_and_generate_tokens,
    refresh_access_token,
    register_author,
    re_verify_email,
    request_reset_password,
    update_password,
    verify_author_email,
)

plan_auth_router = APIRouter(
    prefix="/cms/auth",
    tags=["Plan Authentications"],
)


@plan_auth_router.post("/register", status_code=status.HTTP_202_ACCEPTED, response_model=AuthorDetails)
def register_user(create_user_request: CreateAuthorRequest) -> AuthorDetails:
    return register_author(create_user_request=create_user_request)


@plan_auth_router.get("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(token: Annotated[str, Depends(get_cms_author_token)]) -> AuthorVerificationResponse:
    return verify_author_email(token=token)


@plan_auth_router.post("/email-re-verification", status_code=status.HTTP_202_ACCEPTED, response_model=EmailReVerificationResponse)
def email_re_verification(email: str):
    return re_verify_email(email=email)


@plan_auth_router.post("/login", status_code=status.HTTP_200_OK)
def login_user(author_login_request: AuthorLoginRequest) -> AuthorLoginResponse:
    return authenticate_and_generate_tokens(
        email=author_login_request.email,
        password=author_login_request.password,
    )


@plan_auth_router.post("/request-reset-password", status_code=status.HTTP_202_ACCEPTED)
async def password_reset_request(reset_request: PasswordResetRequest):
    return request_reset_password(email=reset_request.email)


@plan_auth_router.post("/reset-password", status_code=status.HTTP_200_OK)
def password_reset(reset_password_request: ResetPasswordRequest):
    update_password(token=reset_password_request.token, password=reset_password_request.password)


@plan_auth_router.post("/refresh-token", status_code=status.HTTP_200_OK)
def refresh_token(refresh_token_request: RefreshTokenRequest) -> RefreshTokenResponse:
    return refresh_access_token(refresh_token_request.token)
