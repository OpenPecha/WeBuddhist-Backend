import json
from functools import lru_cache
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.recitations.order.recitation_order_constants import (
    DEFAULT_RECITATION_LANGUAGE,
    RECITATION_ORDER_PATHS,
    SUPPORTED_RECITATION_LANGUAGES,
)
from pecha_api.recitations.recitations_response_models import (
    RecitationDTO,
    RecitationsResponse,
    Segment,
)


def resolve_recitation_language(language: str) -> str:
    normalized_language = (language or DEFAULT_RECITATION_LANGUAGE).lower()
    if normalized_language in SUPPORTED_RECITATION_LANGUAGES:
        return normalized_language
    return DEFAULT_RECITATION_LANGUAGE


@lru_cache(maxsize=len(RECITATION_ORDER_PATHS))
def _load_recitation_order(language: str) -> tuple[RecitationDTO, ...]:
    order_path = RECITATION_ORDER_PATHS.get(language)
    if order_path is None or not order_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recitation order data is not available",
        )

    with order_path.open(encoding="utf-8") as order_file:
        order_data: dict[str, Any] = json.load(order_file)

    return tuple(_parse_recitations(order_data.get("recitations", [])))


def _parse_recitations(recitations: list[dict[str, Any]]) -> list[RecitationDTO]:
    parsed_recitations: list[RecitationDTO] = []
    for recitation in recitations:
        first_segment = None
        raw_first_segment = recitation.get("first_segment")
        if isinstance(raw_first_segment, dict):
            first_segment = Segment(
                id=UUID(raw_first_segment["id"]),
                content=raw_first_segment["content"],
            )

        parsed_recitations.append(
            RecitationDTO(
                title=recitation["title"],
                text_id=recitation["text_id"],
                image_url=recitation.get("image_url"),
                first_segment=first_segment,
            )
        )
    return parsed_recitations


def _filter_recitations_by_search(
    recitations: list[RecitationDTO],
    search: Optional[str],
) -> list[RecitationDTO]:
    if not search or not search.strip():
        return recitations

    search_term = search.strip().casefold()
    return [
        recitation
        for recitation in recitations
        if search_term in recitation.title.casefold()
    ]


def get_ordered_recitations_response(
    *,
    language: str,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> RecitationsResponse:
    resolved_language = resolve_recitation_language(language=language)
    recitations = list(_load_recitation_order(resolved_language))
    filtered_recitations = _filter_recitations_by_search(recitations=recitations, search=search)
    total = len(filtered_recitations)
    paginated_recitations = filtered_recitations[skip : skip + limit]

    return RecitationsResponse(
        recitations=paginated_recitations,
        skip=skip,
        limit=limit,
        total=total,
    )
