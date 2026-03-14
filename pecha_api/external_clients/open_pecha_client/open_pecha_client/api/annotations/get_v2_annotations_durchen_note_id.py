from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_annotations_durchen_note_id_response_404 import GetV2AnnotationsDurchenNoteIdResponse404
from ...models.get_v2_annotations_durchen_note_id_response_500 import GetV2AnnotationsDurchenNoteIdResponse500
from ...models.note_output import NoteOutput
from ...types import Response


def _get_kwargs(
    note_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/annotations/durchen/{note_id}".format(
            note_id=quote(str(note_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput | None:
    if response.status_code == 200:
        response_200 = NoteOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2AnnotationsDurchenNoteIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2AnnotationsDurchenNoteIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput]:
    """Retrieve durchen note by ID

     Fetch a specific durchen (critical apparatus) note

    Args:
        note_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput]
    """

    kwargs = _get_kwargs(
        note_id=note_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput | None:
    """Retrieve durchen note by ID

     Fetch a specific durchen (critical apparatus) note

    Args:
        note_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput
    """

    return sync_detailed(
        note_id=note_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput]:
    """Retrieve durchen note by ID

     Fetch a specific durchen (critical apparatus) note

    Args:
        note_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput]
    """

    kwargs = _get_kwargs(
        note_id=note_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput | None:
    """Retrieve durchen note by ID

     Fetch a specific durchen (critical apparatus) note

    Args:
        note_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2AnnotationsDurchenNoteIdResponse404 | GetV2AnnotationsDurchenNoteIdResponse500 | NoteOutput
    """

    return (
        await asyncio_detailed(
            note_id=note_id,
            client=client,
        )
    ).parsed
