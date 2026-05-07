from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_editions_edition_id_metadata_response_404 import GetV2EditionsEditionIdMetadataResponse404
from ...models.get_v2_editions_edition_id_metadata_response_500 import GetV2EditionsEditionIdMetadataResponse500
from ...models.manifestation_output import ManifestationOutput
from ...types import Response


def _get_kwargs(
    edition_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/editions/{edition_id}/metadata".format(
            edition_id=quote(str(edition_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput | None:
    if response.status_code == 200:
        response_200 = ManifestationOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2EditionsEditionIdMetadataResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2EditionsEditionIdMetadataResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput
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
) -> Response[
    GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput
]:
    """Retrieve edition metadata

     Fetch metadata for a given edition ID

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput]
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
) -> GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput | None:
    """Retrieve edition metadata

     Fetch metadata for a given edition ID

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput
    """

    return sync_detailed(
        edition_id=edition_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    edition_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput
]:
    """Retrieve edition metadata

     Fetch metadata for a given edition ID

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput]
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
) -> GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput | None:
    """Retrieve edition metadata

     Fetch metadata for a given edition ID

    Args:
        edition_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2EditionsEditionIdMetadataResponse404 | GetV2EditionsEditionIdMetadataResponse500 | ManifestationOutput
    """

    return (
        await asyncio_detailed(
            edition_id=edition_id,
            client=client,
        )
    ).parsed
