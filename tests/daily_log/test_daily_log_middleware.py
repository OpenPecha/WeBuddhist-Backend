from unittest.mock import MagicMock, patch

import pytest

from pecha_api.daily_log.daily_log_middleware import (
    DailyLogMiddleware,
    _log_daily_log_task_error,
    schedule_daily_log,
)


async def _noop_daily_log(_token: str) -> None:
    return None


def test_schedule_daily_log_creates_background_task():
    mock_task = MagicMock()

    with patch(
        "pecha_api.daily_log.daily_log_middleware.record_daily_log_for_token",
        side_effect=_noop_daily_log,
    ), patch(
        "pecha_api.daily_log.daily_log_middleware.asyncio.create_task",
        return_value=mock_task,
    ) as mock_create_task:
        schedule_daily_log(token="test_token")

        mock_create_task.assert_called_once()
        mock_task.add_done_callback.assert_called_once()


def test_log_daily_log_task_error_ignores_cancelled_task():
    task = MagicMock()
    task.cancelled.return_value = True

    with patch("pecha_api.daily_log.daily_log_middleware.logging.error") as mock_log_error:
        _log_daily_log_task_error(task)

        mock_log_error.assert_not_called()


def test_log_daily_log_task_error_ignores_successful_task():
    task = MagicMock()
    task.cancelled.return_value = False
    task.exception.return_value = None

    with patch("pecha_api.daily_log.daily_log_middleware.logging.error") as mock_log_error:
        _log_daily_log_task_error(task)

        mock_log_error.assert_not_called()


def test_log_daily_log_task_error_logs_failed_task():
    task = MagicMock()
    task.cancelled.return_value = False
    task.exception.return_value = RuntimeError("daily log failed")

    with patch("pecha_api.daily_log.daily_log_middleware.logging.error") as mock_log_error:
        _log_daily_log_task_error(task)

        mock_log_error.assert_called_once()


@pytest.mark.asyncio
async def test_daily_log_middleware_schedules_task_without_blocking():
    middleware = DailyLogMiddleware(app=MagicMock())
    request = MagicMock()
    request.headers = {"Authorization": "Bearer test_token"}
    response = MagicMock()

    async def call_next(_request):
        return response

    with patch("pecha_api.daily_log.daily_log_middleware.schedule_daily_log") as mock_schedule:
        result = await middleware.dispatch(request=request, call_next=call_next)

        mock_schedule.assert_called_once_with(token="test_token")
        assert result is response


@pytest.mark.asyncio
async def test_daily_log_middleware_skips_when_bearer_token_is_empty():
    middleware = DailyLogMiddleware(app=MagicMock())
    request = MagicMock()
    request.headers = {"Authorization": "Bearer "}
    response = MagicMock()

    async def call_next(_request):
        return response

    with patch("pecha_api.daily_log.daily_log_middleware.schedule_daily_log") as mock_schedule:
        result = await middleware.dispatch(request=request, call_next=call_next)

        mock_schedule.assert_not_called()
        assert result is response


@pytest.mark.asyncio
async def test_daily_log_middleware_skips_when_no_bearer_token():
    middleware = DailyLogMiddleware(app=MagicMock())
    request = MagicMock()
    request.headers = {}
    response = MagicMock()

    async def call_next(_request):
        return response

    with patch("pecha_api.daily_log.daily_log_middleware.schedule_daily_log") as mock_schedule:
        result = await middleware.dispatch(request=request, call_next=call_next)

        mock_schedule.assert_not_called()
        assert result is response
