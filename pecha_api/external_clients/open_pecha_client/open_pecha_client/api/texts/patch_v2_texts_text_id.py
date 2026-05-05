from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.expression_output import ExpressionOutput
from ...models.expression_patch import ExpressionPatch
from ...models.patch_v2_texts_text_id_response_400 import PatchV2TextsTextIdResponse400
from ...models.patch_v2_texts_text_id_response_404 import PatchV2TextsTextIdResponse404
from ...models.patch_v2_texts_text_id_response_422 import PatchV2TextsTextIdResponse422
from ...models.patch_v2_texts_text_id_response_500 import PatchV2TextsTextIdResponse500
from ...types import Response


def _get_kwargs(
    text_id: str,
    *,
    body: ExpressionPatch,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v2/texts/{text_id}".format(
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
    ExpressionOutput
    | PatchV2TextsTextIdResponse400
    | PatchV2TextsTextIdResponse404
    | PatchV2TextsTextIdResponse422
    | PatchV2TextsTextIdResponse500
    | None
):
    if response.status_code == 200:
        response_200 = ExpressionOutput.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PatchV2TextsTextIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = PatchV2TextsTextIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = PatchV2TextsTextIdResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PatchV2TextsTextIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    ExpressionOutput
    | PatchV2TextsTextIdResponse400
    | PatchV2TextsTextIdResponse404
    | PatchV2TextsTextIdResponse422
    | PatchV2TextsTextIdResponse500
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
    body: ExpressionPatch,
) -> Response[
    ExpressionOutput
    | PatchV2TextsTextIdResponse400
    | PatchV2TextsTextIdResponse404
    | PatchV2TextsTextIdResponse422
    | PatchV2TextsTextIdResponse500
]:
    """Update a text

     Partially update a text record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        text_id (str):
        body (ExpressionPatch): Partial update for a text. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExpressionOutput | PatchV2TextsTextIdResponse400 | PatchV2TextsTextIdResponse404 | PatchV2TextsTextIdResponse422 | PatchV2TextsTextIdResponse500]
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
    body: ExpressionPatch,
) -> (
    ExpressionOutput
    | PatchV2TextsTextIdResponse400
    | PatchV2TextsTextIdResponse404
    | PatchV2TextsTextIdResponse422
    | PatchV2TextsTextIdResponse500
    | None
):
    """Update a text

     Partially update a text record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        text_id (str):
        body (ExpressionPatch): Partial update for a text. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExpressionOutput | PatchV2TextsTextIdResponse400 | PatchV2TextsTextIdResponse404 | PatchV2TextsTextIdResponse422 | PatchV2TextsTextIdResponse500
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
    body: ExpressionPatch,
) -> Response[
    ExpressionOutput
    | PatchV2TextsTextIdResponse400
    | PatchV2TextsTextIdResponse404
    | PatchV2TextsTextIdResponse422
    | PatchV2TextsTextIdResponse500
]:
    """Update a text

     Partially update a text record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        text_id (str):
        body (ExpressionPatch): Partial update for a text. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ExpressionOutput | PatchV2TextsTextIdResponse400 | PatchV2TextsTextIdResponse404 | PatchV2TextsTextIdResponse422 | PatchV2TextsTextIdResponse500]
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
    body: ExpressionPatch,
) -> (
    ExpressionOutput
    | PatchV2TextsTextIdResponse400
    | PatchV2TextsTextIdResponse404
    | PatchV2TextsTextIdResponse422
    | PatchV2TextsTextIdResponse500
    | None
):
    """Update a text

     Partially update a text record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        text_id (str):
        body (ExpressionPatch): Partial update for a text. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ExpressionOutput | PatchV2TextsTextIdResponse400 | PatchV2TextsTextIdResponse404 | PatchV2TextsTextIdResponse422 | PatchV2TextsTextIdResponse500
    """

    return (
        await asyncio_detailed(
            text_id=text_id,
            client=client,
            body=body,
        )
    ).parsed
