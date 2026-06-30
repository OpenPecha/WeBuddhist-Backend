from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.routines.routine_notifications import routine_notification_service as service


def test_resolve_plan_notification_uses_day_copy_and_custom_image():
    plan_id = uuid4()
    user_id = uuid4()
    day_id = uuid4()
    utc_now = datetime.now(timezone.utc)

    plan = MagicMock(id=plan_id, title="My Plan", image_url="plans/cover.jpg")
    plan_item = MagicMock(id=day_id)
    day_notification = SimpleNamespace(
        title="Day 3 title",
        body="Day 3 body",
        image_type=SimpleNamespace(value=service.IMAGE_TYPE_CUSTOM),
        image_url="notifications/custom.jpg",
    )

    with patch.object(service.repo, "get_plan_by_id", return_value=plan), patch.object(
        service.repo, "get_user_plan_progress", return_value=MagicMock(started_at=utc_now)
    ), patch.object(service.repo, "get_plan_item_by_day_number", return_value=plan_item), patch.object(
        service.repo, "get_day_notification", return_value=day_notification
    ), patch.object(service, "_resolve_plan_image_url", return_value="https://example.com/plan.png"), patch.object(
        service, "_presign_s3_key", return_value="https://example.com/custom.png"
    ):
        content = service._resolve_plan_notification(
            MagicMock(),
            user_id=user_id,
            plan_id=plan_id,
            utc_now=utc_now,
        )

    assert content.title == "Day 3 title"
    assert content.body == "Day 3 body"
    assert content.image_url == "https://example.com/custom.png"


def test_resolve_plan_notification_falls_back_to_plan_defaults_without_day_notification():
    plan_id = uuid4()
    user_id = uuid4()
    utc_now = datetime.now(timezone.utc)

    plan = MagicMock(id=plan_id, title="My Plan", image_url="plans/cover.jpg")

    with patch.object(service.repo, "get_plan_by_id", return_value=plan), patch.object(
        service.repo, "get_user_plan_progress", return_value=None
    ), patch.object(service.repo, "get_plan_item_by_day_number", return_value=None    ), patch.object(
        service,
        "get",
        side_effect=lambda key: {
            "NOTIFICATION_DEFAULT_TITLE": "Default title",
            "NOTIFICATION_DEFAULT_BODY": "Default body",
        }[key],
    ), patch.object(service, "_resolve_plan_image_url", return_value="https://example.com/plan.png"):
        content = service._resolve_plan_notification(
            MagicMock(),
            user_id=user_id,
            plan_id=plan_id,
            utc_now=utc_now,
        )

    assert content.title == "My Plan"
    assert content.body == "Default body"
    assert content.image_url == "https://example.com/plan.png"


def test_resolve_plan_notification_uses_plan_image_when_day_image_type_is_plan():
    plan_id = uuid4()
    user_id = uuid4()
    day_id = uuid4()
    utc_now = datetime.now(timezone.utc)

    plan = MagicMock(id=plan_id, title="My Plan", image_url="plans/cover.jpg")
    plan_item = MagicMock(id=day_id)
    day_notification = SimpleNamespace(
        title="Day 1",
        body="Start here",
        image_type=SimpleNamespace(value=service.IMAGE_TYPE_PLAN),
        image_url=None,
    )

    with patch.object(service.repo, "get_plan_by_id", return_value=plan), patch.object(
        service.repo, "get_user_plan_progress", return_value=None
    ), patch.object(service.repo, "get_plan_item_by_day_number", return_value=plan_item), patch.object(
        service.repo, "get_day_notification", return_value=day_notification
    ), patch.object(service, "_resolve_plan_image_url", return_value="https://example.com/plan.png"):
        content = service._resolve_plan_notification(
            MagicMock(),
            user_id=user_id,
            plan_id=plan_id,
            utc_now=utc_now,
        )

    assert content.title == "Day 1"
    assert content.body == "Start here"
    assert content.image_url == "https://example.com/plan.png"


def test_resolve_series_notification_uses_series_defaults():
    series_id = uuid4()
    series = MagicMock(id=series_id, image="series/cover.jpg")
    metadata = MagicMock(title="Morning Series")

    with patch.object(service.repo, "get_series_by_id", return_value=series), patch.object(
        service.repo, "get_series_metadata", return_value=metadata
    ), patch.object(
        service,
        "get",
        side_effect=lambda key: {
            "NOTIFICATION_DEFAULT_TITLE": "Default title",
            "NOTIFICATION_DEFAULT_BODY": "Default body",
        }[key],
    ), patch.object(service, "_resolve_series_image_url", return_value="https://example.com/series.png"):
        content = service._resolve_series_notification(MagicMock(), series_id=series_id)

    assert content.title == "Morning Series"
    assert content.body == "Default body"
    assert content.image_url == "https://example.com/series.png"


def test_image_model_to_url_prefers_original():
    image = ImageUrlModel(
        thumbnail="https://example.com/thumb.jpg",
        medium="https://example.com/medium.jpg",
        original="https://example.com/original.jpg",
    )
    assert service._image_model_to_url(image) == "https://example.com/original.jpg"
