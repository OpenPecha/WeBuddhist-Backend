from unittest.mock import MagicMock, patch

import pytest

from pecha_api.plans.groups.invite_expiry_job import _expire_once, run_invite_expiry_scheduler


def test_expire_once_calls_repository():
    with patch("pecha_api.plans.groups.invite_expiry_job.SessionLocal") as mock_session, patch(
        "pecha_api.plans.groups.invite_expiry_job.expire_pending_invites",
        return_value=3,
    ) as mock_expire:
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_session.return_value.__exit__.return_value = False
        _expire_once()
    mock_expire.assert_called_once()


@pytest.mark.asyncio
async def test_run_invite_expiry_scheduler_logs_expire_errors():
    import asyncio

    sleep_calls = 0

    async def fake_sleep(_seconds):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls > 1:
            raise asyncio.CancelledError()

    with patch(
        "pecha_api.plans.groups.invite_expiry_job.asyncio.sleep",
        side_effect=fake_sleep,
    ), patch(
        "pecha_api.plans.groups.invite_expiry_job.asyncio.to_thread",
        side_effect=RuntimeError("db error"),
    ), patch(
        "pecha_api.plans.groups.invite_expiry_job.logging.exception",
    ) as mock_log:
        with pytest.raises(asyncio.CancelledError):
            await run_invite_expiry_scheduler()
    mock_log.assert_called_once()
