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
