import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from pecha_api.plans.analytics.analytics_response_models import AnalyticsOverviewResponse
from pecha_api.plans.analytics.analytics_service import (
    _normalize_date_range,
    get_analytics_overview,
)
from pecha_api.plans.analytics.analytics_views import get_cms_analytics_overview
from pecha_api.plans.platform_enums import PlatformRole


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def _make_author(*, is_admin=True):
    author = MagicMock()
    author.id = uuid.uuid4()
    author.platform_role = PlatformRole.SUPER_ADMIN if is_admin else PlatformRole.CREATOR
    author.is_active = True
    return author


def test_normalize_date_range_rejects_inverted_range():
    with pytest.raises(HTTPException) as exc:
        _normalize_date_range(date(2026, 7, 10), date(2026, 7, 1))
    assert exc.value.status_code == 400


def test_normalize_date_range_rejects_too_long_range():
    with pytest.raises(HTTPException) as exc:
        _normalize_date_range(date(2025, 1, 1), date(2026, 7, 1))
    assert exc.value.status_code == 400


@patch("pecha_api.plans.analytics.analytics_service.repo.get_completions_by_day", return_value=[])
@patch("pecha_api.plans.analytics.analytics_service.repo.get_joins_by_day", return_value=[])
@patch("pecha_api.plans.analytics.analytics_service.repo.get_user_growth_by_day", return_value=[])
@patch("pecha_api.plans.analytics.analytics_service.repo.get_top_plans", return_value=[])
@patch("pecha_api.plans.analytics.analytics_service.repo.count_new_users_between", return_value=4)
@patch("pecha_api.plans.analytics.analytics_service.repo.count_total_users", return_value=100)
@patch("pecha_api.plans.analytics.analytics_service.SessionLocal")
@patch("pecha_api.plans.analytics.analytics_service.validate_cms_author_details")
def test_get_analytics_overview_returns_user_and_timeline_stats(
    mock_validate,
    mock_session_local,
    mock_total_users,
    mock_new_users,
    mock_top_plans,
    mock_user_growth,
    mock_joins,
    mock_completions,
):
    mock_validate.return_value = _make_author(is_admin=True)
    _session_local_context(mock_session_local)

    plan_id = uuid.uuid4()
    series_id = uuid.uuid4()
    top_row = MagicMock(
        id=plan_id,
        title="Morning Practice",
        series_id=series_id,
        series_name="Daily Series",
        join_count=12,
        completion_count=5,
    )
    mock_top_plans.return_value = [top_row]
    mock_user_growth.return_value = [(date(2026, 7, 1), 2)]
    mock_joins.return_value = [(date(2026, 7, 1), 3)]
    mock_completions.return_value = [(date(2026, 7, 1), 1)]
    mock_new_users.side_effect = [7, 4]

    result = get_analytics_overview(
        token="token",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 2),
        top_limit=10,
    )

    assert isinstance(result, AnalyticsOverviewResponse)
    assert result.users.total_users == 100
    assert result.users.new_users_this_month == 7
    assert result.users.new_users_in_range == 4
    assert len(result.top_plans) == 1
    assert result.top_plans[0].title == "Morning Practice"
    assert result.top_plans[0].series_name == "Daily Series"
    assert result.top_plans[0].join_count == 12
    assert result.top_plans[0].completion_count == 5
    assert len(result.timeline) == 2
    assert result.timeline[0].new_users == 2
    assert result.timeline[0].joins == 3
    assert result.timeline[0].completions == 1
    assert result.timeline[1].new_users == 0
    mock_total_users.assert_called_once()


@patch("pecha_api.plans.analytics.analytics_views.get_analytics_overview")
def test_get_cms_analytics_overview_delegates_to_service(mock_service):
    expected = MagicMock()
    mock_service.return_value = expected
    auth = MagicMock()
    auth.credentials = "token123"

    resp = get_cms_analytics_overview(
        authentication_credential=auth,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 21),
        group_id=None,
        top_limit=10,
    )

    assert resp == expected
    mock_service.assert_called_once_with(
        token="token123",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 21),
        group_id=None,
        top_limit=10,
    )
