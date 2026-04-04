from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.expression_output import ExpressionOutput
from ...models.get_v2_texts_response_400 import GetV2TextsResponse400
from ...models.get_v2_texts_response_500 import GetV2TextsResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 20,
    offset: int | Unset = 0,
    language: str | Unset = UNSET,
    title: str | Unset = UNSET,
    category_id: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    params["language"] = language

    params["title"] = title

    params["category_id"] = category_id

    params["bdrc"] = bdrc

    params["wiki"] = wiki

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/texts",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ExpressionOutput.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = GetV2TextsResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = GetV2TextsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    offset: int | Unset = 0,
    language: str | Unset = UNSET,
    title: str | Unset = UNSET,
    category_id: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> Response[GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput]]:
    """Retrieve all texts

     Fetch all texts with optional filtering and pagination

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        language (str | Unset):
        title (str | Unset):
        category_id (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        language=language,
        title=title,
        category_id=category_id,
        bdrc=bdrc,
        wiki=wiki,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    offset: int | Unset = 0,
    language: str | Unset = UNSET,
    title: str | Unset = UNSET,
    category_id: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput] | None:
    """Retrieve all texts

     Fetch all texts with optional filtering and pagination

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        language (str | Unset):
        title (str | Unset):
        category_id (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        offset=offset,
        language=language,
        title=title,
        category_id=category_id,
        bdrc=bdrc,
        wiki=wiki,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    offset: int | Unset = 0,
    language: str | Unset = UNSET,
    title: str | Unset = UNSET,
    category_id: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> Response[GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput]]:
    """Retrieve all texts

     Fetch all texts with optional filtering and pagination

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        language (str | Unset):
        title (str | Unset):
        category_id (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        language=language,
        title=title,
        category_id=category_id,
        bdrc=bdrc,
        wiki=wiki,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    offset: int | Unset = 0,
    language: str | Unset = UNSET,
    title: str | Unset = UNSET,
    category_id: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput] | None:
    """Retrieve all texts

     Fetch all texts with optional filtering and pagination

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        language (str | Unset):
        title (str | Unset):
        category_id (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2TextsResponse400 | GetV2TextsResponse500 | list[ExpressionOutput]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            offset=offset,
            language=language,
            title=title,
            category_id=category_id,
            bdrc=bdrc,
            wiki=wiki,
        )
    ).parsed
