from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.expression_output import ExpressionOutput
from ...models.get_v2_texts_text_id_response_404 import GetV2TextsTextIdResponse404
from ...models.get_v2_texts_text_id_response_500 import GetV2TextsTextIdResponse500
from ...types import Response


def _get_kwargs(
    text_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/texts/{text_id}".format(
            text_id=quote(str(text_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500 | None:
    if response.status_code == 200:
        response_200 = ExpressionOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2TextsTextIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2TextsTextIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500]:
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
) -> Response[ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500]:
    """Retrieve text by ID

     Fetch a specific text by its text ID.

    Args:
        text_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500]
    """

    kwargs = _get_kwargs(
        text_id=text_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500 | None:
    """Retrieve text by ID

     Fetch a specific text by its text ID.

    Args:
        text_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500
    """

    return sync_detailed(
        text_id=text_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500]:
    """Retrieve text by ID

     Fetch a specific text by its text ID.

    Args:
        text_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500]
    """

    kwargs = _get_kwargs(
        text_id=text_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500 | None:
    """Retrieve text by ID

     Fetch a specific text by its text ID.

    Args:
        text_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExpressionOutput | GetV2TextsTextIdResponse404 | GetV2TextsTextIdResponse500
    """

    return (
        await asyncio_detailed(
            text_id=text_id,
            client=client,
        )
    ).parsed
