from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_segments_segment_id_related_response_404 import GetV2SegmentsSegmentIdRelatedResponse404
from ...models.get_v2_segments_segment_id_related_response_500 import GetV2SegmentsSegmentIdRelatedResponse500
from ...models.segment_output import SegmentOutput
from ...types import Response


def _get_kwargs(
    segment_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/segments/{segment_id}/related".format(
            segment_id=quote(str(segment_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = SegmentOutput.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 404:
        response_404 = GetV2SegmentsSegmentIdRelatedResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2SegmentsSegmentIdRelatedResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput]
]:
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
) -> Response[
    GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput]
]:
    """Find related segments

     Find all segments that are aligned to a specific segment

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput]]
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
) -> GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput] | None:
    """Find related segments

     Find all segments that are aligned to a specific segment

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput]
    """

    return sync_detailed(
        segment_id=segment_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    segment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput]
]:
    """Find related segments

     Find all segments that are aligned to a specific segment

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput]]
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
) -> GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput] | None:
    """Find related segments

     Find all segments that are aligned to a specific segment

    Args:
        segment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2SegmentsSegmentIdRelatedResponse404 | GetV2SegmentsSegmentIdRelatedResponse500 | list[SegmentOutput]
    """

    return (
        await asyncio_detailed(
            segment_id=segment_id,
            client=client,
        )
    ).parsed
