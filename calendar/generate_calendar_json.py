"""Parse calendar .txt sources into ready-to-use .json files.

Run from the repo root:
    poetry run python calendar/generate_calendar_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a script without installing the package path quirks.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pecha_api.calendar.calendar_parser import (  # noqa: E402
    CalendarType,
    MAX_CALENDAR_YEAR,
    MIN_CALENDAR_YEAR,
    get_calendar_json_for_year,
    parse_calendar_year,
)


def _strip_raw_lines(year_data: dict) -> dict:
    for day_data in year_data.values():
        day_data.pop("raw_lines", None)
    return year_data


def generate_calendar_json(
    years: range | None = None,
    calendar_types: list[CalendarType] | None = None,
) -> None:
    years = years or range(MIN_CALENDAR_YEAR, MAX_CALENDAR_YEAR + 1)
    calendar_types = calendar_types or list(CalendarType)

    for calendar_type in calendar_types:
        for year in years:
            year_data = _strip_raw_lines(parse_calendar_year(year, calendar_type))
            json_path = get_calendar_json_for_year(year, calendar_type)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(year_data, f, ensure_ascii=False, separators=(",", ":"))
            print(f"Wrote {json_path.relative_to(REPO_ROOT)} ({len(year_data)} days)")


if __name__ == "__main__":
    generate_calendar_json()
    print("Done generating calendar JSON.")
