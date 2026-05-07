from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_texts_text_id_editions_edition_type import GetV2TextsTextIdEditionsEditionType
from ...models.get_v2_texts_text_id_editions_response_400 import GetV2TextsTextIdEditionsResponse400
from ...models.get_v2_texts_text_id_editions_response_404 import GetV2TextsTextIdEditionsResponse404
from ...models.get_v2_texts_text_id_editions_response_500 import GetV2TextsTextIdEditionsResponse500
from ...models.manifestation_output import ManifestationOutput
from ...types import UNSET, Response, Unset


def _get_kwargs(
    text_id: str,
    *,
    edition_type: GetV2TextsTextIdEditionsEditionType | Unset = GetV2TextsTextIdEditionsEditionType.ALL,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_edition_type: str | Unset = UNSET
    if not isinstance(edition_type, Unset):
        json_edition_type = edition_type.value

    params["edition_type"] = json_edition_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/texts/{text_id}/editions".format(
            text_id=quote(str(text_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetV2TextsTextIdEditionsResponse400
    | GetV2TextsTextIdEditionsResponse404
    | GetV2TextsTextIdEditionsResponse500
    | list[ManifestationOutput]
    | None
):
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ManifestationOutput.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if response.status_code == 400:
        response_400 = GetV2TextsTextIdEditionsResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = GetV2TextsTextIdEditionsResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2TextsTextIdEditionsResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2TextsTextIdEditionsResponse400
    | GetV2TextsTextIdEditionsResponse404
    | GetV2TextsTextIdEditionsResponse500
    | list[ManifestationOutput]
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
    edition_type: GetV2TextsTextIdEditionsEditionType | Unset = GetV2TextsTextIdEditionsEditionType.ALL,
) -> Response[
    GetV2TextsTextIdEditionsResponse400
    | GetV2TextsTextIdEditionsResponse404
    | GetV2TextsTextIdEditionsResponse500
    | list[ManifestationOutput]
]:
    """Get instances for text

     Retrieve all instances associated with a text. Optionally filter by instance type (manifestation
    type).

    Args:
        text_id (str):
        edition_type (GetV2TextsTextIdEditionsEditionType | Unset):  Default:
            GetV2TextsTextIdEditionsEditionType.ALL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2TextsTextIdEditionsResponse400 | GetV2TextsTextIdEditionsResponse404 | GetV2TextsTextIdEditionsResponse500 | list[ManifestationOutput]]
    """

    kwargs = _get_kwargs(
        text_id=text_id,
        edition_type=edition_type,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
    edition_type: GetV2TextsTextIdEditionsEditionType | Unset = GetV2TextsTextIdEditionsEditionType.ALL,
) -> (
    GetV2TextsTextIdEditionsResponse400
    | GetV2TextsTextIdEditionsResponse404
    | GetV2TextsTextIdEditionsResponse500
    | list[ManifestationOutput]
    | None
):
    """Get instances for text

     Retrieve all instances associated with a text. Optionally filter by instance type (manifestation
    type).

    Args:
        text_id (str):
        edition_type (GetV2TextsTextIdEditionsEditionType | Unset):  Default:
            GetV2TextsTextIdEditionsEditionType.ALL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2TextsTextIdEditionsResponse400 | GetV2TextsTextIdEditionsResponse404 | GetV2TextsTextIdEditionsResponse500 | list[ManifestationOutput]
    """

    return sync_detailed(
        text_id=text_id,
        client=client,
        edition_type=edition_type,
    ).parsed


async def asyncio_detailed(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
    edition_type: GetV2TextsTextIdEditionsEditionType | Unset = GetV2TextsTextIdEditionsEditionType.ALL,
) -> Response[
    GetV2TextsTextIdEditionsResponse400
    | GetV2TextsTextIdEditionsResponse404
    | GetV2TextsTextIdEditionsResponse500
    | list[ManifestationOutput]
]:
    """Get instances for text

     Retrieve all instances associated with a text. Optionally filter by instance type (manifestation
    type).

    Args:
        text_id (str):
        edition_type (GetV2TextsTextIdEditionsEditionType | Unset):  Default:
            GetV2TextsTextIdEditionsEditionType.ALL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2TextsTextIdEditionsResponse400 | GetV2TextsTextIdEditionsResponse404 | GetV2TextsTextIdEditionsResponse500 | list[ManifestationOutput]]
    """

    kwargs = _get_kwargs(
        text_id=text_id,
        edition_type=edition_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    text_id: str,
    *,
    client: AuthenticatedClient | Client,
    edition_type: GetV2TextsTextIdEditionsEditionType | Unset = GetV2TextsTextIdEditionsEditionType.ALL,
) -> (
    GetV2TextsTextIdEditionsResponse400
    | GetV2TextsTextIdEditionsResponse404
    | GetV2TextsTextIdEditionsResponse500
    | list[ManifestationOutput]
    | None
):
    """Get instances for text

     Retrieve all instances associated with a text. Optionally filter by instance type (manifestation
    type).

    Args:
        text_id (str):
        edition_type (GetV2TextsTextIdEditionsEditionType | Unset):  Default:
            GetV2TextsTextIdEditionsEditionType.ALL.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2TextsTextIdEditionsResponse400 | GetV2TextsTextIdEditionsResponse404 | GetV2TextsTextIdEditionsResponse500 | list[ManifestationOutput]
    """

    return (
        await asyncio_detailed(
            text_id=text_id,
            client=client,
            edition_type=edition_type,
        )
    ).parsed
