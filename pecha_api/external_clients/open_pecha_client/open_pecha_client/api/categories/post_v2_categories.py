from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.category_input import CategoryInput
from ...models.post_v2_categories_response_201 import PostV2CategoriesResponse201
from ...models.post_v2_categories_response_400 import PostV2CategoriesResponse400
from ...models.post_v2_categories_response_422 import PostV2CategoriesResponse422
from ...models.post_v2_categories_response_500 import PostV2CategoriesResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: CategoryInput,
    x_application: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["X-Application"] = x_application

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/categories",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostV2CategoriesResponse201
    | PostV2CategoriesResponse400
    | PostV2CategoriesResponse422
    | PostV2CategoriesResponse500
    | None
):
    if response.status_code == 201:
        response_201 = PostV2CategoriesResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = PostV2CategoriesResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = PostV2CategoriesResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PostV2CategoriesResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostV2CategoriesResponse201
    | PostV2CategoriesResponse400
    | PostV2CategoriesResponse422
    | PostV2CategoriesResponse500
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
    body: CategoryInput,
    x_application: str,
) -> Response[
    PostV2CategoriesResponse201
    | PostV2CategoriesResponse400
    | PostV2CategoriesResponse422
    | PostV2CategoriesResponse500
]:
    """Create a new category

     Create a category with localized title and optional parent relationship. Application context is
    provided via X-Application header.

    Args:
        x_application (str):
        body (CategoryInput):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2CategoriesResponse201 | PostV2CategoriesResponse400 | PostV2CategoriesResponse422 | PostV2CategoriesResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
        x_application=x_application,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CategoryInput,
    x_application: str,
) -> (
    PostV2CategoriesResponse201
    | PostV2CategoriesResponse400
    | PostV2CategoriesResponse422
    | PostV2CategoriesResponse500
    | None
):
    """Create a new category

     Create a category with localized title and optional parent relationship. Application context is
    provided via X-Application header.

    Args:
        x_application (str):
        body (CategoryInput):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2CategoriesResponse201 | PostV2CategoriesResponse400 | PostV2CategoriesResponse422 | PostV2CategoriesResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
        x_application=x_application,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CategoryInput,
    x_application: str,
) -> Response[
    PostV2CategoriesResponse201
    | PostV2CategoriesResponse400
    | PostV2CategoriesResponse422
    | PostV2CategoriesResponse500
]:
    """Create a new category

     Create a category with localized title and optional parent relationship. Application context is
    provided via X-Application header.

    Args:
        x_application (str):
        body (CategoryInput):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2CategoriesResponse201 | PostV2CategoriesResponse400 | PostV2CategoriesResponse422 | PostV2CategoriesResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
        x_application=x_application,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CategoryInput,
    x_application: str,
) -> (
    PostV2CategoriesResponse201
    | PostV2CategoriesResponse400
    | PostV2CategoriesResponse422
    | PostV2CategoriesResponse500
    | None
):
    """Create a new category

     Create a category with localized title and optional parent relationship. Application context is
    provided via X-Application header.

    Args:
        x_application (str):
        body (CategoryInput):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2CategoriesResponse201 | PostV2CategoriesResponse400 | PostV2CategoriesResponse422 | PostV2CategoriesResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_application=x_application,
        )
    ).parsed
