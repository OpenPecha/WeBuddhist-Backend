from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_v2_editions_edition_id_response_404 import DeleteV2EditionsEditionIdResponse404
from ...models.delete_v2_editions_edition_id_response_500 import DeleteV2EditionsEditionIdResponse500
from ...types import Response


def _get_kwargs(
    edition_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v2/editions/{edition_id}".format(
            edition_id=quote(str(edition_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500 | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 404:
        response_404 = DeleteV2EditionsEditionIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = DeleteV2EditionsEditionIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500]:
    """Delete an edition

     Delete an edition (manifestation) and all its associated data including annotations (segmentation,
    pagination, bibliography, durchen notes, alignments) and stored content.

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500 | None:
    """Delete an edition

     Delete an edition (manifestation) and all its associated data including annotations (segmentation,
    pagination, bibliography, durchen notes, alignments) and stored content.

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500
    """

    return sync_detailed(
        edition_id=edition_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500]:
    """Delete an edition

     Delete an edition (manifestation) and all its associated data including annotations (segmentation,
    pagination, bibliography, durchen notes, alignments) and stored content.

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500 | None:
    """Delete an edition

     Delete an edition (manifestation) and all its associated data including annotations (segmentation,
    pagination, bibliography, durchen notes, alignments) and stored content.

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteV2EditionsEditionIdResponse404 | DeleteV2EditionsEditionIdResponse500
    """

    return (
        await asyncio_detailed(
            edition_id=edition_id,
            client=client,
        )
    ).parsed
