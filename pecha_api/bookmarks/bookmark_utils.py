from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from pecha_api.bookmarks.bookmark_enums import BookmarkType
from pecha_api.bookmarks.bookmark_models import Bookmark
from pecha_api.texts.segments.segments_models import Segment
from pecha_api.texts.segments.segments_repository import (
    get_related_mapped_segments,
    get_segment_by_id,
)
from pecha_api.texts.texts_repository import (
    get_all_texts_by_group_id,
    get_first_segment_table_of_content,
    get_texts_by_id,
)
from pecha_api.plans.public.plan_response_models import PublicPlanDTO, AuthorDTO
from pecha_api.plans.public.plan_repository import get_published_plan_by_id
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.groups.groups_repository import get_group_id_for_plan
from pecha_api.plans.tags.tag_helpers import tags_to_summary_dtos
from pecha_api.plans.authors.plan_authors_service import get_image_url
from pecha_api.plans.shared.metadata_utils import filter_by_language_with_fallback
from pecha_api.plans.users.plan_user_series_day_sync_repository import (
    get_sibling_plans_in_series_slot,
)
from pecha_api.plans.series.series_repository import (
    get_series_by_id,
    get_active_plan_count_map_by_series_ids,
    get_enrolled_count_map_by_series_ids,
)
from pecha_api.plans.series.series_service import (
    _group_summary_for_series,
    _series_schedule_from_plans,
    _series_to_list_item_dto,
    _to_plan_status,
)
from pecha_api.accumulator.accumulator_models import Accumulator
from pecha_api.accumulator.accumulator_service import (
    convert_accumulator_to_dto,
    convert_metadata_to_dto,
)
from pecha_api.timers.timer_repository import get_timer_by_id
from pecha_api.timers.timer_service import convert_timer_to_dto

DEFAULT_FALLBACK_LANGUAGE = "EN"


