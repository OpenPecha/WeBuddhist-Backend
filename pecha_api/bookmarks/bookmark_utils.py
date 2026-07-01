from datetime import timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from pecha_api.bookmarks.bookmark_enums import BookmarkType
from pecha_api.bookmarks.bookmark_models import Bookmark
from pecha_api.bookmarks.bookmark_response_models import (
    BookmarkAccumulatorDTO,
    BookmarkPlanDTO,
    BookmarkSegmentDTO,
    BookmarkSeriesDTO,
    BookmarkTextDTO,
    BookmarkTimerDTO,
    PlanBookmarkMetadataDTO,
)
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
from pecha_api.plans.public.plan_repository import get_published_plan_by_id
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.authors.plan_authors_service import safe_get_image_url
from pecha_api.plans.shared.metadata_utils import filter_by_language_with_fallback
from pecha_api.plans.users.plan_user_series_day_sync_repository import (
    get_sibling_plans_in_series_slot,
)
from pecha_api.plans.series.series_repository import get_series_by_id
from pecha_api.plans.series.series_service import (
    _metadata_response,
    _series_schedule_from_plans,
    _to_plan_status,
)
from pecha_api.accumulator.accumulator_models import Accumulator
from pecha_api.accumulator.accumulator_service import (
    generate_mala_image_presigned_url,
    resolve_accumulator_bookmark_mala_image_url,
)
from pecha_api.mantra.mantra_repository import get_mantra_by_id
from pecha_api.timers.timer_repository import get_timer_by_id

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


def _mantra_metadata_language(entry) -> str:
    return entry.language.value if hasattr(entry.language, "value") else str(entry.language)


def _bookmark_image_url(
    image_key: Optional[str],
    *,
    resource_id: UUID,
    resource_type: str,
) -> Optional[str]:
    image = safe_get_image_url(
        image_key,
        resource_id=resource_id,
        resource_type=resource_type,
    )
    if not image:
        return None
    return image.medium or image.original


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

    segment_dto = None
    if segment_id and segment:
        segment_dto = BookmarkSegmentDTO(
            id=segment_id,
            content=segment.content,
        )

    return {
        "text": BookmarkTextDTO(
            id=text_id,
            title=text.title if text else "",
            segment=segment_dto,
        )
    }


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

    total_days = db.query(PlanItem).filter(PlanItem.plan_id == plan.id).count()
    end_date = None
    if plan.start_date and total_days > 0:
        end_date = plan.start_date + timedelta(days=total_days - 1)

    return {
        "plan": BookmarkPlanDTO(
            id=plan.id,
            metadata=PlanBookmarkMetadataDTO(
                title=plan.title,
                description=plan.description,
                language=_plan_language_code(plan),
            ),
            image=_bookmark_image_url(
                plan.image_url,
                resource_id=plan.id,
                resource_type="plan",
            ),
            start_date=plan.start_date,
            end_date=end_date,
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

    start_date, end_date, _ = _series_schedule_from_plans(
        series.plans,
        published_only=True,
        language=language,
        fallback=True,
    )
    metadata_entries = getattr(series, "metadata_entries", None) or []

    return {
        "series": BookmarkSeriesDTO(
            id=series.id,
            metadata=_metadata_response(
                metadata_entries,
                language=language,
                fallback=True,
            ),
            image=_bookmark_image_url(
                series.image,
                resource_id=series.id,
                resource_type="series",
            ),
            start_date=start_date,
            end_date=end_date,
        )
    }


def _mantra_bookmark_title_image(mantra, language: Optional[str]) -> tuple[str, Optional[str]]:
    """Bookmark (title, image) derived from the linked mantra.

    Either field may be empty when the mantra is only partially populated
    (no default mala image, or no metadata title); callers should fall back
    to the accumulator's own values in that case.
    """
    image = (
        generate_mala_image_presigned_url(mantra.mala.url)
        if mantra.mala is not None
        else None
    )
    entries = list(mantra.metadata_entries)
    if language:
        entries = filter_by_language_with_fallback(
            entries=entries,
            language=language,
            language_of=_mantra_metadata_language,
            fallback_language=DEFAULT_FALLBACK_LANGUAGE,
        )
    title = entries[0].title if entries else ""
    return title or "", image


def _accumulator_bookmark_title(accumulator: Accumulator, language: Optional[str]) -> str:
    """Bookmark title derived from the accumulator's own metadata."""
    entries = list(accumulator.metadata_entries)
    if language:
        entries = filter_by_language_with_fallback(
            entries=entries,
            language=language,
            language_of=_accumulator_metadata_language,
            fallback_language=DEFAULT_FALLBACK_LANGUAGE,
        )
    return (entries[0].name if entries else "") or ""


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

    # Prefer the linked mantra's title/image. Fall back per-field to the
    # accumulator's own values only when the mantra is missing or lacks that
    # field (no default mala image, or no metadata title).
    mantra = (
        get_mantra_by_id(db, accumulator.mantra_id)
        if accumulator.mantra_id is not None
        else None
    )
    if mantra is not None:
        title, image = _mantra_bookmark_title_image(mantra, language)
    else:
        title, image = "", None

    if not title:
        title = _accumulator_bookmark_title(accumulator, language)
    if image is None:
        image = resolve_accumulator_bookmark_mala_image_url(db, accumulator)

    return {
        "accumulator": BookmarkAccumulatorDTO(
            id=accumulator.id,
            title=title,
            image=image,
        )
    }


def enrich_timer_bookmark(db: Session, source_id: str) -> dict:
    timer_id = _parse_source_uuid(source_id)
    if timer_id is None:
        return {}

    timer = get_timer_by_id(db=db, timer_id=timer_id)
    if not timer:
        return {}

    return {
        "timer": BookmarkTimerDTO(
            id=timer.id,
            title=timer.name,
            duration=timer.duration,
        )
    }


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
