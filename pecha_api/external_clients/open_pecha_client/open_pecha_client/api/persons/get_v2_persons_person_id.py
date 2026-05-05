from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_v2_persons_person_id_response_404 import GetV2PersonsPersonIdResponse404
from ...models.get_v2_persons_person_id_response_500 import GetV2PersonsPersonIdResponse500
from ...models.person_output import PersonOutput
from ...types import Response


def _get_kwargs(
    person_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v2/persons/{person_id}".format(
            person_id=quote(str(person_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput | None:
    if response.status_code == 200:
        response_200 = PersonOutput.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetV2PersonsPersonIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = GetV2PersonsPersonIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    person_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput]:
    """Retrieve person by ID

     Fetch a specific person by their ID

    Args:
        person_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput]
    """

    kwargs = _get_kwargs(
        person_id=person_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    person_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput | None:
    """Retrieve person by ID

     Fetch a specific person by their ID

    Args:
        person_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput
    """

    return sync_detailed(
        person_id=person_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    person_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput]:
    """Retrieve person by ID

     Fetch a specific person by their ID

    Args:
        person_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput]
    """

    kwargs = _get_kwargs(
        person_id=person_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    person_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput | None:
    """Retrieve person by ID

     Fetch a specific person by their ID

    Args:
        person_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetV2PersonsPersonIdResponse404 | GetV2PersonsPersonIdResponse500 | PersonOutput
    """

    return (
        await asyncio_detailed(
            person_id=person_id,
            client=client,
        )
    ).parsed
