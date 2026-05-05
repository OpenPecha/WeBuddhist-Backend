from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_annotations_pagination_pagination_id_response_404 import (
    GetV2AnnotationsPaginationPaginationIdResponse404,
)
from ...models.get_v2_annotations_pagination_pagination_id_response_500 import (
    GetV2AnnotationsPaginationPaginationIdResponse500,
)
from ...models.pagination_output import PaginationOutput
from ...types import Response


def _get_kwargs(
    pagination_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/annotations/pagination/{pagination_id}".format(
            pagination_id=quote(str(pagination_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetV2AnnotationsPaginationPaginationIdResponse404
    | GetV2AnnotationsPaginationPaginationIdResponse500
    | PaginationOutput
    | None
):
    if response.status_code == 200:
        response_200 = PaginationOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2AnnotationsPaginationPaginationIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2AnnotationsPaginationPaginationIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2AnnotationsPaginationPaginationIdResponse404
    | GetV2AnnotationsPaginationPaginationIdResponse500
    | PaginationOutput
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    pagination_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetV2AnnotationsPaginationPaginationIdResponse404
    | GetV2AnnotationsPaginationPaginationIdResponse500
    | PaginationOutput
]:
    """Retrieve pagination annotation by ID

     Fetch a specific pagination annotation with volume and page information

    Args:
        pagination_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2AnnotationsPaginationPaginationIdResponse404 | GetV2AnnotationsPaginationPaginationIdResponse500 | PaginationOutput]
    """

    kwargs = _get_kwargs(
        pagination_id=pagination_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    pagination_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetV2AnnotationsPaginationPaginationIdResponse404
    | GetV2AnnotationsPaginationPaginationIdResponse500
    | PaginationOutput
    | None
):
    """Retrieve pagination annotation by ID

     Fetch a specific pagination annotation with volume and page information

    Args:
        pagination_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2AnnotationsPaginationPaginationIdResponse404 | GetV2AnnotationsPaginationPaginationIdResponse500 | PaginationOutput
    """

    return sync_detailed(
        pagination_id=pagination_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    pagination_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetV2AnnotationsPaginationPaginationIdResponse404
    | GetV2AnnotationsPaginationPaginationIdResponse500
    | PaginationOutput
]:
    """Retrieve pagination annotation by ID

     Fetch a specific pagination annotation with volume and page information

    Args:
        pagination_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2AnnotationsPaginationPaginationIdResponse404 | GetV2AnnotationsPaginationPaginationIdResponse500 | PaginationOutput]
    """

    kwargs = _get_kwargs(
        pagination_id=pagination_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    pagination_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetV2AnnotationsPaginationPaginationIdResponse404
    | GetV2AnnotationsPaginationPaginationIdResponse500
    | PaginationOutput
    | None
):
    """Retrieve pagination annotation by ID

     Fetch a specific pagination annotation with volume and page information

    Args:
        pagination_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2AnnotationsPaginationPaginationIdResponse404 | GetV2AnnotationsPaginationPaginationIdResponse500 | PaginationOutput
    """

    return (
        await asyncio_detailed(
            pagination_id=pagination_id,
            client=client,
        )
    ).parsed
