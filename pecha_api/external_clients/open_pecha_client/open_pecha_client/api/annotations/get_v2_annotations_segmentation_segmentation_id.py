from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_annotations_segmentation_segmentation_id_response_404 import (
    GetV2AnnotationsSegmentationSegmentationIdResponse404,
)
from ...models.get_v2_annotations_segmentation_segmentation_id_response_500 import (
    GetV2AnnotationsSegmentationSegmentationIdResponse500,
)
from ...models.segmentation_output import SegmentationOutput
from ...types import Response


def _get_kwargs(
    segmentation_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/annotations/segmentation/{segmentation_id}".format(
            segmentation_id=quote(str(segmentation_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetV2AnnotationsSegmentationSegmentationIdResponse404
    | GetV2AnnotationsSegmentationSegmentationIdResponse500
    | SegmentationOutput
    | None
):
    if response.status_code == 200:
        response_200 = SegmentationOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2AnnotationsSegmentationSegmentationIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2AnnotationsSegmentationSegmentationIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2AnnotationsSegmentationSegmentationIdResponse404
    | GetV2AnnotationsSegmentationSegmentationIdResponse500
    | SegmentationOutput
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
    GetV2AnnotationsSegmentationSegmentationIdResponse404
    | GetV2AnnotationsSegmentationSegmentationIdResponse500
    | SegmentationOutput
]:
    """Retrieve segmentation annotation by ID

     Fetch a specific segmentation annotation with all its segments

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2AnnotationsSegmentationSegmentationIdResponse404 | GetV2AnnotationsSegmentationSegmentationIdResponse500 | SegmentationOutput]
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
    GetV2AnnotationsSegmentationSegmentationIdResponse404
    | GetV2AnnotationsSegmentationSegmentationIdResponse500
    | SegmentationOutput
    | None
):
    """Retrieve segmentation annotation by ID

     Fetch a specific segmentation annotation with all its segments

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2AnnotationsSegmentationSegmentationIdResponse404 | GetV2AnnotationsSegmentationSegmentationIdResponse500 | SegmentationOutput
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
    GetV2AnnotationsSegmentationSegmentationIdResponse404
    | GetV2AnnotationsSegmentationSegmentationIdResponse500
    | SegmentationOutput
]:
    """Retrieve segmentation annotation by ID

     Fetch a specific segmentation annotation with all its segments

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2AnnotationsSegmentationSegmentationIdResponse404 | GetV2AnnotationsSegmentationSegmentationIdResponse500 | SegmentationOutput]
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
    GetV2AnnotationsSegmentationSegmentationIdResponse404
    | GetV2AnnotationsSegmentationSegmentationIdResponse500
    | SegmentationOutput
    | None
):
    """Retrieve segmentation annotation by ID

     Fetch a specific segmentation annotation with all its segments

    Args:
        segmentation_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2AnnotationsSegmentationSegmentationIdResponse404 | GetV2AnnotationsSegmentationSegmentationIdResponse500 | SegmentationOutput
    """

    return (
        await asyncio_detailed(
            segmentation_id=segmentation_id,
            client=client,
        )
    ).parsed
