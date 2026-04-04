from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_v2_annotations_bibliographic_bibliographic_id_response_404 import (
    DeleteV2AnnotationsBibliographicBibliographicIdResponse404,
)
from ...models.delete_v2_annotations_bibliographic_bibliographic_id_response_500 import (
    DeleteV2AnnotationsBibliographicBibliographicIdResponse500,
)
from ...types import Response


def _get_kwargs(
    bibliographic_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/v2/annotations/bibliographic/{bibliographic_id}".format(
            bibliographic_id=quote(str(bibliographic_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse404
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 404:
        response_404 = DeleteV2AnnotationsBibliographicBibliographicIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = DeleteV2AnnotationsBibliographicBibliographicIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse404
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    bibliographic_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse404
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
]:
    """Delete bibliographic metadata

     Permanently delete a bibliographic metadata annotation

    Args:
        bibliographic_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteV2AnnotationsBibliographicBibliographicIdResponse404 | DeleteV2AnnotationsBibliographicBibliographicIdResponse500]
    """

    kwargs = _get_kwargs(
        bibliographic_id=bibliographic_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    bibliographic_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse404
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
    | None
):
    """Delete bibliographic metadata

     Permanently delete a bibliographic metadata annotation

    Args:
        bibliographic_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteV2AnnotationsBibliographicBibliographicIdResponse404 | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
    """

    return sync_detailed(
        bibliographic_id=bibliographic_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    bibliographic_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse404
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
]:
    """Delete bibliographic metadata

     Permanently delete a bibliographic metadata annotation

    Args:
        bibliographic_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteV2AnnotationsBibliographicBibliographicIdResponse404 | DeleteV2AnnotationsBibliographicBibliographicIdResponse500]
    """

    kwargs = _get_kwargs(
        bibliographic_id=bibliographic_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    bibliographic_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse404
    | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
    | None
):
    """Delete bibliographic metadata

     Permanently delete a bibliographic metadata annotation

    Args:
        bibliographic_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteV2AnnotationsBibliographicBibliographicIdResponse404 | DeleteV2AnnotationsBibliographicBibliographicIdResponse500
    """

    return (
        await asyncio_detailed(
            bibliographic_id=bibliographic_id,
            client=client,
        )
    ).parsed
