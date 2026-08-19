from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

from pecha_api.plans.auth.plan_auth_enums import AuthorStatus

class CreateAuthorRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

class AuthorDetails(BaseModel):
    first_name: str
    last_name: str
    email: str
    status: AuthorStatus
    message: str

class AuthorResponse(BaseModel):
    author: AuthorDetails

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class AuthorInfo(BaseModel):
    name: str
    image_url: Optional[str] = None


class AuthorLoginResponse(BaseModel):
    user: AuthorInfo
    auth: TokenResponse


class PhoneExchangeRequest(BaseModel):
    auth0_token: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PhoneExchangeResponse(BaseModel):
    author_id: UUID
    phone_number: str
    status: AuthorStatus
    message: str
    user: AuthorInfo
    auth: Optional[TokenResponse] = None


class PhoneLinkRequest(BaseModel):
    auth0_token: str


class PhoneLinkResponse(BaseModel):
    author_id: UUID
    phone_number: str
    message: str


class GoogleExchangeRequest(BaseModel):
    auth0_token: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class GoogleExchangeResponse(BaseModel):
    author_id: UUID
    email: str
    status: AuthorStatus
    message: str
    user: AuthorInfo
    auth: Optional[TokenResponse] = None


class EmailExchangeRequest(BaseModel):
    auth0_token: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class EmailExchangeResponse(BaseModel):
    author_id: UUID
    email: str
    status: AuthorStatus
    message: str
    user: AuthorInfo
    auth: Optional[TokenResponse] = None


class AuthorLoginRequest(BaseModel):
    email: str
    password: str

class TokenPayload(BaseModel):
    email: str
    iss: str
    aud: str
    iat: datetime
    exp: datetime
    typ: str

class AuthorVerificationResponse(BaseModel):
    email: str
    status: AuthorStatus
    message: str

class ResponseError(BaseModel):
    error: str
    message: str

class PasswordResetRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class EmailReVerificationResponse(BaseModel):
    message: str

class RefreshTokenRequest(BaseModel):
    token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str