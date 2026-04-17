from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.category_output import CategoryOutput
from ...models.get_v2_categories_response_400 import GetV2CategoriesResponse400
from ...models.get_v2_categories_response_500 import GetV2CategoriesResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    parent_id: None | str | Unset = UNSET,
    language: str | Unset = "bo",
    x_application: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["X-Application"] = x_application

    params: dict[str, Any] = {}

    json_parent_id: None | str | Unset
    if isinstance(parent_id, Unset):
        json_parent_id = UNSET
    else:
        json_parent_id = parent_id
    params["parent_id"] = json_parent_id

    params["language"] = language

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/categories",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = CategoryOutput.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = GetV2CategoriesResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 500:
        response_500 = GetV2CategoriesResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    parent_id: None | str | Unset = UNSET,
    language: str | Unset = "bo",
    x_application: str,
) -> Response[GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput]]:
    """Retrieve categories

     Get categories filtered by application (via X-Application header) and optional parent

    Args:
        parent_id (None | str | Unset):
        language (str | Unset):  Default: 'bo'.
        x_application (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput]]
    """

    kwargs = _get_kwargs(
        parent_id=parent_id,
        language=language,
        x_application=x_application,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    parent_id: None | str | Unset = UNSET,
    language: str | Unset = "bo",
    x_application: str,
) -> GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput] | None:
    """Retrieve categories

     Get categories filtered by application (via X-Application header) and optional parent

    Args:
        parent_id (None | str | Unset):
        language (str | Unset):  Default: 'bo'.
        x_application (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput]
    """

    return sync_detailed(
        client=client,
        parent_id=parent_id,
        language=language,
        x_application=x_application,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    parent_id: None | str | Unset = UNSET,
    language: str | Unset = "bo",
    x_application: str,
) -> Response[GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput]]:
    """Retrieve categories

     Get categories filtered by application (via X-Application header) and optional parent

    Args:
        parent_id (None | str | Unset):
        language (str | Unset):  Default: 'bo'.
        x_application (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput]]
    """

    kwargs = _get_kwargs(
        parent_id=parent_id,
        language=language,
        x_application=x_application,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    parent_id: None | str | Unset = UNSET,
    language: str | Unset = "bo",
    x_application: str,
) -> GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput] | None:
    """Retrieve categories

     Get categories filtered by application (via X-Application header) and optional parent

    Args:
        parent_id (None | str | Unset):
        language (str | Unset):  Default: 'bo'.
        x_application (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2CategoriesResponse400 | GetV2CategoriesResponse500 | list[CategoryOutput]
    """

    return (
        await asyncio_detailed(
            client=client,
            parent_id=parent_id,
            language=language,
            x_application=x_application,
        )
    ).parsed
