from typing import Optional
from uuid import UUID

from pecha_api.plans.groups.group_summary_models import AuthorGroupSummaryDTO
from pecha_api.plans.groups.groups_repository import get_user_series_enrollment_partner_map
from pecha_api.plans.groups.groups_service import get_group_summaries_by_ids
from pecha_api.plans.series.series_response_models import SeriesPartnerDTO, SeriesProgressDTO
from pecha_api.plans.series.series_service import (
    build_series_partner_dto,
    compute_user_series_progress,
)
from pecha_api.plans.users.plan_user_series_repository import get_group_ids_by_series_partner_ids


def series_progress_from_plans(
    plans: list,
    language: Optional[str] = None,
    *,
    completed_day_count: int = 0,
) -> SeriesProgressDTO:
    return compute_user_series_progress(
        plans=plans,
        language=language,
        completed_day_count=completed_day_count,
    )


def load_series_partner_context(
    db,
    user_id: UUID,
    series_ids: list[UUID],
    *,
    language: Optional[str] = None,
) -> tuple[dict[UUID, Optional[AuthorGroupSummaryDTO]], dict[UUID, Optional[SeriesPartnerDTO]]]:
    """Return partner group summaries and partner DTOs keyed by series_id."""
    if not series_ids:
        return {}, {}

    enrollment_partner_map = get_user_series_enrollment_partner_map(
        db=db,
        user_id=user_id,
        series_ids=series_ids,
    )
    series_partner_row_ids = [
        row_id for row_id in enrollment_partner_map.values() if row_id
    ]
    partner_group_id_by_row_id = get_group_ids_by_series_partner_ids(
        db=db,
        series_partner_ids=series_partner_row_ids,
    )
    partner_group_ids = list(partner_group_id_by_row_id.values())
    partner_summaries = (
        get_group_summaries_by_ids(db=db, group_ids=partner_group_ids, language=language)
        if partner_group_ids
        else {}
    )

    partner_group_by_series: dict[UUID, Optional[AuthorGroupSummaryDTO]] = {}
    partner_dto_by_series: dict[UUID, Optional[SeriesPartnerDTO]] = {}
    for series_id in series_ids:
        series_partner_row_id = enrollment_partner_map.get(series_id)
        if not series_partner_row_id:
            partner_group_by_series[series_id] = None
            partner_dto_by_series[series_id] = None
            continue
        partner_group_id = partner_group_id_by_row_id.get(series_partner_row_id)
        partner_group = (
            partner_summaries.get(partner_group_id) if partner_group_id else None
        )
        partner_group_by_series[series_id] = partner_group
        partner_dto_by_series[series_id] = build_series_partner_dto(
            partner_group,
            language=language,
        )

    return partner_group_by_series, partner_dto_by_series


def resolve_series_group_for_user(
    series_id: UUID,
    *,
    series_group_ids: dict[UUID, UUID],
    group_summaries: dict[UUID, AuthorGroupSummaryDTO],
    partner_group_by_series: dict[UUID, Optional[AuthorGroupSummaryDTO]],
    enrollment_partner_map: dict[UUID, Optional[UUID]],
    group_summary_for_id,
) -> Optional[AuthorGroupSummaryDTO]:
    if enrollment_partner_map.get(series_id):
        return partner_group_by_series.get(series_id)
    return group_summary_for_id(series_group_ids.get(series_id), group_summaries)
