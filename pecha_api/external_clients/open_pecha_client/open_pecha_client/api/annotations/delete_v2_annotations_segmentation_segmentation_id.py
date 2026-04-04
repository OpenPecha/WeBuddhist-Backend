from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_v2_annotations_segmentation_segmentation_id_response_400 import (
    DeleteV2AnnotationsSegmentationSegmentationIdResponse400,
)
from ...models.delete_v2_annotations_segmentation_segmentation_id_response_404 import (
    DeleteV2AnnotationsSegmentationSegmentationIdResponse404,
)
from ...models.delete_v2_annotations_segmentation_segmentation_id_response_500 import (
    DeleteV2AnnotationsSegmentationSegmentationIdResponse500,
)
from ...types import Response


def _get_kwargs(
    segmentation_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v2/annotations/segmentation/{segmentation_id}".format(
            segmentation_id=quote(str(segmentation_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse400
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse404
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 400:
        response_400 = DeleteV2AnnotationsSegmentationSegmentationIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = DeleteV2AnnotationsSegmentationSegmentationIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = DeleteV2AnnotationsSegmentationSegmentationIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse400
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse404
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    segmentation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse400
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse404
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
]:
    """Delete segmentation annotation

     Permanently delete a standalone segmentation annotation and all its segments. If the segmentation is
    part of an alignment, this endpoint will return 400. Use DELETE
    /v2/annotations/alignment/{alignment_id} instead.

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteV2AnnotationsSegmentationSegmentationIdResponse400 | DeleteV2AnnotationsSegmentationSegmentationIdResponse404 | DeleteV2AnnotationsSegmentationSegmentationIdResponse500]
    """

    kwargs = _get_kwargs(
        segmentation_id=segmentation_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    segmentation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse400
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse404
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
    | None
):
    """Delete segmentation annotation

     Permanently delete a standalone segmentation annotation and all its segments. If the segmentation is
    part of an alignment, this endpoint will return 400. Use DELETE
    /v2/annotations/alignment/{alignment_id} instead.

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteV2AnnotationsSegmentationSegmentationIdResponse400 | DeleteV2AnnotationsSegmentationSegmentationIdResponse404 | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
    """

    return sync_detailed(
        segmentation_id=segmentation_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    segmentation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse400
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse404
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
]:
    """Delete segmentation annotation

     Permanently delete a standalone segmentation annotation and all its segments. If the segmentation is
    part of an alignment, this endpoint will return 400. Use DELETE
    /v2/annotations/alignment/{alignment_id} instead.

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteV2AnnotationsSegmentationSegmentationIdResponse400 | DeleteV2AnnotationsSegmentationSegmentationIdResponse404 | DeleteV2AnnotationsSegmentationSegmentationIdResponse500]
    """

    kwargs = _get_kwargs(
        segmentation_id=segmentation_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    segmentation_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse400
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse404
    | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
    | None
):
    """Delete segmentation annotation

     Permanently delete a standalone segmentation annotation and all its segments. If the segmentation is
    part of an alignment, this endpoint will return 400. Use DELETE
    /v2/annotations/alignment/{alignment_id} instead.

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteV2AnnotationsSegmentationSegmentationIdResponse400 | DeleteV2AnnotationsSegmentationSegmentationIdResponse404 | DeleteV2AnnotationsSegmentationSegmentationIdResponse500
    """

    return (
        await asyncio_detailed(
            segmentation_id=segmentation_id,
            client=client,
        )
    ).parsed
