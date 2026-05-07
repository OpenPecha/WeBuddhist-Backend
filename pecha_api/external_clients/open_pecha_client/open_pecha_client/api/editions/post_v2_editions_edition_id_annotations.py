from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.annotation_request_input import AnnotationRequestInput
from ...models.post_v2_editions_edition_id_annotations_response_201 import PostV2EditionsEditionIdAnnotationsResponse201
from ...models.post_v2_editions_edition_id_annotations_response_400 import PostV2EditionsEditionIdAnnotationsResponse400
from ...models.post_v2_editions_edition_id_annotations_response_404 import PostV2EditionsEditionIdAnnotationsResponse404
from ...models.post_v2_editions_edition_id_annotations_response_422 import PostV2EditionsEditionIdAnnotationsResponse422
from ...models.post_v2_editions_edition_id_annotations_response_500 import PostV2EditionsEditionIdAnnotationsResponse500
from ...types import Response


def _get_kwargs(
    edition_id: str,
    *,
    body: AnnotationRequestInput,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v2/editions/{edition_id}/annotations".format(
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
    PostV2EditionsEditionIdAnnotationsResponse201
    | PostV2EditionsEditionIdAnnotationsResponse400
    | PostV2EditionsEditionIdAnnotationsResponse404
    | PostV2EditionsEditionIdAnnotationsResponse422
    | PostV2EditionsEditionIdAnnotationsResponse500
    | None
):
    if response.status_code == 201:
        response_201 = PostV2EditionsEditionIdAnnotationsResponse201.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = PostV2EditionsEditionIdAnnotationsResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = PostV2EditionsEditionIdAnnotationsResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = PostV2EditionsEditionIdAnnotationsResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PostV2EditionsEditionIdAnnotationsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PostV2EditionsEditionIdAnnotationsResponse201
    | PostV2EditionsEditionIdAnnotationsResponse400
    | PostV2EditionsEditionIdAnnotationsResponse404
    | PostV2EditionsEditionIdAnnotationsResponse422
    | PostV2EditionsEditionIdAnnotationsResponse500
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
    body: AnnotationRequestInput,
) -> Response[
    PostV2EditionsEditionIdAnnotationsResponse201
    | PostV2EditionsEditionIdAnnotationsResponse400
    | PostV2EditionsEditionIdAnnotationsResponse404
    | PostV2EditionsEditionIdAnnotationsResponse422
    | PostV2EditionsEditionIdAnnotationsResponse500
]:
    """Add annotation to an edition

     Adds an annotation to the specified edition (manifestation). Exactly one annotation type must be
    provided per request.
    Supported annotation types: - **segmentation**: Text segmentation with segments containing lines
    (spans) - **alignment**: Alignment between this edition and a target edition - **pagination**:
    Page/folio references for diplomatic editions - **bibliographic_metadata**: Colophon, title, author
    spans - **durchen_notes**: Critical apparatus notes

    Args:
        edition_id (str):
        body (AnnotationRequestInput): Request body for adding annotations. Exactly one annotation
            type must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2EditionsEditionIdAnnotationsResponse201 | PostV2EditionsEditionIdAnnotationsResponse400 | PostV2EditionsEditionIdAnnotationsResponse404 | PostV2EditionsEditionIdAnnotationsResponse422 | PostV2EditionsEditionIdAnnotationsResponse500]
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
    body: AnnotationRequestInput,
) -> (
    PostV2EditionsEditionIdAnnotationsResponse201
    | PostV2EditionsEditionIdAnnotationsResponse400
    | PostV2EditionsEditionIdAnnotationsResponse404
    | PostV2EditionsEditionIdAnnotationsResponse422
    | PostV2EditionsEditionIdAnnotationsResponse500
    | None
):
    """Add annotation to an edition

     Adds an annotation to the specified edition (manifestation). Exactly one annotation type must be
    provided per request.
    Supported annotation types: - **segmentation**: Text segmentation with segments containing lines
    (spans) - **alignment**: Alignment between this edition and a target edition - **pagination**:
    Page/folio references for diplomatic editions - **bibliographic_metadata**: Colophon, title, author
    spans - **durchen_notes**: Critical apparatus notes

    Args:
        edition_id (str):
        body (AnnotationRequestInput): Request body for adding annotations. Exactly one annotation
            type must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2EditionsEditionIdAnnotationsResponse201 | PostV2EditionsEditionIdAnnotationsResponse400 | PostV2EditionsEditionIdAnnotationsResponse404 | PostV2EditionsEditionIdAnnotationsResponse422 | PostV2EditionsEditionIdAnnotationsResponse500
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
    body: AnnotationRequestInput,
) -> Response[
    PostV2EditionsEditionIdAnnotationsResponse201
    | PostV2EditionsEditionIdAnnotationsResponse400
    | PostV2EditionsEditionIdAnnotationsResponse404
    | PostV2EditionsEditionIdAnnotationsResponse422
    | PostV2EditionsEditionIdAnnotationsResponse500
]:
    """Add annotation to an edition

     Adds an annotation to the specified edition (manifestation). Exactly one annotation type must be
    provided per request.
    Supported annotation types: - **segmentation**: Text segmentation with segments containing lines
    (spans) - **alignment**: Alignment between this edition and a target edition - **pagination**:
    Page/folio references for diplomatic editions - **bibliographic_metadata**: Colophon, title, author
    spans - **durchen_notes**: Critical apparatus notes

    Args:
        edition_id (str):
        body (AnnotationRequestInput): Request body for adding annotations. Exactly one annotation
            type must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostV2EditionsEditionIdAnnotationsResponse201 | PostV2EditionsEditionIdAnnotationsResponse400 | PostV2EditionsEditionIdAnnotationsResponse404 | PostV2EditionsEditionIdAnnotationsResponse422 | PostV2EditionsEditionIdAnnotationsResponse500]
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
    body: AnnotationRequestInput,
) -> (
    PostV2EditionsEditionIdAnnotationsResponse201
    | PostV2EditionsEditionIdAnnotationsResponse400
    | PostV2EditionsEditionIdAnnotationsResponse404
    | PostV2EditionsEditionIdAnnotationsResponse422
    | PostV2EditionsEditionIdAnnotationsResponse500
    | None
):
    """Add annotation to an edition

     Adds an annotation to the specified edition (manifestation). Exactly one annotation type must be
    provided per request.
    Supported annotation types: - **segmentation**: Text segmentation with segments containing lines
    (spans) - **alignment**: Alignment between this edition and a target edition - **pagination**:
    Page/folio references for diplomatic editions - **bibliographic_metadata**: Colophon, title, author
    spans - **durchen_notes**: Critical apparatus notes

    Args:
        edition_id (str):
        body (AnnotationRequestInput): Request body for adding annotations. Exactly one annotation
            type must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostV2EditionsEditionIdAnnotationsResponse201 | PostV2EditionsEditionIdAnnotationsResponse400 | PostV2EditionsEditionIdAnnotationsResponse404 | PostV2EditionsEditionIdAnnotationsResponse422 | PostV2EditionsEditionIdAnnotationsResponse500
    """

    return (
        await asyncio_detailed(
            edition_id=edition_id,
            client=client,
            body=body,
        )
    ).parsed
