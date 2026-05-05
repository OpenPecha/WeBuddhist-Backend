from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_v2_applications_body import PostV2ApplicationsBody
from ...models.post_v2_applications_response_201 import PostV2ApplicationsResponse201
from ...models.post_v2_applications_response_400 import PostV2ApplicationsResponse400
from ...models.post_v2_applications_response_422 import PostV2ApplicationsResponse422
from ...models.post_v2_applications_response_500 import PostV2ApplicationsResponse500
from ...types import Response


def _get_kwargs(
    *,
    body: PostV2ApplicationsBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/applications",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PostV2ApplicationsResponse201
    | PostV2ApplicationsResponse400
    | PostV2ApplicationsResponse422
    | PostV2ApplicationsResponse500
    | None
):
    if response.status_code == 201:
        response_201 = PostV2ApplicationsResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = PostV2ApplicationsResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 422:
        response_422 = PostV2ApplicationsResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PostV2ApplicationsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostV2ApplicationsResponse201
    | PostV2ApplicationsResponse400
    | PostV2ApplicationsResponse422
    | PostV2ApplicationsResponse500
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
    body: PostV2ApplicationsBody,
) -> Response[
    PostV2ApplicationsResponse201
    | PostV2ApplicationsResponse400
    | PostV2ApplicationsResponse422
    | PostV2ApplicationsResponse500
]:
    """Create a new application

     Create a new application entry in the database. Input is normalized to lowercase for both id and
    name.

    Args:
        body (PostV2ApplicationsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2ApplicationsResponse201 | PostV2ApplicationsResponse400 | PostV2ApplicationsResponse422 | PostV2ApplicationsResponse500]
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
    body: PostV2ApplicationsBody,
) -> (
    PostV2ApplicationsResponse201
    | PostV2ApplicationsResponse400
    | PostV2ApplicationsResponse422
    | PostV2ApplicationsResponse500
    | None
):
    """Create a new application

     Create a new application entry in the database. Input is normalized to lowercase for both id and
    name.

    Args:
        body (PostV2ApplicationsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2ApplicationsResponse201 | PostV2ApplicationsResponse400 | PostV2ApplicationsResponse422 | PostV2ApplicationsResponse500
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PostV2ApplicationsBody,
) -> Response[
    PostV2ApplicationsResponse201
    | PostV2ApplicationsResponse400
    | PostV2ApplicationsResponse422
    | PostV2ApplicationsResponse500
]:
    """Create a new application

     Create a new application entry in the database. Input is normalized to lowercase for both id and
    name.

    Args:
        body (PostV2ApplicationsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2ApplicationsResponse201 | PostV2ApplicationsResponse400 | PostV2ApplicationsResponse422 | PostV2ApplicationsResponse500]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PostV2ApplicationsBody,
) -> (
    PostV2ApplicationsResponse201
    | PostV2ApplicationsResponse400
    | PostV2ApplicationsResponse422
    | PostV2ApplicationsResponse500
    | None
):
    """Create a new application

     Create a new application entry in the database. Input is normalized to lowercase for both id and
    name.

    Args:
        body (PostV2ApplicationsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2ApplicationsResponse201 | PostV2ApplicationsResponse400 | PostV2ApplicationsResponse422 | PostV2ApplicationsResponse500
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
