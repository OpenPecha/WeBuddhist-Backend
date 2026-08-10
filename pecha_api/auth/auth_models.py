from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from pecha_api.auth.auth_enums import RegistrationSource


class CreateUserRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str

class CreateSocialUserRequest(BaseModel):
    create_user_request: CreateUserRequest
    platform: RegistrationSource

class UserLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserInfo(BaseModel):
    name: str
    avatar_url: Optional[str] = None


class UserLoginResponse(BaseModel):
    user: UserInfo
    auth: TokenResponse


class PhoneExchangeRequest(BaseModel):
    auth0_token: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PhoneExchangeResponse(BaseModel):
    user_id: UUID
    phone_number: str
    message: str
    user: UserInfo
    auth: TokenResponse


class PhoneLinkRequest(BaseModel):
    auth0_token: str


class PhoneLinkResponse(BaseModel):
    user_id: UUID
    phone_number: str
    message: str


class RefreshTokenRequest(BaseModel):
    token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str


class PasswordResetRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    password: str

class PropsResponse(BaseModel):
    client_id: str
    domain: str
    audience: str