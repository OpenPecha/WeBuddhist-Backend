from datetime import date, datetime, timezone
from types import SimpleNamespace

from pecha_api.verse_of_day.verse_of_day_notification_service import (
    _local_time_matches,
    _resolve_notification_content,
    _resolve_zoneinfo,
)


def _verse(lang_to_text: dict, verse_date=date(2026, 6, 23)):
    metadata = [SimpleNamespace(lang=lang, verse=text) for lang, text in lang_to_text.items()]
    return SimpleNamespace(verse_metadata=metadata, image_urls=None, date=verse_date)


def test_resolve_zoneinfo_valid_iana_name():
    tz = _resolve_zoneinfo("Asia/Kathmandu")
    assert str(tz) == "Asia/Kathmandu"


def test_resolve_zoneinfo_none_defaults_to_utc():
    assert _resolve_zoneinfo(None) is timezone.utc


def test_resolve_zoneinfo_utc_string():
    assert _resolve_zoneinfo("UTC") is timezone.utc


def test_resolve_zoneinfo_invalid_name_falls_back_to_utc():
    assert _resolve_zoneinfo("Not/A_Real_Zone") is timezone.utc


def test_local_time_matches_at_exact_local_ten_am():
    # Asia/Kathmandu is UTC+5:45, so 10:00 local == 04:15 UTC.
    utc_now = datetime(2026, 6, 23, 4, 15, tzinfo=timezone.utc)
    assert _local_time_matches("Asia/Kathmandu", utc_now) is True


def test_local_time_matches_false_one_minute_off():
    utc_now = datetime(2026, 6, 23, 4, 16, tzinfo=timezone.utc)
    assert _local_time_matches("Asia/Kathmandu", utc_now) is False


def test_local_time_matches_defaults_to_utc_when_missing():
    utc_now = datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc)
    assert _local_time_matches(None, utc_now) is True


def test_local_time_matches_across_dst_boundary():
    # America/New_York is UTC-4 during DST (late June).
    utc_now = datetime(2026, 6, 23, 14, 0, tzinfo=timezone.utc)
    assert _local_time_matches("America/New_York", utc_now) is True


def test_resolve_notification_content_matches_user_language():
    verse = _verse({"en": "In English", "bo": "In Tibetan"})
    content = _resolve_notification_content(verse, "BO")
    assert content is not None
    assert content.body == "In Tibetan"


def test_resolve_notification_content_falls_back_to_english():
    verse = _verse({"en": "In English", "bo": "In Tibetan"})
    content = _resolve_notification_content(verse, "ZH")
    assert content is not None
    assert content.body == "In English"


def test_resolve_notification_content_defaults_to_english_when_no_language():
    verse = _verse({"en": "In English"})
    content = _resolve_notification_content(verse, None)
    assert content is not None
    assert content.body == "In English"


def test_resolve_notification_content_skips_when_no_verse():
    assert _resolve_notification_content(None, "EN") is None


def test_resolve_notification_content_skips_when_no_matching_or_fallback_language():
    verse = _verse({"bo": "In Tibetan"})
    assert _resolve_notification_content(verse, "ZH") is None
