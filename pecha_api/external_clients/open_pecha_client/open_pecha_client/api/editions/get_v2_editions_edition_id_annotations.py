from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.annotation_request_output import AnnotationRequestOutput
from ...models.get_v2_editions_edition_id_annotations_response_404 import GetV2EditionsEditionIdAnnotationsResponse404
from ...models.get_v2_editions_edition_id_annotations_response_500 import GetV2EditionsEditionIdAnnotationsResponse500
from ...models.get_v2_editions_edition_id_annotations_type_item import GetV2EditionsEditionIdAnnotationsTypeItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    edition_id: str,
    *,
    type_: list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_type_: list[str] | Unset = UNSET
    if not isinstance(type_, Unset):
        json_type_ = []
        for type_item_data in type_:
            type_item = type_item_data.value
            json_type_.append(type_item)

    params["type"] = json_type_

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/editions/{edition_id}/annotations".format(
            edition_id=quote(str(edition_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AnnotationRequestOutput
    | GetV2EditionsEditionIdAnnotationsResponse404
    | GetV2EditionsEditionIdAnnotationsResponse500
    | None
):
    if response.status_code == 200:
        response_200 = AnnotationRequestOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2EditionsEditionIdAnnotationsResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2EditionsEditionIdAnnotationsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    AnnotationRequestOutput
    | GetV2EditionsEditionIdAnnotationsResponse404
    | GetV2EditionsEditionIdAnnotationsResponse500
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
    type_: list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset = UNSET,
) -> Response[
    AnnotationRequestOutput
    | GetV2EditionsEditionIdAnnotationsResponse404
    | GetV2EditionsEditionIdAnnotationsResponse500
]:
    """Get all annotations for an edition

     Retrieves all annotations for the specified edition (manifestation). Use the `type` query parameter
    to filter by annotation type(s). Multiple types can be specified by repeating the parameter.

    Args:
        edition_id (str):
        type_ (list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AnnotationRequestOutput | GetV2EditionsEditionIdAnnotationsResponse404 | GetV2EditionsEditionIdAnnotationsResponse500]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
        type_=type_,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    type_: list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset = UNSET,
) -> (
    AnnotationRequestOutput
    | GetV2EditionsEditionIdAnnotationsResponse404
    | GetV2EditionsEditionIdAnnotationsResponse500
    | None
):
    """Get all annotations for an edition

     Retrieves all annotations for the specified edition (manifestation). Use the `type` query parameter
    to filter by annotation type(s). Multiple types can be specified by repeating the parameter.

    Args:
        edition_id (str):
        type_ (list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AnnotationRequestOutput | GetV2EditionsEditionIdAnnotationsResponse404 | GetV2EditionsEditionIdAnnotationsResponse500
    """

    return sync_detailed(
        edition_id=edition_id,
        client=client,
        type_=type_,
    ).parsed


async def asyncio_detailed(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    type_: list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset = UNSET,
) -> Response[
    AnnotationRequestOutput
    | GetV2EditionsEditionIdAnnotationsResponse404
    | GetV2EditionsEditionIdAnnotationsResponse500
]:
    """Get all annotations for an edition

     Retrieves all annotations for the specified edition (manifestation). Use the `type` query parameter
    to filter by annotation type(s). Multiple types can be specified by repeating the parameter.

    Args:
        edition_id (str):
        type_ (list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AnnotationRequestOutput | GetV2EditionsEditionIdAnnotationsResponse404 | GetV2EditionsEditionIdAnnotationsResponse500]
    """

    kwargs = _get_kwargs(
        edition_id=edition_id,
        type_=type_,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
    type_: list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset = UNSET,
) -> (
    AnnotationRequestOutput
    | GetV2EditionsEditionIdAnnotationsResponse404
    | GetV2EditionsEditionIdAnnotationsResponse500
    | None
):
    """Get all annotations for an edition

     Retrieves all annotations for the specified edition (manifestation). Use the `type` query parameter
    to filter by annotation type(s). Multiple types can be specified by repeating the parameter.

    Args:
        edition_id (str):
        type_ (list[GetV2EditionsEditionIdAnnotationsTypeItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AnnotationRequestOutput | GetV2EditionsEditionIdAnnotationsResponse404 | GetV2EditionsEditionIdAnnotationsResponse500
    """

    return (
        await asyncio_detailed(
            edition_id=edition_id,
            client=client,
            type_=type_,
        )
    ).parsed
