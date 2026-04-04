from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_languages_response_200_item import GetV2LanguagesResponse200Item
from ...models.get_v2_languages_response_500 import GetV2LanguagesResponse500
from ...types import Response


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/languages",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = GetV2LanguagesResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 500:
        response_500 = GetV2LanguagesResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item]]:
    """Retrieve all languages

     Fetch all available language codes from the database

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item] | None:
    """Retrieve all languages

     Fetch all available language codes from the database

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item]]:
    """Retrieve all languages

     Fetch all available language codes from the database

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item] | None:
    """Retrieve all languages

     Fetch all available language codes from the database

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2LanguagesResponse500 | list[GetV2LanguagesResponse200Item]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
