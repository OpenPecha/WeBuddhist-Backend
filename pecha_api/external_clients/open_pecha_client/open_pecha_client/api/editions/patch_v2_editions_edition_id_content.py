from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.patch_v2_editions_edition_id_content_response_200 import PatchV2EditionsEditionIdContentResponse200
from ...models.patch_v2_editions_edition_id_content_response_400 import PatchV2EditionsEditionIdContentResponse400
from ...models.patch_v2_editions_edition_id_content_response_404 import PatchV2EditionsEditionIdContentResponse404
from ...models.patch_v2_editions_edition_id_content_response_422 import PatchV2EditionsEditionIdContentResponse422
from ...models.patch_v2_editions_edition_id_content_response_500 import PatchV2EditionsEditionIdContentResponse500
from ...models.text_operation import TextOperation
from ...types import Response


def _get_kwargs(
    edition_id: str,
    *,
    body: TextOperation,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v2/editions/{edition_id}/content".format(
            edition_id=quote(str(edition_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PatchV2EditionsEditionIdContentResponse200
    | PatchV2EditionsEditionIdContentResponse400
    | PatchV2EditionsEditionIdContentResponse404
    | PatchV2EditionsEditionIdContentResponse422
    | PatchV2EditionsEditionIdContentResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PatchV2EditionsEditionIdContentResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PatchV2EditionsEditionIdContentResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = PatchV2EditionsEditionIdContentResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = PatchV2EditionsEditionIdContentResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PatchV2EditionsEditionIdContentResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PatchV2EditionsEditionIdContentResponse200
    | PatchV2EditionsEditionIdContentResponse400
    | PatchV2EditionsEditionIdContentResponse404
    | PatchV2EditionsEditionIdContentResponse422
    | PatchV2EditionsEditionIdContentResponse500
]:
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
    body: TextOperation,
) -> Response[
    PatchV2EditionsEditionIdContentResponse200
    | PatchV2EditionsEditionIdContentResponse400
    | PatchV2EditionsEditionIdContentResponse404
    | PatchV2EditionsEditionIdContentResponse422
    | PatchV2EditionsEditionIdContentResponse500
]:
    """Modify edition content

     Apply a text operation (INSERT, DELETE, or REPLACE) to the edition's content. This operation updates
    the base text in storage and adjusts all affected spans on the same manifestation. Segmentation
    segments and annotations are adjusted differently based on the operation type and overlap.

    Args:
        edition_id (str):
        body (TextOperation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PatchV2EditionsEditionIdContentResponse200 | PatchV2EditionsEditionIdContentResponse400 | PatchV2EditionsEditionIdContentResponse404 | PatchV2EditionsEditionIdContentResponse422 | PatchV2EditionsEditionIdContentResponse500]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TextOperation,
) -> (
    PatchV2EditionsEditionIdContentResponse200
    | PatchV2EditionsEditionIdContentResponse400
    | PatchV2EditionsEditionIdContentResponse404
    | PatchV2EditionsEditionIdContentResponse422
    | PatchV2EditionsEditionIdContentResponse500
    | None
):
    """Modify edition content

     Apply a text operation (INSERT, DELETE, or REPLACE) to the edition's content. This operation updates
    the base text in storage and adjusts all affected spans on the same manifestation. Segmentation
    segments and annotations are adjusted differently based on the operation type and overlap.

    Args:
        edition_id (str):
        body (TextOperation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PatchV2EditionsEditionIdContentResponse200 | PatchV2EditionsEditionIdContentResponse400 | PatchV2EditionsEditionIdContentResponse404 | PatchV2EditionsEditionIdContentResponse422 | PatchV2EditionsEditionIdContentResponse500
    """

    return sync_detailed(
        edition_id=edition_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TextOperation,
) -> Response[
    PatchV2EditionsEditionIdContentResponse200
    | PatchV2EditionsEditionIdContentResponse400
    | PatchV2EditionsEditionIdContentResponse404
    | PatchV2EditionsEditionIdContentResponse422
    | PatchV2EditionsEditionIdContentResponse500
]:
    """Modify edition content

     Apply a text operation (INSERT, DELETE, or REPLACE) to the edition's content. This operation updates
    the base text in storage and adjusts all affected spans on the same manifestation. Segmentation
    segments and annotations are adjusted differently based on the operation type and overlap.

    Args:
        edition_id (str):
        body (TextOperation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PatchV2EditionsEditionIdContentResponse200 | PatchV2EditionsEditionIdContentResponse400 | PatchV2EditionsEditionIdContentResponse404 | PatchV2EditionsEditionIdContentResponse422 | PatchV2EditionsEditionIdContentResponse500]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TextOperation,
) -> (
    PatchV2EditionsEditionIdContentResponse200
    | PatchV2EditionsEditionIdContentResponse400
    | PatchV2EditionsEditionIdContentResponse404
    | PatchV2EditionsEditionIdContentResponse422
    | PatchV2EditionsEditionIdContentResponse500
    | None
):
    """Modify edition content

     Apply a text operation (INSERT, DELETE, or REPLACE) to the edition's content. This operation updates
    the base text in storage and adjusts all affected spans on the same manifestation. Segmentation
    segments and annotations are adjusted differently based on the operation type and overlap.

    Args:
        edition_id (str):
        body (TextOperation):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PatchV2EditionsEditionIdContentResponse200 | PatchV2EditionsEditionIdContentResponse400 | PatchV2EditionsEditionIdContentResponse404 | PatchV2EditionsEditionIdContentResponse422 | PatchV2EditionsEditionIdContentResponse500
    """

    return (
        await asyncio_detailed(
            edition_id=edition_id,
            client=client,
            body=body,
        )
    ).parsed
