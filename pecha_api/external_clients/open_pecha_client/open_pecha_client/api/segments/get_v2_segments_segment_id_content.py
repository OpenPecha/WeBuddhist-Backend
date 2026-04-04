from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_segments_segment_id_content_response_404 import GetV2SegmentsSegmentIdContentResponse404
from ...models.get_v2_segments_segment_id_content_response_500 import GetV2SegmentsSegmentIdContentResponse500
from ...types import Response


def _get_kwargs(
    segment_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/segments/{segment_id}/content".format(
            segment_id=quote(str(segment_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str | None:
    if response.status_code == 200:
        response_200 = cast(str, response.json())
        return response_200

    if response.status_code == 404:
        response_404 = GetV2SegmentsSegmentIdContentResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2SegmentsSegmentIdContentResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    segment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str]:
    """Get segment text content

     Retrieve the base text content for a segment based on its character span

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str]
    """

    kwargs = _get_kwargs(
        segment_id=segment_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    segment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str | None:
    """Get segment text content

     Retrieve the base text content for a segment based on its character span

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str
    """

    return sync_detailed(
        segment_id=segment_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    segment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str]:
    """Get segment text content

     Retrieve the base text content for a segment based on its character span

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str]
    """

    kwargs = _get_kwargs(
        segment_id=segment_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    segment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str | None:
    """Get segment text content

     Retrieve the base text content for a segment based on its character span

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2SegmentsSegmentIdContentResponse404 | GetV2SegmentsSegmentIdContentResponse500 | str
    """

    return (
        await asyncio_detailed(
            segment_id=segment_id,
            client=client,
        )
    ).parsed
