from typing import Annotated, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.plans.groups.groups_enums import AuthorGroupInviteStatus, AuthorGroupType
from pecha_api.plans.groups.groups_response_models import (
    AuthorGroupDetailDTO,
    AuthorGroupListResponse,
    CreateAuthorGroupRequest,
    CreateGroupInviteRequest,
    GroupInviteCreatedResponse,
    GroupInviteDTO,
    GroupInviteListResponse,
    PublicAuthorGroupDetailDTO,
    PublicAuthorGroupListResponse,
    PublicAuthorGroupSummaryDTO,
    ReplaceGroupSocialLinksRequest,
    ReplaceGroupTagsRequest,
    UpdateAuthorGroupRequest,
    TransferGroupOwnershipRequest,
    UpdateGroupMemberRoleRequest,
)
from pecha_api.plans.groups.groups_service import (
    accept_group_invite_by_id,
    create_author_group,
    create_group_member_invite,
    delete_group_member,
    follow_group,
    get_author_group_detail,
    get_cms_group_detail,
    get_followed_group,
    get_joined_group,
    join_group,
    leave_group,
    list_cms_groups,
    list_followed_groups,
    list_joined_groups,
    list_group_invites,
    list_my_pending_group_invites,
    list_public_groups,
    reject_group_invite_by_id,
    replace_group_social_links_by_id,
    replace_group_tags,
    revoke_group_invite,
    unfollow_group,
    update_author_group,
    transfer_group_ownership,
    update_group_member_role,
)

oauth2_scheme = HTTPBearer()

cms_groups_router = APIRouter(prefix="/cms/author/groups", tags=["CMS Author Groups"])
public_groups_router = APIRouter(prefix="/author/groups", tags=["Author Groups"])
user_groups_router = APIRouter(
    prefix="/users/me/following/author/groups",
    tags=["Author Groups"],
)
user_joined_groups_router = APIRouter(
    prefix="/users/me/joined/author/groups",
    tags=["Author Groups"],
)


