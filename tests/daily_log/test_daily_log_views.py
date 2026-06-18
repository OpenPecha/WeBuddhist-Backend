from unittest.mock import patch

import pytest
from fastapi import HTTPException

from pecha_api.daily_log.daily_log_response_models import UserStreakResponse
from pecha_api.daily_log.daily_log_views import get_user_streak


@pytest.mark.asyncio
async def test_get_user_streak_endpoint_success():
    mock_credentials = type("Credentials", (), {"credentials": "test_token"})()

    with patch(
        "pecha_api.daily_log.daily_log_views.get_user_streak_service",
        return_value=UserStreakResponse(streak=5),
    ) as mock_service:
        result = await get_user_streak(authentication_credential=mock_credentials)

        assert result.streak == 5
        mock_service.assert_awaited_once_with(token="test_token")


@pytest.mark.asyncio
async def test_get_user_streak_endpoint_unauthorized():
    mock_credentials = type("Credentials", (), {"credentials": "invalid_token"})()

    with patch(
        "pecha_api.daily_log.daily_log_views.get_user_streak_service",
        side_effect=HTTPException(status_code=401, detail="Invalid token"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_streak(authentication_credential=mock_credentials)

        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_stats_endpoint_success():
    from pecha_api.daily_log.daily_log_response_models import StreakStats, UserStatsResponse
    from pecha_api.daily_log.daily_log_views import get_user_stats

    mock_credentials = type("Credentials", (), {"credentials": "test_token"})()
    response = UserStatsResponse(
        streak=StreakStats(current=3, highest=7, week=[2, 3, 6]),
        total_timer=1200,
        total_accumulated=10800,
        total_practice_days=42,
    )

    with patch(
        "pecha_api.daily_log.daily_log_views.get_user_stats_service",
        return_value=response,
    ) as mock_service:
        result = await get_user_stats(authentication_credential=mock_credentials)

        assert result.streak.highest == 7
        assert result.total_practice_days == 42
        mock_service.assert_awaited_once_with(token="test_token")
