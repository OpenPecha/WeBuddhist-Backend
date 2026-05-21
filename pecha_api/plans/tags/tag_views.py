from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.plans.tags.tag_response_models import CreateTagRequest, TagDTO, TagsListResponse, UpdateTagRequest
from pecha_api.plans.tags.tag_service import (
    create_new_tag,
    delete_tag,
    get_cms_tag_detail,
    get_cms_tags_list,
    update_existing_tag,
)

oauth2_scheme = HTTPBearer()

cms_tags_router = APIRouter(
    prefix="/cms/tags",
    tags=["CMS Tags"],
)


@cms_tags_router.post("", status_code=status.HTTP_201_CREATED, response_model=TagDTO)
async def create_tag(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    create_tag_request: CreateTagRequest,
):
    return create_new_tag(
        token=authentication_credential.credentials,
        create_tag_request=create_tag_request,
    )


@cms_tags_router.put("/{tag_id}", status_code=status.HTTP_200_OK, response_model=TagDTO)
async def update_tag(
    tag_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    update_tag_request: UpdateTagRequest,
):
    return update_existing_tag(
        token=authentication_credential.credentials,
        tag_id=tag_id,
        update_tag_request=update_tag_request,
    )


@cms_tags_router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag(
    tag_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    delete_tag(token=authentication_credential.credentials, tag_id=tag_id)


@cms_tags_router.get("", status_code=status.HTTP_200_OK, response_model=TagsListResponse)
async def list_tags(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    search: Annotated[Optional[str], Query(description="Search by tag name")] = None,
    skip: Annotated[int, Query()] = 0,
    limit: Annotated[int, Query()] = 10,
):
    return get_cms_tags_list(
        token=authentication_credential.credentials,
        search=search,
        skip=skip,
        limit=limit,
    )


@cms_tags_router.get("/{tag_id}", status_code=status.HTTP_200_OK, response_model=TagDTO)
async def get_tag(
    tag_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return get_cms_tag_detail(
        token=authentication_credential.credentials,
        tag_id=tag_id,
    )