def _normalize_language(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    normalized = language.strip().upper()
    return normalized or None


def _plan_language_code(plan) -> str:
    return plan.language.value if hasattr(plan.language, "value") else str(plan.language)


def _accumulator_metadata_language(entry) -> str:
    return entry.language.value if hasattr(entry.language, "value") else str(entry.language)


def _text_language_code(text) -> str:
    return text.language if isinstance(text.language, str) else str(text.language)


async def _resolve_segment_by_ref(segment_ref: str) -> Optional[Segment]:
    try:
        UUID(segment_ref)
        segment = await get_segment_by_id(segment_id=segment_ref)
        if segment:
            return segment
    except ValueError:
        pass
    return await Segment.get_segment_by_pecha_segment_id(pecha_segment_id=segment_ref)


async def _resolve_text_segment(
    text_id: str,
    verse_id: Optional[str],
) -> tuple[Optional[str], Optional[Segment]]:
    if verse_id:
        segment = await _resolve_segment_by_ref(verse_id)
        if segment and segment.text_id == text_id:
            return str(segment.id), segment

    segment_id, _ = await get_first_segment_table_of_content(text_id=text_id)
    if segment_id:
        segment = await get_segment_by_id(segment_id=segment_id)
        return segment_id, segment

    segment = await Segment.get_first_segment_by_text_id(text_id=text_id)
    if segment:
        return str(segment.id), segment

    return None, None


async def enrich_text_bookmark(
    bookmark: Bookmark,
    language: Optional[str] = None,
) -> dict:
    verse_id: Optional[str] = None
    text_id: Optional[str] = None

    if bookmark.type == BookmarkType.VERSE:
        verse_id = bookmark.source_id
        segment = await _resolve_segment_by_ref(verse_id)
        if not segment:
            return {}
        text_id = segment.text_id
        segment_id = str(segment.id)
    elif bookmark.type == BookmarkType.TEXT:
        text_id = bookmark.source_id
        if bookmark.name:
            candidate = await _resolve_segment_by_ref(bookmark.name)
            if candidate and candidate.text_id == text_id:
                verse_id = bookmark.name
        segment_id, segment = await _resolve_text_segment(text_id=text_id, verse_id=verse_id)
        if not segment_id:
            return {}
    else:
        return {}

    if language:
        text = await _resolve_localized_text(text_id=text_id, language=language)
        if text:
            text_id = str(text.id)
        else:
            text = await get_texts_by_id(text_id=text_id)
    else:
        text = await get_texts_by_id(text_id=text_id)

    if language and segment and text_id != segment.text_id:
        localized_segment = await _resolve_localized_segment(
            segment=segment,
            target_text_id=text_id,
        )
        if localized_segment:
            segment = localized_segment
            segment_id = str(segment.id)

    result = {
        "text_id": text_id,
        "text_title": text.title if text else None,
        "segment_id": segment_id,
        "segment_content": segment.content if segment else None,
    }

    if verse_id:
        result["verse_id"] = verse_id

    return result


async def _resolve_localized_text(text_id: str, language: Optional[str]):
    text = await get_texts_by_id(text_id=text_id)
    if not text or not language:
        return text

    group_texts = await get_all_texts_by_group_id(group_id=text.group_id)
    if not group_texts:
        return text

    matched = filter_by_language_with_fallback(
        entries=group_texts,
        language=language,
        language_of=_text_language_code,
        fallback_language=DEFAULT_FALLBACK_LANGUAGE,
    )
    return matched[0] if matched else text


async def _resolve_localized_segment(segment: Segment, target_text_id: str) -> Optional[Segment]:
    if segment.text_id == target_text_id:
        return segment

    mapped_segments = await get_related_mapped_segments(parent_segment_id=str(segment.id))
    for mapped in mapped_segments:
        if mapped.text_id == target_text_id:
            localized = await get_segment_by_id(segment_id=str(mapped.id))
            return localized or mapped
    return segment


def _resolve_published_plan_for_language(
    db: Session,
    plan_id: UUID,
    language: Optional[str],
):
    plan = get_published_plan_by_id(db=db, plan_id=plan_id)
    if not plan or not language:
        return plan

    candidates = [plan]
    if plan.series_id is not None and plan.display_order is not None:
        siblings = get_sibling_plans_in_series_slot(
            db=db,
            series_id=plan.series_id,
            display_order=plan.display_order,
            exclude_plan_id=plan.id,
        )
        for sibling in siblings:
            published_sibling = get_published_plan_by_id(db=db, plan_id=sibling.id)
            if published_sibling:
                candidates.append(published_sibling)

    matched = filter_by_language_with_fallback(
        entries=candidates,
        language=language,
        language_of=_plan_language_code,
        fallback_language=DEFAULT_FALLBACK_LANGUAGE,
    )
    return matched[0] if matched else plan


def enrich_plan_bookmark(
    db: Session,
    source_id: str,
    language: Optional[str] = None,
) -> dict:
    plan_id = _parse_source_uuid(source_id)
    if plan_id is None:
        return {}

    plan = _resolve_published_plan_for_language(db=db, plan_id=plan_id, language=language)
    if not plan:
        return {}

    tag_language = _normalize_language(language) or DEFAULT_FALLBACK_LANGUAGE
    plan_image = get_image_url(image_url=plan.image_url)
    author_dto = None
    if plan.author:
        author_image = get_image_url(image_url=plan.author.image_url)
        author_dto = AuthorDTO(
            id=plan.author.id,
            firstname=plan.author.first_name,
            lastname=plan.author.last_name,
            image=author_image,
        )

    total_days = db.query(PlanItem).filter(PlanItem.plan_id == plan.id).count()
    group_id = get_group_id_for_plan(db=db, plan_id=plan.id)

    return {
        "plan": PublicPlanDTO(
            id=plan.id,
            title=plan.title,
            description=plan.description,
            language=_plan_language_code(plan),
            difficulty_level=plan.difficulty_level,
            image=plan_image,
            total_days=total_days,
            tags=tags_to_summary_dtos(plan.tag_list, language=tag_language),
            author=author_dto,
            start_date=plan.start_date,
            display_order=plan.display_order,
            group_id=group_id,
        )
    }


def enrich_series_bookmark(
    db: Session,
    source_id: str,
    language: Optional[str] = None,
) -> dict:
    series_id = _parse_source_uuid(source_id)
    if series_id is None:
        return {}

    series = get_series_by_id(db=db, series_id=series_id)
    if not series or _to_plan_status(series.status) != PlanStatus.PUBLISHED:
        return {}

    plan_count = get_active_plan_count_map_by_series_ids(
        db, [series_id], published_only=True
    ).get(series_id, 0)
    enrolled_count = get_enrolled_count_map_by_series_ids(db, [series_id]).get(series_id, 0)
    start_date, end_date, total_days = _series_schedule_from_plans(
        series.plans,
        published_only=True,
        language=language,
        fallback=True,
    )

    return {
        "series": _series_to_list_item_dto(
            series,
            plan_count=plan_count,
            enrolled_count=enrolled_count,
            language=language,
            group=_group_summary_for_series(db=db, series=series, language=language),
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            fallback=True,
        )
    }


def enrich_accumulator_bookmark(
    db: Session,
    source_id: str,
    language: Optional[str] = None,
) -> dict:
    accumulator_id = _parse_source_uuid(source_id)
    if accumulator_id is None:
        return {}

    accumulator = (
        db.query(Accumulator)
        .options(
            selectinload(Accumulator.metadata_entries),
            selectinload(Accumulator.mala),
        )
        .filter(
            Accumulator.id == accumulator_id,
            Accumulator.deleted_at.is_(None),
        )
        .first()
    )
    if not accumulator:
        return {}

    dto = convert_accumulator_to_dto(accumulator)
    if language:
        matched_metadata = filter_by_language_with_fallback(
            entries=list(accumulator.metadata_entries),
            language=language,
            language_of=_accumulator_metadata_language,
            fallback_language=DEFAULT_FALLBACK_LANGUAGE,
        )
        dto.metadata = [convert_metadata_to_dto(entry) for entry in matched_metadata]

    return {"accumulator": dto}


def enrich_timer_bookmark(db: Session, source_id: str) -> dict:
    timer_id = _parse_source_uuid(source_id)
    if timer_id is None:
        return {}

    timer = get_timer_by_id(db=db, timer_id=timer_id)
    if not timer:
        return {}

    return {"timer": convert_timer_to_dto(timer)}


def _parse_source_uuid(source_id: str) -> Optional[UUID]:
    try:
        return UUID(source_id)
    except ValueError:
        return None


async def enrich_bookmark(
    bookmark: Bookmark,
    db: Session,
    language: Optional[str] = None,
) -> dict:
    normalized_language = _normalize_language(language)
    if bookmark.type in (BookmarkType.TEXT, BookmarkType.VERSE):
        return await enrich_text_bookmark(bookmark, language=normalized_language)
    if bookmark.type == BookmarkType.PLAN:
        return enrich_plan_bookmark(
            db=db,
            source_id=bookmark.source_id,
            language=normalized_language,
        )
    if bookmark.type == BookmarkType.SERIES:
        return enrich_series_bookmark(
            db=db,
            source_id=bookmark.source_id,
            language=normalized_language,
        )
    if bookmark.type == BookmarkType.ACCUMULATOR:
        return enrich_accumulator_bookmark(
            db=db,
            source_id=bookmark.source_id,
            language=normalized_language,
        )
    if bookmark.type == BookmarkType.TIMER:
        return enrich_timer_bookmark(db=db, source_id=bookmark.source_id)
    return {}
