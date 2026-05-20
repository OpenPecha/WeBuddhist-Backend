from __future__ import annotations

import logging
from typing import Any, List

from fastapi import HTTPException
from starlette import status

from pecha_api.external_clients import get_authenticated_open_pecha_client
from pecha_api.texts.text_openpecha_response_models import ContributionModel, TextDetailResponse, CriticalEditionModel
from pecha_api.texts.texts_response_models import TextDTO

logger = logging.getLogger(__name__)


def _parse_text_detail(data: dict[str, Any]) -> TextDetailResponse:
    contributions = [
        ContributionModel(
            role=c.get("role", ""),
            person_id=c.get("person_id"),
            person_bdrc_id=c.get("person_bdrc_id"),
            person_name=c.get("person_name"),
            ai_id=c.get("ai_id"),
        )
        for c in data.get("contributions", [])
    ]

    alt_titles_raw = data.get("alt_titles")
    alt_titles = alt_titles_raw if isinstance(alt_titles_raw, list) else None

    return TextDetailResponse(
        id=data["id"],
        title=data.get("title") or {},
        language=data["language"],
        category_id=data["category_id"],
        license=data.get("license", ""),
        contributions=contributions,
        commentaries=data.get("commentaries", []),
        translations=data.get("translations", []),
        editions=data.get("editions", []),
        bdrc=data.get("bdrc"),
        wiki=data.get("wiki"),
        date=data.get("date"),
        alt_titles=alt_titles,
        commentary_of=data.get("commentary_of"),
        translation_of=data.get("translation_of"),
    )


async def _fetch_critical_edition(text_id: str) -> List[TextDTO]:
    client = get_authenticated_open_pecha_client()

    try:
        response = await client.get_async_httpx_client().get(
            f"/v2/texts/{text_id}/editions",
            params={"edition_type": "critical"},
        )
    except Exception as e:
        logger.error(f"Failed to fetch critical editions from OpenPecha API: {e}")
        return []

    if response.status_code == 404:
        return []

    if response.status_code != 200:
        logger.error(
            f"Unexpected status {response.status_code} fetching critical editions for text '{text_id}'"
        )
        return []

    editions_data = response.json()


    return [
            CriticalEditionModel(
                id=edition["id"],
                text_id=edition["text_id"],
                type=edition["type"],
                source=edition["source"],
                colophon=edition["colophon"],
                incipit_title=edition["incipit_title"],
                alt_incipit_titles=edition["alt_incipit_titles"],
                bdrc=edition["bdrc"],
                wiki=edition["wiki"],
            )
            for edition in editions_data
    ]


async def get_text_detail_by_id(text_id: str) -> TextDetailResponse:
    client = get_authenticated_open_pecha_client()

    try:
        response = await client.get_async_httpx_client().get(f"/v2/texts/{text_id}")
    except Exception as e:
        logger.error(
            f"Failed to fetch text detail from OpenPecha API: {e} | "
            f"URL: {client._base_url}/v2/texts/{text_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text detail from upstream service",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )

    if response.status_code != 200:
        logger.error(
            f"Unexpected status {response.status_code} fetching text detail for '{text_id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from upstream service",
        )

    text_detail = _parse_text_detail(response.json())
    text_detail.edition_details = await _fetch_critical_edition(text_id=text_id)
    return text_detail
