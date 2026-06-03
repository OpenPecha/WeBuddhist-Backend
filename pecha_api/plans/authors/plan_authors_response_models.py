from typing import Optional, List

from pydantic import BaseModel
from uuid import UUID
from pecha_api.users.users_enums import SocialProfile


class SocialMediaProfile(BaseModel):
    account: SocialProfile
    url: str

class ImageUrlModel(BaseModel):
    thumbnail: str
    medium: str
    original: str 

class AuthorUpdateResponse(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    email: str
    image_url: str
    image_key: str
    bio: Optional[str] = None


class AuthorInfoRequest(BaseModel):
    firstname: str
    lastname: str
    image_url: Optional[str] = None
    bio: Optional[str] = None
    social_profiles: List[SocialMediaProfile]

class AuthorInfoResponse(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    email: str
    is_admin: bool = False
    image_url: Optional[str] = None
    bio: Optional[str] = None
    social_profiles: List[SocialMediaProfile]

class AuthorInfoPublicResponse(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    email: str
    image: Optional[ImageUrlModel] = None
    bio: Optional[str] = None
    social_profiles: List[SocialMediaProfile]

class AuthorsResponse(BaseModel):
    authors: List[AuthorInfoResponse]
    skip: int
    limit: int
    total: int

class AuthorPlanDTO(BaseModel):
    id: UUID
    title: str
    description: str
    language: str
    total_days: int
    subscription_count: int
    image: Optional[ImageUrlModel] = None

class AuthorPlansResponse(BaseModel):
    plans: List[AuthorPlanDTO]
    skip: int
    limit: int
    total: int

class AuthorPlanAggregate(BaseModel):
    id: UUID
    title: str
    description: str
    language: str
    image_url: Optional[str] = None
    total_days: int
    subscription_count: int