from unittest.mock import MagicMock, patch

import pytest

from pecha_api.scheduler import setup_scheduler, shutdown_scheduler


def test_setup_scheduler_rejects_non_positive_retention():
    with patch("pecha_api.scheduler.get_int", return_value=0), patch(
        "pecha_api.scheduler.scheduler"
    ) as mock_scheduler:
        mock_scheduler.running = False

        with pytest.raises(ValueError, match="positive integer"):
            setup_scheduler()

        mock_scheduler.add_job.assert_not_called()
        mock_scheduler.start.assert_not_called()


def test_setup_scheduler_rejects_negative_retention():
    with patch("pecha_api.scheduler.get_int", return_value=-7), patch(
        "pecha_api.scheduler.scheduler"
    ) as mock_scheduler:
        mock_scheduler.running = False

        with pytest.raises(ValueError, match="positive integer"):
            setup_scheduler()

        mock_scheduler.add_job.assert_not_called()


def test_setup_scheduler_registers_cleanup_job():
    with patch("pecha_api.scheduler.get_int", return_value=7), patch(
        "pecha_api.scheduler.scheduler"
    ) as mock_scheduler, patch(
        "pecha_api.scheduler.CronTrigger"
    ) as mock_cron_trigger:
        mock_scheduler.running = False
        mock_trigger = MagicMock()
        mock_cron_trigger.return_value = mock_trigger

        setup_scheduler()

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args
        assert call_kwargs.kwargs["args"] == [7]
        assert call_kwargs.kwargs["id"] == "cleanup_expired_verses_of_day"
        mock_scheduler.start.assert_called_once()


def test_shutdown_scheduler_when_running():
    with patch("pecha_api.scheduler.scheduler") as mock_scheduler:
        mock_scheduler.running = True

        shutdown_scheduler()

        mock_scheduler.shutdown.assert_called_once_with(wait=False)


def test_shutdown_scheduler_when_not_running():
    with patch("pecha_api.scheduler.scheduler") as mock_scheduler:
        mock_scheduler.running = False

        shutdown_scheduler()

        mock_scheduler.shutdown.assert_not_called()
