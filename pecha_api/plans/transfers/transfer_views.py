from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from pecha_api.plans.auth.cms_auth_deps import get_cms_author_token
from pecha_api.plans.transfers.transfer_enums import ContentTransferStatus
from pecha_api.plans.transfers.transfer_response_models import (
    CreateTransferRequestBody,
    TransferRequestCreatedResponse,
    TransferRequestDTO,
    TransferRequestListResponse,
)
from pecha_api.plans.transfers.transfer_service import (
    accept_transfer_request,
    create_plan_transfer_request,
    create_series_transfer_request,
    list_incoming_transfer_requests,
    list_incoming_transfer_requests_for_group,
    list_outgoing_transfer_requests,
    list_outgoing_transfer_requests_for_group,
    reject_transfer_request,
    revoke_transfer_request,
)

CMS_CONTENT_TRANSFERS_TAG = "CMS Content Transfers"

cms_transfers_router = APIRouter(prefix="/cms/transfer-requests", tags=[CMS_CONTENT_TRANSFERS_TAG])


@cms_transfers_router.get("/incoming", status_code=status.HTTP_200_OK, response_model=TransferRequestListResponse)
def get_incoming_transfer_requests(
    status_filter: Annotated[Optional[ContentTransferStatus], Query(alias="status")] = None,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return list_incoming_transfer_requests(token=token, status_filter=status_filter)


@cms_transfers_router.get("/outgoing", status_code=status.HTTP_200_OK, response_model=TransferRequestListResponse)
def get_outgoing_transfer_requests(
    status_filter: Annotated[Optional[ContentTransferStatus], Query(alias="status")] = None,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return list_outgoing_transfer_requests(token=token, status_filter=status_filter)


@cms_transfers_router.post("/{transfer_id}/accept", status_code=status.HTTP_200_OK, response_model=TransferRequestDTO)
def post_accept_transfer_request(
    transfer_id: UUID,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return accept_transfer_request(token=token, transfer_id=transfer_id)


@cms_transfers_router.post("/{transfer_id}/reject", status_code=status.HTTP_200_OK, response_model=TransferRequestDTO)
def post_reject_transfer_request(
    transfer_id: UUID,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return reject_transfer_request(token=token, transfer_id=transfer_id)


@cms_transfers_router.post("/{transfer_id}/revoke", status_code=status.HTTP_200_OK, response_model=TransferRequestDTO)
def post_revoke_transfer_request(
    transfer_id: UUID,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return revoke_transfer_request(token=token, transfer_id=transfer_id)


plan_transfers_router = APIRouter(prefix="/cms/plans", tags=[CMS_CONTENT_TRANSFERS_TAG])


@plan_transfers_router.post(
    "/{plan_id}/transfer-requests",
    status_code=status.HTTP_201_CREATED,
    response_model=TransferRequestCreatedResponse,
)
def post_plan_transfer_request(
    plan_id: UUID,
    body: CreateTransferRequestBody,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return create_plan_transfer_request(token=token, plan_id=plan_id, body=body)


series_transfers_router = APIRouter(prefix="/cms/series", tags=[CMS_CONTENT_TRANSFERS_TAG])


@series_transfers_router.post(
    "/{series_id}/transfer-requests",
    status_code=status.HTTP_201_CREATED,
    response_model=TransferRequestCreatedResponse,
)
def post_series_transfer_request(
    series_id: UUID,
    body: CreateTransferRequestBody,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return create_series_transfer_request(token=token, series_id=series_id, body=body)


group_transfers_router = APIRouter(
    prefix="/cms/author/groups/{group_id}/transfer-requests",
    tags=[CMS_CONTENT_TRANSFERS_TAG],
)


@group_transfers_router.get("/incoming", status_code=status.HTTP_200_OK, response_model=TransferRequestListResponse)
def get_group_incoming_transfer_requests(
    group_id: UUID,
    status_filter: Annotated[Optional[ContentTransferStatus], Query(alias="status")] = None,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return list_incoming_transfer_requests_for_group(
        token=token,
        group_id=group_id,
        status_filter=status_filter,
    )


@group_transfers_router.get("/outgoing", status_code=status.HTTP_200_OK, response_model=TransferRequestListResponse)
def get_group_outgoing_transfer_requests(
    group_id: UUID,
    status_filter: Annotated[Optional[ContentTransferStatus], Query(alias="status")] = None,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return list_outgoing_transfer_requests_for_group(
        token=token,
        group_id=group_id,
        status_filter=status_filter,
    )
