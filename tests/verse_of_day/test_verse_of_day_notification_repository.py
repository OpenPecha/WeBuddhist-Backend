from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.verse_of_day.verse_of_day_notification_repository import (
    _enum_value,
    _normalize_platform,
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
