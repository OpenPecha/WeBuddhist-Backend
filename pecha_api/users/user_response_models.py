from typing import List, Optional

from pydantic import BaseModel, field_validator
from .users_enums import SocialProfile

class SocialMediaProfile(BaseModel):
    account: SocialProfile
    url: str

class UserInfoRequest(BaseModel):
    firstname: str
    lastname: str
    title: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    educations: List[str]
    avatar_url : Optional[str] = None
    about_me: Optional[str] = None
    social_profiles: List[SocialMediaProfile]

class UserInfoResponse(BaseModel):
    firstname: str
    lastname: str
    username: str
    email: str
    title: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    educations: List[str]
    avatar_url: Optional[str] = None
    about_me: Optional[str] = None
    followers: int
    following: int
    social_profiles: List[SocialMediaProfile]

class PublisherInfoResponse(BaseModel):
    id: str
    username: str
    firstname: str
    lastname: str
    avatar_url: Optional[str] = None


class UpdateUsernameRequest(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 30:
            raise ValueError("Username must be at most 30 characters")
        return v


class UpdateUsernameResponse(BaseModel):
    message: str
    username: Optional[str] = None
    suggestions: Optional[List[str]] = None
