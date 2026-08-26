from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.verse_of_day.verse_of_day_notification_repository import (
    _enum_value,
    _normalize_platform,
    get_active_device_targets,
)


def test_enum_value_from_enum():
    assert _enum_value(LanguageCode.EN) == "EN"
    assert _enum_value(PushPlatform.ANDROID) == "ANDROID"


def test_enum_value_from_stringified_enum_name():
    assert _enum_value("LanguageCode.EN") == "EN"


def test_enum_value_from_plain_string():
    assert _enum_value("EN") == "EN"


def test_enum_value_from_none():
    assert _enum_value(None) is None


def test_normalize_platform_from_push_platform_enum():
    assert _normalize_platform(PushPlatform.ANDROID) == "android"
    assert _normalize_platform(PushPlatform.IOS) == "ios"


def test_normalize_platform_from_none():
    assert _normalize_platform(None) == ""


def test_get_active_device_targets_maps_rows_to_dataclass():
    user_id = uuid4()
    fake_row = SimpleNamespace(
        user_id=user_id,
        token="fcm-token",
        platform=PushPlatform.ANDROID,
        timezone="Asia/Kathmandu",
        language=LanguageCode.EN,
    )
    db = MagicMock()
    db.execute.return_value.all.return_value = [fake_row]

    targets = get_active_device_targets(db)

    assert len(targets) == 1
    target = targets[0]
    assert target.user_id == user_id
    assert target.device_token == "fcm-token"
    assert target.platform == "android"
    assert target.timezone == "Asia/Kathmandu"
    assert target.language == "EN"


def test_get_active_device_targets_returns_empty_list_when_no_rows():
    db = MagicMock()
    db.execute.return_value.all.return_value = []

    assert get_active_device_targets(db) == []


def test_get_active_device_targets_handles_missing_user_metadata():
    user_id = uuid4()
    fake_row = SimpleNamespace(
        user_id=user_id,
        token="fcm-token",
        platform=PushPlatform.IOS,
        timezone=None,
        language=None,
    )
    db = MagicMock()
    db.execute.return_value.all.return_value = [fake_row]

    targets = get_active_device_targets(db)

    assert targets[0].timezone is None
    assert targets[0].language is None
