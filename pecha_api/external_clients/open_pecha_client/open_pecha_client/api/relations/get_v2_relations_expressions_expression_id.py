from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_relations_expressions_expression_id_response_200 import (
    GetV2RelationsExpressionsExpressionIdResponse200,
)
from ...models.get_v2_relations_expressions_expression_id_response_404 import (
    GetV2RelationsExpressionsExpressionIdResponse404,
)
from ...models.get_v2_relations_expressions_expression_id_response_500 import (
    GetV2RelationsExpressionsExpressionIdResponse500,
)
from ...types import Response


def _get_kwargs(
    expression_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/relations/expressions/{expression_id}".format(
            expression_id=quote(str(expression_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetV2RelationsExpressionsExpressionIdResponse200
    | GetV2RelationsExpressionsExpressionIdResponse404
    | GetV2RelationsExpressionsExpressionIdResponse500
    | None
):
    if response.status_code == 200:
        response_200 = GetV2RelationsExpressionsExpressionIdResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2RelationsExpressionsExpressionIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2RelationsExpressionsExpressionIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2RelationsExpressionsExpressionIdResponse200
    | GetV2RelationsExpressionsExpressionIdResponse404
    | GetV2RelationsExpressionsExpressionIdResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    expression_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetV2RelationsExpressionsExpressionIdResponse200
    | GetV2RelationsExpressionsExpressionIdResponse404
    | GetV2RelationsExpressionsExpressionIdResponse500
]:
    """Get relations for an expression

     Returns all relationships for a given expression, including direction and related expression IDs.

    Args:
        expression_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2RelationsExpressionsExpressionIdResponse200 | GetV2RelationsExpressionsExpressionIdResponse404 | GetV2RelationsExpressionsExpressionIdResponse500]
    """

    kwargs = _get_kwargs(
        expression_id=expression_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    expression_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetV2RelationsExpressionsExpressionIdResponse200
    | GetV2RelationsExpressionsExpressionIdResponse404
    | GetV2RelationsExpressionsExpressionIdResponse500
    | None
):
    """Get relations for an expression

     Returns all relationships for a given expression, including direction and related expression IDs.

    Args:
        expression_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2RelationsExpressionsExpressionIdResponse200 | GetV2RelationsExpressionsExpressionIdResponse404 | GetV2RelationsExpressionsExpressionIdResponse500
    """

    return sync_detailed(
        expression_id=expression_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    expression_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetV2RelationsExpressionsExpressionIdResponse200
    | GetV2RelationsExpressionsExpressionIdResponse404
    | GetV2RelationsExpressionsExpressionIdResponse500
]:
    """Get relations for an expression

     Returns all relationships for a given expression, including direction and related expression IDs.

    Args:
        expression_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2RelationsExpressionsExpressionIdResponse200 | GetV2RelationsExpressionsExpressionIdResponse404 | GetV2RelationsExpressionsExpressionIdResponse500]
    """

    kwargs = _get_kwargs(
        expression_id=expression_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    expression_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetV2RelationsExpressionsExpressionIdResponse200
    | GetV2RelationsExpressionsExpressionIdResponse404
    | GetV2RelationsExpressionsExpressionIdResponse500
    | None
):
    """Get relations for an expression

     Returns all relationships for a given expression, including direction and related expression IDs.

    Args:
        expression_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2RelationsExpressionsExpressionIdResponse200 | GetV2RelationsExpressionsExpressionIdResponse404 | GetV2RelationsExpressionsExpressionIdResponse500
    """

    return (
        await asyncio_detailed(
            expression_id=expression_id,
            client=client,
        )
    ).parsed
