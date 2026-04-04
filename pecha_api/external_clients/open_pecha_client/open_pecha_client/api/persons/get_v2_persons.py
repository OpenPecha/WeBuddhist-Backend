from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_persons_response_500 import GetV2PersonsResponse500
from ...models.person_output import PersonOutput
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: int | Unset = 20,
    offset: int | Unset = 0,
    name: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    params["name"] = name

    params["bdrc"] = bdrc

    params["wiki"] = wiki

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/persons",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2PersonsResponse500 | list[PersonOutput] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = PersonOutput.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 500:
        response_500 = GetV2PersonsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetV2PersonsResponse500 | list[PersonOutput]]:
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
    name: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> Response[GetV2PersonsResponse500 | list[PersonOutput]]:
    """Retrieve all persons

     Fetch all persons from the database with optional pagination and filtering

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        name (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2PersonsResponse500 | list[PersonOutput]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        name=name,
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
    name: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> GetV2PersonsResponse500 | list[PersonOutput] | None:
    """Retrieve all persons

     Fetch all persons from the database with optional pagination and filtering

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        name (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2PersonsResponse500 | list[PersonOutput]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        offset=offset,
        name=name,
        bdrc=bdrc,
        wiki=wiki,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 20,
    offset: int | Unset = 0,
    name: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> Response[GetV2PersonsResponse500 | list[PersonOutput]]:
    """Retrieve all persons

     Fetch all persons from the database with optional pagination and filtering

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        name (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2PersonsResponse500 | list[PersonOutput]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        name=name,
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
    name: str | Unset = UNSET,
    bdrc: str | Unset = UNSET,
    wiki: str | Unset = UNSET,
) -> GetV2PersonsResponse500 | list[PersonOutput] | None:
    """Retrieve all persons

     Fetch all persons from the database with optional pagination and filtering

    Args:
        limit (int | Unset):  Default: 20.
        offset (int | Unset):  Default: 0.
        name (str | Unset):
        bdrc (str | Unset):
        wiki (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2PersonsResponse500 | list[PersonOutput]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            offset=offset,
            name=name,
            bdrc=bdrc,
            wiki=wiki,
        )
    ).parsed
