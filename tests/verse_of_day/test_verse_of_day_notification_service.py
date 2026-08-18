from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.verse_of_day.verse_of_day_notification_repository import VerseOfDayDeviceTargetRow
from pecha_api.verse_of_day.verse_of_day_notification_response_models import (
    VerseOfDayNotificationContentDTO,
    VerseOfDayNotificationUserTargetDTO,
    VerseOfDayPushDeviceTargetDTO,
)
from pecha_api.verse_of_day.verse_of_day_notification_service import (
    _build_user_targets,
    _local_time_matches,
    _resolve_notification_content,
    _resolve_zoneinfo,
    get_verse_of_day_notification_targets,
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


def test_resolve_notification_content_matches_language_regardless_of_stored_casing():
    # VerseMetadata.lang has no DB-level casing constraint; a verse stored with
    # uppercase/mixed-case keys must still match a lowercase user language and fallback.
    verse = _verse({"EN": "In English", "Bo": "In Tibetan"})

    assert _resolve_notification_content(verse, "BO").body == "In Tibetan"
    assert _resolve_notification_content(verse, "ZH").body == "In English"


def _row(*, user_id, device_token, platform="android", timezone_name="Asia/Kathmandu", language="EN"):
    return VerseOfDayDeviceTargetRow(
        user_id=user_id,
        device_token=device_token,
        platform=platform,
        timezone=timezone_name,
        language=language,
    )


class TestBuildUserTargets:
    def test_dedupes_devices_and_resolves_content_per_user(self):
        user_id = uuid4()
        row_android = _row(user_id=user_id, device_token="tok-android", platform="android")
        row_ios = _row(user_id=user_id, device_token="tok-ios", platform="ios")
        duplicate = _row(user_id=user_id, device_token="tok-android", platform="android")
        # 10:00 in Asia/Kathmandu (UTC+5:45) is 04:15 UTC.
        utc_now = datetime(2026, 6, 23, 4, 15, tzinfo=timezone.utc)
        verse = _verse({"en": "Verse text"})

        with patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service.get_verse_of_day_today",
            return_value=verse,
        ):
            targets = _build_user_targets(MagicMock(), [row_android, row_ios, duplicate], utc_now)

        assert len(targets) == 1
        assert targets[0].user_id == user_id
        assert targets[0].notification.body == "Verse text"
        assert {d.token for d in targets[0].push_devices} == {"tok-android", "tok-ios"}

    def test_skips_user_when_no_verse_for_their_local_date(self):
        user_id = uuid4()
        row = _row(user_id=user_id, device_token="tok-1")
        utc_now = datetime(2026, 6, 23, 4, 15, tzinfo=timezone.utc)

        with patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service.get_verse_of_day_today",
            return_value=None,
        ):
            targets = _build_user_targets(MagicMock(), [row], utc_now)

        assert targets == []

    def test_groups_users_by_their_own_local_date(self):
        # Two users in different timezones can be at 10:00 local simultaneously
        # while their local calendar dates differ.
        user_kathmandu = uuid4()
        user_honolulu = uuid4()
        row_kathmandu = _row(user_id=user_kathmandu, device_token="tok-1", timezone_name="Asia/Kathmandu")
        row_honolulu = _row(user_id=user_honolulu, device_token="tok-2", timezone_name="Pacific/Honolulu")
        utc_now = datetime(2026, 6, 23, 20, 0, tzinfo=timezone.utc)

        verses_by_date = {
            date(2026, 6, 24): _verse({"en": "Tomorrow's verse"}, verse_date=date(2026, 6, 24)),
            date(2026, 6, 23): _verse({"en": "Today's verse"}, verse_date=date(2026, 6, 23)),
        }

        def fake_get_verse_of_day_today(_db, local_date):
            return verses_by_date.get(local_date)

        with patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service.get_verse_of_day_today",
            side_effect=fake_get_verse_of_day_today,
        ):
            targets = _build_user_targets(MagicMock(), [row_kathmandu, row_honolulu], utc_now)

        bodies_by_user = {t.user_id: t.notification.body for t in targets}
        assert bodies_by_user[user_kathmandu] == "Tomorrow's verse"
        assert bodies_by_user[user_honolulu] == "Today's verse"


class TestGetVerseOfDayNotificationTargets:
    def test_returns_empty_response_when_no_devices_match_local_time(self):
        row = _row(user_id=uuid4(), device_token="tok-1")
        with patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service.SessionLocal"
        ) as mock_session_local, patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service.repo.get_active_device_targets",
            return_value=[row],
        ), patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service._local_time_matches",
            return_value=False,
        ):
            mock_session_local.return_value.__enter__.return_value = MagicMock()
            mock_session_local.return_value.__exit__.return_value = None

            response = get_verse_of_day_notification_targets()

        assert response.users == []

    def test_returns_matched_users_from_build_user_targets(self):
        row = _row(user_id=uuid4(), device_token="tok-1")
        fake_user_target = VerseOfDayNotificationUserTargetDTO(
            user_id=uuid4(),
            notification=VerseOfDayNotificationContentDTO(title="WebBuddhist", body="Verse text"),
            push_devices=[VerseOfDayPushDeviceTargetDTO(token="tok-1", platform="android")],
        )

        with patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service.SessionLocal"
        ) as mock_session_local, patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service.repo.get_active_device_targets",
            return_value=[row],
        ), patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service._local_time_matches",
            return_value=True,
        ), patch(
            "pecha_api.verse_of_day.verse_of_day_notification_service._build_user_targets",
            return_value=[fake_user_target],
        ):
            mock_session_local.return_value.__enter__.return_value = MagicMock()
            mock_session_local.return_value.__exit__.return_value = None

            response = get_verse_of_day_notification_targets()

        assert response.users == [fake_user_target]
