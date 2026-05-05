from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.alignment_output import AlignmentOutput
from ...models.get_v2_annotations_alignment_alignment_id_response_404 import (
    GetV2AnnotationsAlignmentAlignmentIdResponse404,
)
from ...models.get_v2_annotations_alignment_alignment_id_response_500 import (
    GetV2AnnotationsAlignmentAlignmentIdResponse500,
)
from ...types import Response


def _get_kwargs(
    alignment_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/annotations/alignment/{alignment_id}".format(
            alignment_id=quote(str(alignment_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AlignmentOutput
    | GetV2AnnotationsAlignmentAlignmentIdResponse404
    | GetV2AnnotationsAlignmentAlignmentIdResponse500
    | None
):
    if response.status_code == 200:
        response_200 = AlignmentOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2AnnotationsAlignmentAlignmentIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2AnnotationsAlignmentAlignmentIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    AlignmentOutput | GetV2AnnotationsAlignmentAlignmentIdResponse404 | GetV2AnnotationsAlignmentAlignmentIdResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    alignment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    AlignmentOutput | GetV2AnnotationsAlignmentAlignmentIdResponse404 | GetV2AnnotationsAlignmentAlignmentIdResponse500
]:
    """Retrieve alignment annotation by ID

     Fetch a specific alignment annotation with source and target segments

    Args:
        alignment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlignmentOutput | GetV2AnnotationsAlignmentAlignmentIdResponse404 | GetV2AnnotationsAlignmentAlignmentIdResponse500]
    """

    kwargs = _get_kwargs(
        alignment_id=alignment_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    alignment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    AlignmentOutput
    | GetV2AnnotationsAlignmentAlignmentIdResponse404
    | GetV2AnnotationsAlignmentAlignmentIdResponse500
    | None
):
    """Retrieve alignment annotation by ID

     Fetch a specific alignment annotation with source and target segments

    Args:
        alignment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AlignmentOutput | GetV2AnnotationsAlignmentAlignmentIdResponse404 | GetV2AnnotationsAlignmentAlignmentIdResponse500
    """

    return sync_detailed(
        alignment_id=alignment_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    alignment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    AlignmentOutput | GetV2AnnotationsAlignmentAlignmentIdResponse404 | GetV2AnnotationsAlignmentAlignmentIdResponse500
]:
    """Retrieve alignment annotation by ID

     Fetch a specific alignment annotation with source and target segments

    Args:
        alignment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AlignmentOutput | GetV2AnnotationsAlignmentAlignmentIdResponse404 | GetV2AnnotationsAlignmentAlignmentIdResponse500]
    """

    kwargs = _get_kwargs(
        alignment_id=alignment_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    alignment_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    AlignmentOutput
    | GetV2AnnotationsAlignmentAlignmentIdResponse404
    | GetV2AnnotationsAlignmentAlignmentIdResponse500
    | None
):
    """Retrieve alignment annotation by ID

     Fetch a specific alignment annotation with source and target segments

    Args:
        alignment_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AlignmentOutput | GetV2AnnotationsAlignmentAlignmentIdResponse404 | GetV2AnnotationsAlignmentAlignmentIdResponse500
    """

    return (
        await asyncio_detailed(
            alignment_id=alignment_id,
            client=client,
        )
    ).parsed
