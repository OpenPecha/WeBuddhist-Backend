from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from pecha_api.plans.auth.cms_auth_deps import get_cms_author_token
from pecha_api.region_restrictions.region_restriction_admin_service import (
    create_admin_china_restricted_item,
    delete_admin_china_restricted_item,
    list_admin_china_restricted_items,
)
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_response_models import (
    ChinaRestrictedItemDTO,
    ChinaRestrictedItemListResponse,
    CreateChinaRestrictedItemRequest,
)

cms_china_restrictions_router = APIRouter(
    prefix="/cms/admin/china-restrictions",
    tags=["CMS Admin China Restrictions"],
)


@cms_china_restrictions_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=ChinaRestrictedItemListResponse,
)
def get_cms_china_restricted_items(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    item_type: Annotated[Optional[RestrictedItemType], Query()] = None,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return list_admin_china_restricted_items(
        token=token,
        skip=skip,
        limit=limit,
        item_type=item_type,
    )


@cms_china_restrictions_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ChinaRestrictedItemDTO,
)
def post_cms_china_restricted_item(
    body: CreateChinaRestrictedItemRequest,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return create_admin_china_restricted_item(token=token, body=body)


@cms_china_restrictions_router.delete(
    "/{row_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_cms_china_restricted_item(
    row_id: UUID,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    delete_admin_china_restricted_item(token=token, row_id=row_id)
