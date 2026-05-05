from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_editions_edition_id_segments_related_response_400 import (
    GetV2EditionsEditionIdSegmentsRelatedResponse400,
)
from ...models.get_v2_editions_edition_id_segments_related_response_404 import (
    GetV2EditionsEditionIdSegmentsRelatedResponse404,
)
from ...models.get_v2_editions_edition_id_segments_related_response_422 import (
    GetV2EditionsEditionIdSegmentsRelatedResponse422,
)
from ...models.get_v2_editions_edition_id_segments_related_response_500 import (
    GetV2EditionsEditionIdSegmentsRelatedResponse500,
)
from ...models.segment_output import SegmentOutput
from ...types import UNSET, Response


def _get_kwargs(
    edition_id: str,
    *,
    span_start: int,
    span_end: int,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["span_start"] = span_start

    params["span_end"] = span_end

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/editions/{edition_id}/segments/related".format(
            edition_id=quote(str(edition_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetV2EditionsEditionIdSegmentsRelatedResponse400
    | GetV2EditionsEditionIdSegmentsRelatedResponse404
    | GetV2EditionsEditionIdSegmentsRelatedResponse422
    | GetV2EditionsEditionIdSegmentsRelatedResponse500
    | list[SegmentOutput]
    | None
):
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = SegmentOutput.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = GetV2EditionsEditionIdSegmentsRelatedResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = GetV2EditionsEditionIdSegmentsRelatedResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = GetV2EditionsEditionIdSegmentsRelatedResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = GetV2EditionsEditionIdSegmentsRelatedResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2EditionsEditionIdSegmentsRelatedResponse400
    | GetV2EditionsEditionIdSegmentsRelatedResponse404
    | GetV2EditionsEditionIdSegmentsRelatedResponse422
    | GetV2EditionsEditionIdSegmentsRelatedResponse500
    | list[SegmentOutput]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    span_start: int,
    span_end: int,
) -> Response[
    GetV2EditionsEditionIdSegmentsRelatedResponse400
    | GetV2EditionsEditionIdSegmentsRelatedResponse404
    | GetV2EditionsEditionIdSegmentsRelatedResponse422
    | GetV2EditionsEditionIdSegmentsRelatedResponse500
    | list[SegmentOutput]
]:
    """Find related segments by span

     Find segments that overlap with a given character span in the edition, then return all related
    (aligned) segments from other manifestations.

    Args:
        edition_id (str):
        span_start (int):
        span_end (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2EditionsEditionIdSegmentsRelatedResponse400 | GetV2EditionsEditionIdSegmentsRelatedResponse404 | GetV2EditionsEditionIdSegmentsRelatedResponse422 | GetV2EditionsEditionIdSegmentsRelatedResponse500 | list[SegmentOutput]]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
        span_start=span_start,
        span_end=span_end,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    span_start: int,
    span_end: int,
) -> (
    GetV2EditionsEditionIdSegmentsRelatedResponse400
    | GetV2EditionsEditionIdSegmentsRelatedResponse404
    | GetV2EditionsEditionIdSegmentsRelatedResponse422
    | GetV2EditionsEditionIdSegmentsRelatedResponse500
    | list[SegmentOutput]
    | None
):
    """Find related segments by span

     Find segments that overlap with a given character span in the edition, then return all related
    (aligned) segments from other manifestations.

    Args:
        edition_id (str):
        span_start (int):
        span_end (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2EditionsEditionIdSegmentsRelatedResponse400 | GetV2EditionsEditionIdSegmentsRelatedResponse404 | GetV2EditionsEditionIdSegmentsRelatedResponse422 | GetV2EditionsEditionIdSegmentsRelatedResponse500 | list[SegmentOutput]
    """

    return sync_detailed(
        edition_id=edition_id,
        client=client,
        span_start=span_start,
        span_end=span_end,
    ).parsed


async def asyncio_detailed(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    span_start: int,
    span_end: int,
) -> Response[
    GetV2EditionsEditionIdSegmentsRelatedResponse400
    | GetV2EditionsEditionIdSegmentsRelatedResponse404
    | GetV2EditionsEditionIdSegmentsRelatedResponse422
    | GetV2EditionsEditionIdSegmentsRelatedResponse500
    | list[SegmentOutput]
]:
    """Find related segments by span

     Find segments that overlap with a given character span in the edition, then return all related
    (aligned) segments from other manifestations.

    Args:
        edition_id (str):
        span_start (int):
        span_end (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2EditionsEditionIdSegmentsRelatedResponse400 | GetV2EditionsEditionIdSegmentsRelatedResponse404 | GetV2EditionsEditionIdSegmentsRelatedResponse422 | GetV2EditionsEditionIdSegmentsRelatedResponse500 | list[SegmentOutput]]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
        span_start=span_start,
        span_end=span_end,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    span_start: int,
    span_end: int,
) -> (
    GetV2EditionsEditionIdSegmentsRelatedResponse400
    | GetV2EditionsEditionIdSegmentsRelatedResponse404
    | GetV2EditionsEditionIdSegmentsRelatedResponse422
    | GetV2EditionsEditionIdSegmentsRelatedResponse500
    | list[SegmentOutput]
    | None
):
    """Find related segments by span

     Find segments that overlap with a given character span in the edition, then return all related
    (aligned) segments from other manifestations.

    Args:
        edition_id (str):
        span_start (int):
        span_end (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2EditionsEditionIdSegmentsRelatedResponse400 | GetV2EditionsEditionIdSegmentsRelatedResponse404 | GetV2EditionsEditionIdSegmentsRelatedResponse422 | GetV2EditionsEditionIdSegmentsRelatedResponse500 | list[SegmentOutput]
    """

    return (
        await asyncio_detailed(
            edition_id=edition_id,
            client=client,
            span_start=span_start,
            span_end=span_end,
        )
    ).parsed
