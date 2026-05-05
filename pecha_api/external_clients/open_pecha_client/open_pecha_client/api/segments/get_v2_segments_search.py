from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_segments_search_response_200 import GetV2SegmentsSearchResponse200
from ...models.get_v2_segments_search_response_400 import GetV2SegmentsSearchResponse400
from ...models.get_v2_segments_search_response_422 import GetV2SegmentsSearchResponse422
from ...models.get_v2_segments_search_response_500 import GetV2SegmentsSearchResponse500
from ...models.get_v2_segments_search_search_type import GetV2SegmentsSearchSearchType
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    query: str,
    search_type: GetV2SegmentsSearchSearchType | Unset = GetV2SegmentsSearchSearchType.HYBRID,
    limit: int | Unset = 10,
    title: str | Unset = UNSET,
    return_text: bool | Unset = True,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["query"] = query

    json_search_type: str | Unset = UNSET
    if not isinstance(search_type, Unset):
        json_search_type = search_type.value

    params["search_type"] = json_search_type

    params["limit"] = limit

    params["title"] = title

    params["return_text"] = return_text

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/segments/search",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetV2SegmentsSearchResponse200
    | GetV2SegmentsSearchResponse400
    | GetV2SegmentsSearchResponse422
    | GetV2SegmentsSearchResponse500
    | None
):
    if response.status_code == 200:
        response_200 = GetV2SegmentsSearchResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = GetV2SegmentsSearchResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = GetV2SegmentsSearchResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = GetV2SegmentsSearchResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2SegmentsSearchResponse200
    | GetV2SegmentsSearchResponse400
    | GetV2SegmentsSearchResponse422
    | GetV2SegmentsSearchResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    query: str,
    search_type: GetV2SegmentsSearchSearchType | Unset = GetV2SegmentsSearchSearchType.HYBRID,
    limit: int | Unset = 10,
    title: str | Unset = UNSET,
    return_text: bool | Unset = True,
) -> Response[
    GetV2SegmentsSearchResponse200
    | GetV2SegmentsSearchResponse400
    | GetV2SegmentsSearchResponse422
    | GetV2SegmentsSearchResponse500
]:
    """Search segments with segmentation mapping

     Search segments by forwarding request to external search API and enriching results with overlapping
    segmentation annotation segment IDs. For each search result (which contains a search_segmentation
    segment ID), finds overlapping segments from segmentation annotations and adds them as
    segmentation_ids.

    Args:
        query (str):
        search_type (GetV2SegmentsSearchSearchType | Unset):  Default:
            GetV2SegmentsSearchSearchType.HYBRID.
        limit (int | Unset):  Default: 10.
        title (str | Unset):
        return_text (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2SegmentsSearchResponse200 | GetV2SegmentsSearchResponse400 | GetV2SegmentsSearchResponse422 | GetV2SegmentsSearchResponse500]
    """

    kwargs = _get_kwargs(
        query=query,
        search_type=search_type,
        limit=limit,
        title=title,
        return_text=return_text,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    query: str,
    search_type: GetV2SegmentsSearchSearchType | Unset = GetV2SegmentsSearchSearchType.HYBRID,
    limit: int | Unset = 10,
    title: str | Unset = UNSET,
    return_text: bool | Unset = True,
) -> (
    GetV2SegmentsSearchResponse200
    | GetV2SegmentsSearchResponse400
    | GetV2SegmentsSearchResponse422
    | GetV2SegmentsSearchResponse500
    | None
):
    """Search segments with segmentation mapping

     Search segments by forwarding request to external search API and enriching results with overlapping
    segmentation annotation segment IDs. For each search result (which contains a search_segmentation
    segment ID), finds overlapping segments from segmentation annotations and adds them as
    segmentation_ids.

    Args:
        query (str):
        search_type (GetV2SegmentsSearchSearchType | Unset):  Default:
            GetV2SegmentsSearchSearchType.HYBRID.
        limit (int | Unset):  Default: 10.
        title (str | Unset):
        return_text (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2SegmentsSearchResponse200 | GetV2SegmentsSearchResponse400 | GetV2SegmentsSearchResponse422 | GetV2SegmentsSearchResponse500
    """

    return sync_detailed(
        client=client,
        query=query,
        search_type=search_type,
        limit=limit,
        title=title,
        return_text=return_text,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    query: str,
    search_type: GetV2SegmentsSearchSearchType | Unset = GetV2SegmentsSearchSearchType.HYBRID,
    limit: int | Unset = 10,
    title: str | Unset = UNSET,
    return_text: bool | Unset = True,
) -> Response[
    GetV2SegmentsSearchResponse200
    | GetV2SegmentsSearchResponse400
    | GetV2SegmentsSearchResponse422
    | GetV2SegmentsSearchResponse500
]:
    """Search segments with segmentation mapping

     Search segments by forwarding request to external search API and enriching results with overlapping
    segmentation annotation segment IDs. For each search result (which contains a search_segmentation
    segment ID), finds overlapping segments from segmentation annotations and adds them as
    segmentation_ids.

    Args:
        query (str):
        search_type (GetV2SegmentsSearchSearchType | Unset):  Default:
            GetV2SegmentsSearchSearchType.HYBRID.
        limit (int | Unset):  Default: 10.
        title (str | Unset):
        return_text (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2SegmentsSearchResponse200 | GetV2SegmentsSearchResponse400 | GetV2SegmentsSearchResponse422 | GetV2SegmentsSearchResponse500]
    """

    kwargs = _get_kwargs(
        query=query,
        search_type=search_type,
        limit=limit,
        title=title,
        return_text=return_text,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    query: str,
    search_type: GetV2SegmentsSearchSearchType | Unset = GetV2SegmentsSearchSearchType.HYBRID,
    limit: int | Unset = 10,
    title: str | Unset = UNSET,
    return_text: bool | Unset = True,
) -> (
    GetV2SegmentsSearchResponse200
    | GetV2SegmentsSearchResponse400
    | GetV2SegmentsSearchResponse422
    | GetV2SegmentsSearchResponse500
    | None
):
    """Search segments with segmentation mapping

     Search segments by forwarding request to external search API and enriching results with overlapping
    segmentation annotation segment IDs. For each search result (which contains a search_segmentation
    segment ID), finds overlapping segments from segmentation annotations and adds them as
    segmentation_ids.

    Args:
        query (str):
        search_type (GetV2SegmentsSearchSearchType | Unset):  Default:
            GetV2SegmentsSearchSearchType.HYBRID.
        limit (int | Unset):  Default: 10.
        title (str | Unset):
        return_text (bool | Unset):  Default: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2SegmentsSearchResponse200 | GetV2SegmentsSearchResponse400 | GetV2SegmentsSearchResponse422 | GetV2SegmentsSearchResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            query=query,
            search_type=search_type,
            limit=limit,
            title=title,
            return_text=return_text,
        )
    ).parsed
