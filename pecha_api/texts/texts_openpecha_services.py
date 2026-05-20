from __future__ import annotations

from pecha_api.texts.text_openpecha_response_models import TextDetailResponse
from pecha_api.texts.texts_openpecha_api import fetch_critical_editions, fetch_text_detail


async def get_text_detail_by_id(text_id: str) -> TextDetailResponse:
    text_detail = await fetch_text_detail(text_id=text_id)

    try:
        text_detail.edition_details = await fetch_critical_editions(text_id=text_id)
    except Exception:
        text_detail.edition_details = []

    return text_detail
