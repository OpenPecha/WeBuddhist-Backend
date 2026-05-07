from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_editions_edition_id_content_response_400 import GetV2EditionsEditionIdContentResponse400
from ...models.get_v2_editions_edition_id_content_response_404 import GetV2EditionsEditionIdContentResponse404
from ...models.get_v2_editions_edition_id_content_response_500 import GetV2EditionsEditionIdContentResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    edition_id: str,
    *,
    span_start: int | Unset = UNSET,
    span_end: int | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["span_start"] = span_start

    params["span_end"] = span_end

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/editions/{edition_id}/content".format(
            edition_id=quote(str(edition_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetV2EditionsEditionIdContentResponse400
    | GetV2EditionsEditionIdContentResponse404
    | GetV2EditionsEditionIdContentResponse500
    | str
    | None
):
    if response.status_code == 200:
        response_200 = cast(str, response.json())
        return response_200

    if response.status_code == 400:
        response_400 = GetV2EditionsEditionIdContentResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = GetV2EditionsEditionIdContentResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2EditionsEditionIdContentResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2EditionsEditionIdContentResponse400
    | GetV2EditionsEditionIdContentResponse404
    | GetV2EditionsEditionIdContentResponse500
    | str
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
    span_start: int | Unset = UNSET,
    span_end: int | Unset = UNSET,
) -> Response[
    GetV2EditionsEditionIdContentResponse400
    | GetV2EditionsEditionIdContentResponse404
    | GetV2EditionsEditionIdContentResponse500
    | str
]:
    """Retrieve edition content

     Fetch base text content for a given edition ID. Optionally specify a span to retrieve a portion of
    the content.

    Args:
        edition_id (str):
        span_start (int | Unset):
        span_end (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2EditionsEditionIdContentResponse400 | GetV2EditionsEditionIdContentResponse404 | GetV2EditionsEditionIdContentResponse500 | str]
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
    span_start: int | Unset = UNSET,
    span_end: int | Unset = UNSET,
) -> (
    GetV2EditionsEditionIdContentResponse400
    | GetV2EditionsEditionIdContentResponse404
    | GetV2EditionsEditionIdContentResponse500
    | str
    | None
):
    """Retrieve edition content

     Fetch base text content for a given edition ID. Optionally specify a span to retrieve a portion of
    the content.

    Args:
        edition_id (str):
        span_start (int | Unset):
        span_end (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2EditionsEditionIdContentResponse400 | GetV2EditionsEditionIdContentResponse404 | GetV2EditionsEditionIdContentResponse500 | str
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
    span_start: int | Unset = UNSET,
    span_end: int | Unset = UNSET,
) -> Response[
    GetV2EditionsEditionIdContentResponse400
    | GetV2EditionsEditionIdContentResponse404
    | GetV2EditionsEditionIdContentResponse500
    | str
]:
    """Retrieve edition content

     Fetch base text content for a given edition ID. Optionally specify a span to retrieve a portion of
    the content.

    Args:
        edition_id (str):
        span_start (int | Unset):
        span_end (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2EditionsEditionIdContentResponse400 | GetV2EditionsEditionIdContentResponse404 | GetV2EditionsEditionIdContentResponse500 | str]
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
    span_start: int | Unset = UNSET,
    span_end: int | Unset = UNSET,
) -> (
    GetV2EditionsEditionIdContentResponse400
    | GetV2EditionsEditionIdContentResponse404
    | GetV2EditionsEditionIdContentResponse500
    | str
    | None
):
    """Retrieve edition content

     Fetch base text content for a given edition ID. Optionally specify a span to retrieve a portion of
    the content.

    Args:
        edition_id (str):
        span_start (int | Unset):
        span_end (int | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2EditionsEditionIdContentResponse400 | GetV2EditionsEditionIdContentResponse404 | GetV2EditionsEditionIdContentResponse500 | str
    """

    return (
        await asyncio_detailed(
            edition_id=edition_id,
            client=client,
            span_start=span_start,
            span_end=span_end,
        )
    ).parsed