@cms_groups_router.post("", status_code=status.HTTP_201_CREATED, response_model=AuthorGroupDetailDTO)
def post_cms_group(
    create_group_request: CreateAuthorGroupRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return create_author_group(
        token=authentication_credential.credentials,
        request=create_group_request,
    )


def _update_cms_group(
    group_id: UUID,
    update_group_request: UpdateAuthorGroupRequest,
    token: str,
) -> AuthorGroupDetailDTO:
    return update_author_group(
        token=token,
        group_id=group_id,
        request=update_group_request,
    )


@cms_groups_router.put("/{group_id}", status_code=status.HTTP_200_OK, response_model=AuthorGroupDetailDTO)
def put_cms_group(
    group_id: UUID,
    update_group_request: UpdateAuthorGroupRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return _update_cms_group(
        group_id=group_id,
        update_group_request=update_group_request,
        token=authentication_credential.credentials,
    )


@cms_groups_router.patch("/{group_id}", status_code=status.HTTP_200_OK, response_model=AuthorGroupDetailDTO)
def patch_cms_group(
    group_id: UUID,
    update_group_request: UpdateAuthorGroupRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return _update_cms_group(
        group_id=group_id,
        update_group_request=update_group_request,
        token=authentication_credential.credentials,
    )


@cms_groups_router.get("/{group_id}", status_code=status.HTTP_200_OK, response_model=AuthorGroupDetailDTO)
def get_cms_group(
    group_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    language: Annotated[Optional[str], Query(description="Filter group metadata by language (e.g. 'en', 'bo', 'zh')")] = None,
):
    return get_cms_group_detail(
        token=authentication_credential.credentials,
        group_id=group_id,
        language=language,
    )


@cms_groups_router.get("", status_code=status.HTTP_200_OK, response_model=AuthorGroupListResponse)
def get_cms_groups(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    search: Annotated[Optional[str], Query()] = None,
    language: Annotated[Optional[str], Query()] = None,
    tag_id: Annotated[Optional[UUID], Query()] = None,
    is_public: Annotated[Optional[bool], Query(description="Filter by public visibility; omit to include all groups")] = None,
    group_type: Annotated[Optional[AuthorGroupType], Query(description="Filter by group type: PAGE or COMMUNITY")] = None,
    for_transfer: Annotated[bool, Query(description="When true, list all groups for transfer target selection")] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return list_cms_groups(
        token=authentication_credential.credentials,
        search=search,
        language=language,
        tag_id=tag_id,
        is_public=is_public,
        group_type=group_type,
        for_transfer=for_transfer,
        skip=skip,
        limit=limit,
    )


@cms_groups_router.put("/{group_id}/tags", status_code=status.HTTP_200_OK, response_model=AuthorGroupDetailDTO)
def put_cms_group_tags(
    group_id: UUID,
    request: ReplaceGroupTagsRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return replace_group_tags(
        token=authentication_credential.credentials,
        group_id=group_id,
        request=request,
    )


@cms_groups_router.put("/{group_id}/social-links", status_code=status.HTTP_200_OK, response_model=AuthorGroupDetailDTO)
def put_cms_group_social_links(
    group_id: UUID,
    request: ReplaceGroupSocialLinksRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return replace_group_social_links_by_id(
        token=authentication_credential.credentials,
        group_id=group_id,
        request=request,
    )


@cms_groups_router.post("/{group_id}/members/invites", status_code=status.HTTP_201_CREATED, response_model=GroupInviteCreatedResponse)
def post_cms_group_invite(
    group_id: UUID,
    request: CreateGroupInviteRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return create_group_member_invite(
        token=authentication_credential.credentials,
        group_id=group_id,
        request=request,
    )


@cms_groups_router.get(
    "/{group_id}/members/invites",
    status_code=status.HTTP_200_OK,
    response_model=GroupInviteListResponse,
)
def get_cms_group_invites(
    group_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    status_filter: Annotated[Optional[AuthorGroupInviteStatus], Query(alias="status")] = None,
):
    return list_group_invites(
        token=authentication_credential.credentials,
        group_id=group_id,
        status_filter=status_filter,
    )


@cms_groups_router.get(
    "/invites/me",
    status_code=status.HTTP_200_OK,
    response_model=GroupInviteListResponse,
)
def get_my_pending_group_invites(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return list_my_pending_group_invites(token=authentication_credential.credentials)


@cms_groups_router.post(
    "/invites/{invite_id}/accept",
    status_code=status.HTTP_200_OK,
    response_model=AuthorGroupDetailDTO,
)
def post_accept_group_invite_by_id(
    invite_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return accept_group_invite_by_id(
        token=authentication_credential.credentials,
        invite_id=invite_id,
    )


@cms_groups_router.post(
    "/invites/{invite_id}/reject",
    status_code=status.HTTP_200_OK,
    response_model=GroupInviteDTO,
)
def post_reject_group_invite_by_id(
    invite_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return reject_group_invite_by_id(
        token=authentication_credential.credentials,
        invite_id=invite_id,
    )


@cms_groups_router.post("/{group_id}/members/invites/{invite_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
def post_revoke_group_invite(
    group_id: UUID,
    invite_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    revoke_group_invite(
        token=authentication_credential.credentials,
        group_id=group_id,
        invite_id=invite_id,
    )
    return None


@cms_groups_router.post(
    "/{group_id}/transfer-ownership",
    status_code=status.HTTP_200_OK,
    response_model=AuthorGroupDetailDTO,
)
def post_transfer_group_ownership(
    group_id: UUID,
    request: TransferGroupOwnershipRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return transfer_group_ownership(
        token=authentication_credential.credentials,
        group_id=group_id,
        new_owner_author_id=request.new_owner_author_id,
    )


@cms_groups_router.patch("/{group_id}/members/{author_id}/role", status_code=status.HTTP_200_OK, response_model=AuthorGroupDetailDTO)
def patch_group_member_role(
    group_id: UUID,
    author_id: UUID,
    request: UpdateGroupMemberRoleRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return update_group_member_role(
        token=authentication_credential.credentials,
        group_id=group_id,
        author_id=author_id,
        request=request,
    )


@cms_groups_router.delete("/{group_id}/members/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_member_by_id(
    group_id: UUID,
    author_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    delete_group_member(
        token=authentication_credential.credentials,
        group_id=group_id,
        author_id=author_id,
    )
    return None


@public_groups_router.get("/{group_id}", status_code=status.HTTP_200_OK, response_model=PublicAuthorGroupDetailDTO)
def get_public_group(
    group_id: UUID,
    language: Annotated[Optional[str], Query(description="Filter group metadata by language (e.g. 'en', 'bo', 'zh')")] = None,
):
    return get_author_group_detail(group_id=group_id, require_public=True, language=language)


@public_groups_router.get("", status_code=status.HTTP_200_OK, response_model=PublicAuthorGroupListResponse)
def get_public_groups(
    search: Annotated[Optional[str], Query()] = None,
    language: Annotated[Optional[str], Query()] = None,
    tag_id: Annotated[Optional[UUID], Query()] = None,
    group_type: Annotated[
        AuthorGroupType,
        Query(description="Filter by group type: PAGE or COMMUNITY"),
    ] = AuthorGroupType.COMMUNITY,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return list_public_groups(
        search=search,
        language=language,
        tag_id=tag_id,
        group_type=group_type,
        skip=skip,
        limit=limit,
    )


@public_groups_router.post("/{group_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def post_follow_group(
    group_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    follow_group(token=authentication_credential.credentials, group_id=group_id)
    return None


@public_groups_router.delete("/{group_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def delete_follow_group(
    group_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    unfollow_group(token=authentication_credential.credentials, group_id=group_id)
    return None


@public_groups_router.post("/{group_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def post_join_group(
    group_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    join_group(token=authentication_credential.credentials, group_id=group_id)
    return None


@public_groups_router.delete("/{group_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def delete_join_group(
    group_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    leave_group(token=authentication_credential.credentials, group_id=group_id)
    return None


@user_groups_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Union[PublicAuthorGroupListResponse, PublicAuthorGroupSummaryDTO],
)
def get_my_followed_groups(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    group_id: Annotated[Optional[UUID], Query(description="Return this group if the user is following it")] = None,
    language: Annotated[Optional[str], Query(description="Filter group metadata by language (e.g. 'en', 'bo', 'zh')")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    if group_id is not None:
        return get_followed_group(
            token=authentication_credential.credentials,
            group_id=group_id,
            language=language,
        )
    return list_followed_groups(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit,
    )


@user_joined_groups_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Union[PublicAuthorGroupListResponse, PublicAuthorGroupSummaryDTO],
)
def get_my_joined_groups(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    group_id: Annotated[Optional[UUID], Query(description="Return this group if the user has joined it")] = None,
    language: Annotated[Optional[str], Query(description="Filter group metadata by language (e.g. 'en', 'bo', 'zh')")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    if group_id is not None:
        return get_joined_group(
            token=authentication_credential.credentials,
            group_id=group_id,
            language=language,
        )
    return list_joined_groups(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit,
    )
