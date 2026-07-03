import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pecha_api.plans.groups.group_summary_models import AuthorGroupSummaryDTO
from pecha_api.plans.groups.groups_enums import AuthorGroupType
from pecha_api.plans.series.series_response_models import SeriesPartnerDTO
from pecha_api.plans.users.series_user_progress import (
    load_series_partner_context,
    resolve_series_group_for_user,
    series_progress_from_plans,
)


def _published_plan(*, plan_id, item_count=3, start_date=None):
    from datetime import datetime, timezone

    return SimpleNamespace(
        id=plan_id,
        deleted_at=None,
        status=SimpleNamespace(value="PUBLISHED"),
        display_order=0,
        start_date=start_date or datetime(2020, 1, 1, tzinfo=timezone.utc),
        language=SimpleNamespace(value="EN"),
        items=[SimpleNamespace() for _ in range(item_count)],
    )


def test_series_progress_from_plans_delegates_to_compute_user_series_progress():
    plan_id = uuid.uuid4()
    plan = _published_plan(plan_id=plan_id, item_count=2)

    progress = series_progress_from_plans([plan], language="en", completed_day_count=1)

    assert progress.total_day_count == 2
    assert progress.current_day_number == 1


def test_load_series_partner_context_returns_empty_for_no_series_ids():
    partner_groups, partner_dtos = load_series_partner_context(
        db=MagicMock(),
        user_id=uuid.uuid4(),
        series_ids=[],
        language="en",
    )

    assert partner_groups == {}
    assert partner_dtos == {}


def test_load_series_partner_context_builds_partner_dto_for_enrolled_series():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    series_partner_row_id = uuid.uuid4()
    partner_group_id = uuid.uuid4()
    partner_group = AuthorGroupSummaryDTO(
        id=partner_group_id,
        slug="partner-group",
        group_type=AuthorGroupType.COMMUNITY,
        is_public=True,
        avatar_url="https://partner.example/avatar.jpg",
    )
    partner_dto = SeriesPartnerDTO(
        group_name="Partner Group",
        group_image="https://partner.example/avatar.jpg",
    )

    with patch(
        "pecha_api.plans.users.series_user_progress.get_user_series_enrollment_partner_map",
        return_value={series_id: series_partner_row_id},
    ), patch(
        "pecha_api.plans.users.series_user_progress.get_group_ids_by_series_partner_ids",
        return_value={series_partner_row_id: partner_group_id},
    ), patch(
        "pecha_api.plans.users.series_user_progress.get_group_summaries_by_ids",
        return_value={partner_group_id: partner_group},
    ), patch(
        "pecha_api.plans.users.series_user_progress.build_series_partner_dto",
        return_value=partner_dto,
    ):
        partner_groups, partner_dtos = load_series_partner_context(
            db=MagicMock(),
            user_id=user_id,
            series_ids=[series_id],
            language="en",
        )

    assert partner_groups[series_id] == partner_group
    assert partner_dtos[series_id] == partner_dto


def test_load_series_partner_context_returns_none_when_series_not_partner_enrolled():
    series_id = uuid.uuid4()

    with patch(
        "pecha_api.plans.users.series_user_progress.get_user_series_enrollment_partner_map",
        return_value={series_id: None},
    ):
        partner_groups, partner_dtos = load_series_partner_context(
            db=MagicMock(),
            user_id=uuid.uuid4(),
            series_ids=[series_id],
            language="en",
        )

    assert partner_groups[series_id] is None
    assert partner_dtos[series_id] is None


def test_load_series_partner_context_handles_missing_partner_group_lookup():
    series_id = uuid.uuid4()
    series_partner_row_id = uuid.uuid4()

    with patch(
        "pecha_api.plans.users.series_user_progress.get_user_series_enrollment_partner_map",
        return_value={series_id: series_partner_row_id},
    ), patch(
        "pecha_api.plans.users.series_user_progress.get_group_ids_by_series_partner_ids",
        return_value={},
    ), patch(
        "pecha_api.plans.users.series_user_progress.build_series_partner_dto",
        return_value=None,
    ) as mock_build:
        partner_groups, partner_dtos = load_series_partner_context(
            db=MagicMock(),
            user_id=uuid.uuid4(),
            series_ids=[series_id],
            language="en",
        )

    assert partner_groups[series_id] is None
    assert partner_dtos[series_id] is None
    mock_build.assert_called_once_with(None, language="en")


def test_resolve_series_group_for_user_prefers_partner_group_when_enrolled_via_partner():
    series_id = uuid.uuid4()
    creator_group_id = uuid.uuid4()
    partner_group = AuthorGroupSummaryDTO(
        id=uuid.uuid4(),
        slug="partner",
        group_type=AuthorGroupType.COMMUNITY,
        is_public=True,
    )
    creator_group = AuthorGroupSummaryDTO(
        id=creator_group_id,
        slug="creator",
        group_type=AuthorGroupType.COMMUNITY,
        is_public=True,
    )

    resolved = resolve_series_group_for_user(
        series_id,
        series_group_ids={series_id: creator_group_id},
        group_summaries={creator_group_id: creator_group},
        partner_group_by_series={series_id: partner_group},
        enrollment_partner_map={series_id: uuid.uuid4()},
        group_summary_for_id=lambda group_id, summaries: summaries.get(group_id),
    )

    assert resolved == partner_group


def test_resolve_series_group_for_user_uses_creator_group_without_partner_enrollment():
    series_id = uuid.uuid4()
    creator_group_id = uuid.uuid4()
    creator_group = AuthorGroupSummaryDTO(
        id=creator_group_id,
        slug="creator",
        group_type=AuthorGroupType.COMMUNITY,
        is_public=True,
    )

    resolved = resolve_series_group_for_user(
        series_id,
        series_group_ids={series_id: creator_group_id},
        group_summaries={creator_group_id: creator_group},
        partner_group_by_series={series_id: None},
        enrollment_partner_map={series_id: None},
        group_summary_for_id=lambda group_id, summaries: summaries.get(group_id),
    )

    assert resolved == creator_group
