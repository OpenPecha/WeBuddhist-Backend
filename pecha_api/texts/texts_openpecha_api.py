from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException
from starlette import status

from pecha_api.external_clients import get_authenticated_open_pecha_client
from pecha_api.texts.text_openpecha_response_models import (
    ContributionModel,
    CriticalEditionModel,
    TextDetailResponse,
    SegmentationResponseModel,
    SegmentLineModel,
    segmentSpans,
    SegmentationSegmentResponseModel,
    EditionContentResponse,
)

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


async def fetch_text_detail(text_id: str) -> TextDetailResponse:
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
        logger.error(f"Unexpected status {response.status_code} fetching text detail for '{text_id}'")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from upstream service",
        )

    return _parse_text_detail(response.json())


async def fetch_critical_editions(text_id: str) -> list[CriticalEditionModel]:
    client = get_authenticated_open_pecha_client()

    try:
        response = await client.get_async_httpx_client().get(
            f"/v2/texts/{text_id}/editions",
            params={"edition_type": "critical"},
        )
    except Exception as e:
        logger.error(f"Failed to fetch critical editions from OpenPecha API: {e}")
        raise

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )

    if response.status_code != 200:
        logger.error(
            f"Unexpected status {response.status_code} fetching critical editions for text '{text_id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from upstream service",
        )

    data = response.json()
    return [
        CriticalEditionModel(
            id=edition["id"],
            text_id=edition["text_id"],
            type=edition["type"],
            source=edition.get("source"),
            colophon=edition.get("colophon"),
            incipit_title=edition.get("incipit_title"),
            alt_incipit_titles=edition.get("alt_incipit_titles"),
            bdrc=edition.get("bdrc"),
            wiki=edition.get("wiki"),
        )
        for edition in data
    ]




async def fetch_editions_segmentation(edition_id: str) -> list[SegmentationResponseModel]:
    client = get_authenticated_open_pecha_client()

    try:
        response = await client.get_async_httpx_client().get(
            f"/v2/editions/{edition_id}/segmentations",
        )
    except Exception as e:
        logger.error(f"Failed to fetch editions segmentation from OpenPecha API: {e}")
        raise

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edition with id '{edition_id}' not found",
        )

    if response.status_code != 200:
        logger.error(f"Unexpected status {response.status_code} fetching editions segmentation for edition '{edition_id}'")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from upstream service",
        )

    data = response.json()
    return [
            SegmentationResponseModel(
                id=segmentation["id"],
                edition_id=segmentation["edition_id"],
                text_id=segmentation["text_id"]
            ) for segmentation in data
        ]


async def fetch_segmentation_segments(segmentation_id: str, limit: int, offset: int) -> SegmentationSegmentResponseModel:
    client = get_authenticated_open_pecha_client()

    try:
        response = await client.get_async_httpx_client().get(
            f"/v2/segmentations/{segmentation_id}/segments",
            params={"limit": limit, "offset": offset},
        )
    except Exception as e:
        logger.error(f"Failed to fetch segmentation segments from OpenPecha API: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch segmentation segments from upstream service",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Segmentation with id '{segmentation_id}' not found",
        )

    if response.status_code != 200:
        logger.error(
            f"Unexpected status {response.status_code} fetching segments for segmentation '{segmentation_id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from upstream service",
        )

    data = response.json()
    return SegmentationSegmentResponseModel(
        items=[
            segmentSpans(
                id=segment["id"],
                lines=[SegmentLineModel(start=line["start"], end=line["end"]) for line in segment.get("lines", [])],
            )
            for segment in data.get("items", [])
        ],
        has_more=data["has_more"],
        offset=data["offset"],
        limit=data["limit"],
    )


async def fetch_edition_content(edition_id: str) -> EditionContentResponse:
    client = get_authenticated_open_pecha_client()

    try:
        response = await client.get_async_httpx_client().get(
            f"/v2/editions/{edition_id}/content",
        )
    except Exception as e:
        logger.error(f"Failed to fetch edition content from OpenPecha API: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch edition content from upstream service",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edition with id '{edition_id}' not found",
        )

    if response.status_code != 200:
        logger.error(
            f"Unexpected status {response.status_code} fetching content for edition '{edition_id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from upstream service",
        )

    return EditionContentResponse(content=response.json())

