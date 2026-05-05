from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_v2_languages_body import PostV2LanguagesBody
from ...models.post_v2_languages_response_201 import PostV2LanguagesResponse201
from ...models.post_v2_languages_response_400 import PostV2LanguagesResponse400
from ...models.post_v2_languages_response_422 import PostV2LanguagesResponse422
from ...models.post_v2_languages_response_500 import PostV2LanguagesResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PostV2LanguagesBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/languages",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostV2LanguagesResponse201
    | PostV2LanguagesResponse400
    | PostV2LanguagesResponse422
    | PostV2LanguagesResponse500
    | None
):
    if response.status_code == 201:
        response_201 = PostV2LanguagesResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = PostV2LanguagesResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = PostV2LanguagesResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PostV2LanguagesResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostV2LanguagesResponse201 | PostV2LanguagesResponse400 | PostV2LanguagesResponse422 | PostV2LanguagesResponse500
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
    body: PostV2LanguagesBody,
) -> Response[
    PostV2LanguagesResponse201 | PostV2LanguagesResponse400 | PostV2LanguagesResponse422 | PostV2LanguagesResponse500
]:
    """Create a new language

     Create a new language entry in the database

    Args:
        body (PostV2LanguagesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2LanguagesResponse201 | PostV2LanguagesResponse400 | PostV2LanguagesResponse422 | PostV2LanguagesResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: PostV2LanguagesBody,
) -> (
    PostV2LanguagesResponse201
    | PostV2LanguagesResponse400
    | PostV2LanguagesResponse422
    | PostV2LanguagesResponse500
    | None
):
    """Create a new language

     Create a new language entry in the database

    Args:
        body (PostV2LanguagesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2LanguagesResponse201 | PostV2LanguagesResponse400 | PostV2LanguagesResponse422 | PostV2LanguagesResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostV2LanguagesBody,
) -> Response[
    PostV2LanguagesResponse201 | PostV2LanguagesResponse400 | PostV2LanguagesResponse422 | PostV2LanguagesResponse500
]:
    """Create a new language

     Create a new language entry in the database

    Args:
        body (PostV2LanguagesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2LanguagesResponse201 | PostV2LanguagesResponse400 | PostV2LanguagesResponse422 | PostV2LanguagesResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostV2LanguagesBody,
) -> (
    PostV2LanguagesResponse201
    | PostV2LanguagesResponse400
    | PostV2LanguagesResponse422
    | PostV2LanguagesResponse500
    | None
):
    """Create a new language

     Create a new language entry in the database

    Args:
        body (PostV2LanguagesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2LanguagesResponse201 | PostV2LanguagesResponse400 | PostV2LanguagesResponse422 | PostV2LanguagesResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
