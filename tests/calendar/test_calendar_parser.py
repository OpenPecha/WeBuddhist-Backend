from datetime import date
from pathlib import Path

import pytest

from pecha_api.calendar.calendar_parser import (
    CalendarType,
    MAX_CALENDAR_YEAR,
    MIN_CALENDAR_YEAR,
    find_calendar_day_for_gregorian_date,
    get_calendar_file_for_year,
    get_calendar_json_for_year,
    get_days_for_gregorian_month,
    load_calendar_year,
    parse_calendar_file,
    parse_calendar_year,
    to_tibetan_year,
)

SAMPLE_CALENDAR = """\
New Year: 2025, Wood-female-Snake

Tibetan Lunar Month: 1 - Earth-male-Dragon

1: Fri. mon gre. Earth-Water; 28 Feb 2025
  yongs 'joms, mi sdug pa, Tiger, kham 7
  6;52,56 22;45,42 22;44,38 18;30,21 10;1,51
  Solar: Earth-Dragon. Gui 8
2: Sat. mon gru. Earth-Earth; 1 Mar 2025
  zhi ba, byis pa, Rabbit, gin 8
  0;47,41 23;49,26 22;49,8 19;38,35 10;2,50
  Solar: Earth-Snake. Liu 9
17. Omitted: Horse kham 5
  omitted qualities line

Tibetan Lunar Month: 2 - Earth-female-Snake

1: Sat. mon gru. Earth-Earth; 1 Mar 2025
  zhi ba, byis pa, Rabbit, gin 8
"""


@pytest.fixture
def sample_calendar_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "2025.txt"
    file_path.write_text(SAMPLE_CALENDAR, encoding="utf-8")
    return file_path


class TestToTibetanYear:
    def test_converts_western_losar_year_to_traditional_tibetan_year(self):
        assert to_tibetan_year(2026) == 2153
        assert to_tibetan_year("2025") == 2152


class TestGetCalendarFileForYear:
    def test_returns_path_for_available_year(self):
        path = get_calendar_file_for_year(2025)
        assert path.name == "2025.txt"
        assert path.parent.name == "source_text"
        assert path.parent.parent.name == "Phugpa_calendar"
        assert path.is_file()

    def test_returns_tsurphu_path_when_selected(self):
        path = get_calendar_file_for_year(2025, CalendarType.TSURPHU)

        assert path.name == "2025.txt"
        assert path.parent.name == "source_text"
        assert path.parent.parent.name == "Tsurphu_calendar"
        assert path.is_file()

    def test_raises_for_year_out_of_range(self):
        with pytest.raises(FileNotFoundError, match="out of supported range"):
            get_calendar_file_for_year(MIN_CALENDAR_YEAR - 1)
        with pytest.raises(FileNotFoundError, match="out of supported range"):
            get_calendar_file_for_year(MAX_CALENDAR_YEAR + 1)

    def test_raises_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pecha_api.calendar.calendar_parser.PHUGPA_CALENDAR_DIR",
            tmp_path,
        )
        with pytest.raises(FileNotFoundError, match="No calendar file for year 2025"):
            get_calendar_file_for_year(2025)


class TestParseCalendarFile:
    def test_parses_gregorian_days_with_lunar_and_solar_details(self, sample_calendar_file):
        data = parse_calendar_file(str(sample_calendar_file))

        assert "2025-02-28" in data
        day = data["2025-02-28"]
        assert day["lunar_day"] == 1
        assert day["lunar_month"]["month"] == 1
        assert day["new_year"]["year"] == "2025"
        assert day["lunar_times"] is not None
        assert day["solar"]["designation"] == "Earth-Dragon"
        assert day["solar"]["number"] == "8"

    def test_parses_omitted_day_without_gregorian_date(self, sample_calendar_file):
        data = parse_calendar_file(str(sample_calendar_file))
        omitted_keys = [key for key in data if key.startswith("omitted_")]

        assert len(omitted_keys) == 1
        omitted_day = data[omitted_keys[0]]
        assert omitted_day["gregorian_date"] is None
        assert omitted_day["lunar_day"] == 17

    def test_parses_tsurphu_omitted_day_marker(self, tmp_path):
        file_path = tmp_path / "tsurphu.txt"
        file_path.write_text(
            "New Year: 2025, Wood-female-Snake\n"
            "Tibetan Lunar Month: 1 - Earth-male-Tiger\n"
            "1. Omitted.\n"
            "  6;56,50 23;39,37\n",
            encoding="utf-8",
        )

        data = parse_calendar_file(str(file_path))

        assert data["omitted_2025_M01_D01"]["gregorian_date"] is None


class TestParseCalendarYear:
    def test_loads_real_calendar_year(self):
        data = parse_calendar_year(2025)

        assert "2025-03-01" in data
        assert data["2025-03-01"]["lunar_month"]["month"] == 1

    def test_loads_real_tsurphu_calendar_year(self):
        data = parse_calendar_year(2025, CalendarType.TSURPHU)

        assert "2025-03-01" in data
        assert data["2025-03-01"]["lunar_month"]["designation"] == "Earth-male-Tiger"
        assert "omitted_2025_M01_D01" in data


class TestLoadCalendarYear:
    def test_loads_from_json_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pecha_api.calendar.calendar_parser.PHUGPA_CALENDAR_DIR",
            tmp_path,
        )
        json_path = tmp_path / "json" / "2025.json"
        json_path.parent.mkdir()
        json_path.write_text(
            '{"2025-03-01": {"gregorian_date": "2025-03-01", "lunar_day": 1}}',
            encoding="utf-8",
        )

        data = load_calendar_year(2025)

        assert data["2025-03-01"]["lunar_day"] == 1

    def test_falls_back_to_txt_when_json_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pecha_api.calendar.calendar_parser.PHUGPA_CALENDAR_DIR",
            tmp_path,
        )
        source_text_dir = tmp_path / "source_text"
        source_text_dir.mkdir()
        (source_text_dir / "2025.txt").write_text(SAMPLE_CALENDAR, encoding="utf-8")

        data = load_calendar_year(2025)

        assert "2025-02-28" in data

    def test_json_path_for_year(self):
        path = get_calendar_json_for_year(2025, CalendarType.TSURPHU)
        assert path.name == "2025.json"
        assert path.parent.name == "json"
        assert path.parent.parent.name == "Tsurphu_calendar"


class TestGetDaysForGregorianMonth:
    def test_returns_sorted_days_for_gregorian_month(self):
        days = get_days_for_gregorian_month(2025, 3)

        assert len(days) == 31
        assert days[0]["gregorian_date"] == "2025-03-01"
        assert days[-1]["gregorian_date"] == "2025-03-31"

    def test_spans_adjacent_tibetan_years(self):
        days = get_days_for_gregorian_month(2025, 1)

        assert len(days) == 31
        assert days[0]["lunar_month"]["month"] == 11


class TestFindCalendarDayForGregorianDate:
    def test_finds_day_using_date_object(self):
        result = find_calendar_day_for_gregorian_date(date(2025, 3, 15))

        assert result is not None
        tibetan_year, day_data = result
        assert tibetan_year == 2025
        assert day_data["gregorian_date"] == "2025-03-15"

    def test_finds_day_using_iso_string(self):
        result = find_calendar_day_for_gregorian_date("2025-03-15")

        assert result is not None
        tibetan_year, day_data = result
        assert tibetan_year == 2025
        assert day_data["gregorian_date"] == "2025-03-15"

    def test_returns_none_when_day_not_found(self):
        assert find_calendar_day_for_gregorian_date("1800-01-01") is None
