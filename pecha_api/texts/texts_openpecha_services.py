from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel
from starlette import status

from pecha_api.config import get
from pecha_api.external_clients import get_authenticated_open_pecha_client
from pecha_api.external_clients.open_pecha_client.open_pecha_client.api.texts import get_v2_texts_text_id
from pecha_api.external_clients.open_pecha_client.open_pecha_client.models.expression_output import ExpressionOutput
from pecha_api.external_clients.open_pecha_client.open_pecha_client.models.get_v2_texts_text_id_response_404 import (
    GetV2TextsTextIdResponse404,
)
from pecha_api.external_clients.open_pecha_client.open_pecha_client.types import UNSET

logger = logging.getLogger(__name__)


class ContributionModel(BaseModel):
    role: str
    person_id: Optional[str] = None
    person_bdrc_id: Optional[str] = None
    person_name: Optional[dict] = None
    ai_id: Optional[str] = None


class TextDetailResponse(BaseModel):
    id: str
    title: dict
    language: str
    category_id: str
    license: str
    contributions: list[ContributionModel]
    commentaries: list[str]
    translations: list[str]
    editions: list[str]
    bdrc: Optional[str] = None
    wiki: Optional[str] = None
    date: Optional[str] = None
    alt_titles: Optional[list[dict]] = None
    commentary_of: Optional[str] = None
    translation_of: Optional[str] = None


def _unset_to_none(value):
    return None if isinstance(value, type(UNSET)) or value is UNSET else value


def _expression_output_to_text_detail(expression: ExpressionOutput) -> TextDetailResponse:
    title = expression.title.to_dict() if hasattr(expression.title, "to_dict") else {}

    contributions = [
        ContributionModel(
            role=c.role.value if hasattr(c.role, "value") else str(c.role),
            person_id=_unset_to_none(c.person_id),
            person_bdrc_id=_unset_to_none(c.person_bdrc_id),
            person_name=(
                c.person_name.to_dict()
                if hasattr(c, "person_name") and hasattr(c.person_name, "to_dict")
                else _unset_to_none(c.person_name) if hasattr(c, "person_name") else None
            ),
            ai_id=_unset_to_none(c.ai_id) if hasattr(c, "ai_id") else None,
        )
        for c in expression.contributions
    ]

    alt_titles_raw = _unset_to_none(expression.alt_titles)
    alt_titles = None
    if alt_titles_raw is not None and isinstance(alt_titles_raw, list):
        alt_titles = [item.to_dict() if hasattr(item, "to_dict") else item for item in alt_titles_raw]

    return TextDetailResponse(
        id=expression.id,
        title=title,
        language=expression.language,
        category_id=expression.category_id,
        license=expression.license_.value if hasattr(expression.license_, "value") else str(expression.license_),
        contributions=contributions,
        commentaries=expression.commentaries,
        translations=expression.translations,
        editions=expression.editions,
        bdrc=_unset_to_none(expression.bdrc),
        wiki=_unset_to_none(expression.wiki),
        date=_unset_to_none(expression.date),
        alt_titles=alt_titles,
        commentary_of=_unset_to_none(expression.commentary_of),
        translation_of=_unset_to_none(expression.translation_of),
    )


async def get_text_detail_by_id(text_id: str) -> TextDetailResponse:
    client = get_authenticated_open_pecha_client()

    try:
        result = await get_v2_texts_text_id.asyncio(
            text_id=text_id,
            client=client,
        )
    except Exception as e:
        logger.error(
            f"Failed to fetch text detail from OpenPecha API: {e} | "
            f"URL: {client._base_url}/v2/texts/{text_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text detail from upstream service"
        )

    if isinstance(result, GetV2TextsTextIdResponse404):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found"
        )

    if result is None or not isinstance(result, ExpressionOutput):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from upstream service"
        )

    return _expression_output_to_text_detail(result)
