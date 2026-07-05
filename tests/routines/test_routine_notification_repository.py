from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.routines.routine_notifications.routine_notification_repository import (
    _enum_value,
    _normalize_platform,
)
from pecha_api.routines.routines_enums import SessionType


def test_enum_value_from_session_type_enum():
    assert _enum_value(SessionType.SERIES) == "SERIES"
    assert _enum_value(SessionType.PLAN) == "PLAN"


def test_enum_value_from_stringified_enum_name():
    assert _enum_value("SessionType.SERIES") == "SERIES"
    assert _enum_value("SessionType.PLAN") == "PLAN"


def test_enum_value_from_plain_string():
    assert _enum_value("SERIES") == "SERIES"


def test_normalize_platform_from_push_platform_enum():
    assert _normalize_platform(PushPlatform.ANDROID) == "android"
    assert _normalize_platform(PushPlatform.IOS) == "ios"


def test_normalize_platform_from_stringified_enum_name():
    assert _normalize_platform("PushPlatform.ANDROID") == "android"
    assert _normalize_platform("pushplatform.android") == "android"


def test_normalize_platform_from_plain_string():
    assert _normalize_platform("ANDROID") == "android"
