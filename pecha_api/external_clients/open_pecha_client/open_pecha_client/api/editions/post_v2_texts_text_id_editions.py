from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_v2_texts_text_id_editions_body import PostV2TextsTextIdEditionsBody
from ...models.post_v2_texts_text_id_editions_response_201 import PostV2TextsTextIdEditionsResponse201
from ...models.post_v2_texts_text_id_editions_response_400 import PostV2TextsTextIdEditionsResponse400
from ...models.post_v2_texts_text_id_editions_response_422 import PostV2TextsTextIdEditionsResponse422
from ...models.post_v2_texts_text_id_editions_response_500 import PostV2TextsTextIdEditionsResponse500
from ...types import Response


def _get_kwargs(
    text_id: str,
    *,
    body: PostV2TextsTextIdEditionsBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/texts/{text_id}/editions".format(
            text_id=quote(str(text_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostV2TextsTextIdEditionsResponse201
    | PostV2TextsTextIdEditionsResponse400
    | PostV2TextsTextIdEditionsResponse422
    | PostV2TextsTextIdEditionsResponse500
    | None
):
    if response.status_code == 201:
        response_201 = PostV2TextsTextIdEditionsResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = PostV2TextsTextIdEditionsResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = PostV2TextsTextIdEditionsResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PostV2TextsTextIdEditionsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostV2TextsTextIdEditionsResponse201
    | PostV2TextsTextIdEditionsResponse400
    | PostV2TextsTextIdEditionsResponse422
    | PostV2TextsTextIdEditionsResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostV2TextsTextIdEditionsBody,
) -> Response[
    PostV2TextsTextIdEditionsResponse201
    | PostV2TextsTextIdEditionsResponse400
    | PostV2TextsTextIdEditionsResponse422
    | PostV2TextsTextIdEditionsResponse500
]:
    """Create a new edition

     Create a new edition with metadata for a specific text

    Args:
        text_id (str):
        body (PostV2TextsTextIdEditionsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2TextsTextIdEditionsResponse201 | PostV2TextsTextIdEditionsResponse400 | PostV2TextsTextIdEditionsResponse422 | PostV2TextsTextIdEditionsResponse500]
    """

    kwargs = _get_kwargs(
        text_id=text_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostV2TextsTextIdEditionsBody,
) -> (
    PostV2TextsTextIdEditionsResponse201
    | PostV2TextsTextIdEditionsResponse400
    | PostV2TextsTextIdEditionsResponse422
    | PostV2TextsTextIdEditionsResponse500
    | None
):
    """Create a new edition

     Create a new edition with metadata for a specific text

    Args:
        text_id (str):
        body (PostV2TextsTextIdEditionsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2TextsTextIdEditionsResponse201 | PostV2TextsTextIdEditionsResponse400 | PostV2TextsTextIdEditionsResponse422 | PostV2TextsTextIdEditionsResponse500
    """

    return sync_detailed(
        text_id=text_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostV2TextsTextIdEditionsBody,
) -> Response[
    PostV2TextsTextIdEditionsResponse201
    | PostV2TextsTextIdEditionsResponse400
    | PostV2TextsTextIdEditionsResponse422
    | PostV2TextsTextIdEditionsResponse500
]:
    """Create a new edition

     Create a new edition with metadata for a specific text

    Args:
        text_id (str):
        body (PostV2TextsTextIdEditionsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2TextsTextIdEditionsResponse201 | PostV2TextsTextIdEditionsResponse400 | PostV2TextsTextIdEditionsResponse422 | PostV2TextsTextIdEditionsResponse500]
    """

    kwargs = _get_kwargs(
        text_id=text_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PostV2TextsTextIdEditionsBody,
) -> (
    PostV2TextsTextIdEditionsResponse201
    | PostV2TextsTextIdEditionsResponse400
    | PostV2TextsTextIdEditionsResponse422
    | PostV2TextsTextIdEditionsResponse500
    | None
):
    """Create a new edition

     Create a new edition with metadata for a specific text

    Args:
        text_id (str):
        body (PostV2TextsTextIdEditionsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2TextsTextIdEditionsResponse201 | PostV2TextsTextIdEditionsResponse400 | PostV2TextsTextIdEditionsResponse422 | PostV2TextsTextIdEditionsResponse500
    """

    return (
        await asyncio_detailed(
            text_id=text_id,
            client=client,
            body=body,
        )
    ).parsed
