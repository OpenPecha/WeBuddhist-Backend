from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.patch_v2_persons_person_id_response_400 import PatchV2PersonsPersonIdResponse400
from ...models.patch_v2_persons_person_id_response_404 import PatchV2PersonsPersonIdResponse404
from ...models.patch_v2_persons_person_id_response_409 import PatchV2PersonsPersonIdResponse409
from ...models.patch_v2_persons_person_id_response_422 import PatchV2PersonsPersonIdResponse422
from ...models.patch_v2_persons_person_id_response_500 import PatchV2PersonsPersonIdResponse500
from ...models.person_output import PersonOutput
from ...models.person_patch import PersonPatch
from ...types import Response


def _get_kwargs(
    person_id: str,
    *,
    body: PersonPatch,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/v2/persons/{person_id}".format(
            person_id=quote(str(person_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PatchV2PersonsPersonIdResponse400
    | PatchV2PersonsPersonIdResponse404
    | PatchV2PersonsPersonIdResponse409
    | PatchV2PersonsPersonIdResponse422
    | PatchV2PersonsPersonIdResponse500
    | PersonOutput
    | None
):
    if response.status_code == 200:
        response_200 = PersonOutput.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = PatchV2PersonsPersonIdResponse400.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = PatchV2PersonsPersonIdResponse404.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PatchV2PersonsPersonIdResponse409.from_dict(response.json())

        return response_409

    if response.status_code == 422:
        response_422 = PatchV2PersonsPersonIdResponse422.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = PatchV2PersonsPersonIdResponse500.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PatchV2PersonsPersonIdResponse400
    | PatchV2PersonsPersonIdResponse404
    | PatchV2PersonsPersonIdResponse409
    | PatchV2PersonsPersonIdResponse422
    | PatchV2PersonsPersonIdResponse500
    | PersonOutput
]:
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
    body: PersonPatch,
) -> Response[
    PatchV2PersonsPersonIdResponse400
    | PatchV2PersonsPersonIdResponse404
    | PatchV2PersonsPersonIdResponse409
    | PatchV2PersonsPersonIdResponse422
    | PatchV2PersonsPersonIdResponse500
    | PersonOutput
]:
    """Update a person

     Partially update a person record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        person_id (str):
        body (PersonPatch): Partial update for a person. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PatchV2PersonsPersonIdResponse400 | PatchV2PersonsPersonIdResponse404 | PatchV2PersonsPersonIdResponse409 | PatchV2PersonsPersonIdResponse422 | PatchV2PersonsPersonIdResponse500 | PersonOutput]
    """

    kwargs = _get_kwargs(
        person_id=person_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    person_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonPatch,
) -> (
    PatchV2PersonsPersonIdResponse400
    | PatchV2PersonsPersonIdResponse404
    | PatchV2PersonsPersonIdResponse409
    | PatchV2PersonsPersonIdResponse422
    | PatchV2PersonsPersonIdResponse500
    | PersonOutput
    | None
):
    """Update a person

     Partially update a person record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        person_id (str):
        body (PersonPatch): Partial update for a person. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PatchV2PersonsPersonIdResponse400 | PatchV2PersonsPersonIdResponse404 | PatchV2PersonsPersonIdResponse409 | PatchV2PersonsPersonIdResponse422 | PatchV2PersonsPersonIdResponse500 | PersonOutput
    """

    return sync_detailed(
        person_id=person_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    person_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonPatch,
) -> Response[
    PatchV2PersonsPersonIdResponse400
    | PatchV2PersonsPersonIdResponse404
    | PatchV2PersonsPersonIdResponse409
    | PatchV2PersonsPersonIdResponse422
    | PatchV2PersonsPersonIdResponse500
    | PersonOutput
]:
    """Update a person

     Partially update a person record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        person_id (str):
        body (PersonPatch): Partial update for a person. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PatchV2PersonsPersonIdResponse400 | PatchV2PersonsPersonIdResponse404 | PatchV2PersonsPersonIdResponse409 | PatchV2PersonsPersonIdResponse422 | PatchV2PersonsPersonIdResponse500 | PersonOutput]
    """

    kwargs = _get_kwargs(
        person_id=person_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    person_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PersonPatch,
) -> (
    PatchV2PersonsPersonIdResponse400
    | PatchV2PersonsPersonIdResponse404
    | PatchV2PersonsPersonIdResponse409
    | PatchV2PersonsPersonIdResponse422
    | PatchV2PersonsPersonIdResponse500
    | PersonOutput
    | None
):
    """Update a person

     Partially update a person record. Only provided fields will be updated; omitted fields retain their
    current values.

    Args:
        person_id (str):
        body (PersonPatch): Partial update for a person. At least one field must be provided.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PatchV2PersonsPersonIdResponse400 | PatchV2PersonsPersonIdResponse404 | PatchV2PersonsPersonIdResponse409 | PatchV2PersonsPersonIdResponse422 | PatchV2PersonsPersonIdResponse500 | PersonOutput
    """

    return (
        await asyncio_detailed(
            person_id=person_id,
            client=client,
            body=body,
        )
    ).parsed
