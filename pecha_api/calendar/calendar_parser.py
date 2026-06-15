from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional
import re

PHUGPA_CALENDAR_DIR = (
    Path(__file__).resolve().parent.parent.parent / "calendar" / "Phugpa_calendar"
)
MIN_CALENDAR_YEAR = 1800
MAX_CALENDAR_YEAR = 2049


def get_calendar_file_for_year(year: int) -> Path:
    if year < MIN_CALENDAR_YEAR or year > MAX_CALENDAR_YEAR:
        raise FileNotFoundError(
            f"Calendar year {year} is out of supported range "
            f"({MIN_CALENDAR_YEAR}-{MAX_CALENDAR_YEAR})"
        )
    file_path = PHUGPA_CALENDAR_DIR / f"{year}.txt"
    if not file_path.is_file():
        raise FileNotFoundError(f"No calendar file for year {year}: {file_path}")
    return file_path


@lru_cache(maxsize=32)
def parse_calendar_year(year: int) -> Dict[str, Dict[str, Any]]:
    return parse_calendar_file(str(get_calendar_file_for_year(year)))


def parse_calendar_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    data: Dict[str, Dict[str, Any]] = {}
    lunar_date = None
    lunar_month = None
    new_year = None

    re_new_year = re.compile(r"New Year:\s+(\d{4}),\s*(.+)")
    re_lunar_month = re.compile(r"Tibetan Lunar Month:\s+(\d+)\s*-\s*(.+)")
    re_day = re.compile(
        r"^(\d{1,2})(:|\. Omitted:)\s*(.*?);?\s*(\d{1,2}\s\w+\.\s+.+;)?\s*([0-9]{1,2} \w+ \d{4})?"
    )
    re_date = re.compile(r"([0-9]{1,2} [A-Za-z]{3,} \d{4})")
    re_solar = re.compile(r"^\s*Solar:\s+(.+)\.\s+([A-Za-z]+)\s*(\d+)?")
    re_lunar_props = re.compile(
        r"^\s*([^\d]+),\s*([^\d]+),\s*([^\d]+),\s*([^\d]+)\s+([^\d]+)"
    )
    re_hours = re.compile(r"^\s*([\d; ,]+)")

    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    current: Dict[str, Any] = {}
    for idx, line in enumerate(lines):
        line_strip = line.strip()

        ny = re_new_year.match(line_strip)
        if ny:
            new_year = {"year": ny.group(1), "designation": ny.group(2)}
            continue

        lm = re_lunar_month.match(line_strip)
        if lm:
            lunar_month = {"month": int(lm.group(1)), "designation": lm.group(2)}
            continue

        day_match = re_day.match(line_strip)
        if day_match:
            lunar_date = int(day_match.group(1))
            gdate_m = re_date.search(line)
            if gdate_m:
                gdate = gdate_m.group(1)
                try:
                    gregorian_key = datetime.strptime(gdate, "%d %b %Y").date().isoformat()
                except ValueError:
                    gregorian_key = gdate
            else:
                year_value = new_year["year"] if new_year else "unknown"
                month_value = lunar_month["month"] if lunar_month else 0
                gregorian_key = f"omitted_{year_value}_M{month_value:02d}_D{lunar_date:02d}"

            current = {
                "gregorian_date": gregorian_key if not gregorian_key.startswith("omitted_") else None,
                "lunar_day": lunar_date,
                "lunar_month": lunar_month.copy() if lunar_month else None,
                "new_year": new_year.copy() if new_year else None,
                "day_summary": line_strip,
                "raw_lines": [line_strip],
            }

            for add_idx in range(1, 6):
                if idx + add_idx >= len(lines):
                    break
                lnext = lines[idx + add_idx].strip()
                if not lnext:
                    continue
                if re_lunar_props.match(lnext):
                    current["lunar_qualities"] = lnext
                    current["raw_lines"].append(lnext)
                    continue
                if re_hours.match(lnext):
                    current["lunar_times"] = lnext
                    current["raw_lines"].append(lnext)
                    continue
                solar_m = re_solar.match(lnext)
                if solar_m:
                    current["solar"] = {
                        "designation": solar_m.group(1).strip(),
                        "zodiac": solar_m.group(2).strip(),
                        "number": solar_m.group(3).strip() if solar_m.group(3) else None,
                    }
                    current["raw_lines"].append(lnext)
                    continue
                if (
                    re_day.match(lnext)
                    or re_lunar_month.match(lnext)
                    or re_new_year.match(lnext)
                ):
                    break
                current["raw_lines"].append(lnext)
            data[gregorian_key] = current
    return data


def get_days_for_gregorian_month(
    gregorian_year: int,
    gregorian_month: int,
) -> list[Dict[str, Any]]:
    month_prefix = f"{gregorian_year}-{gregorian_month:02d}"
    days_by_date: Dict[str, Dict[str, Any]] = {}

    for tibetan_year in (gregorian_year - 1, gregorian_year, gregorian_year + 1):
        if tibetan_year < MIN_CALENDAR_YEAR or tibetan_year > MAX_CALENDAR_YEAR:
            continue
        try:
            year_data = parse_calendar_year(tibetan_year)
        except FileNotFoundError:
            continue
        for day_data in year_data.values():
            gregorian_date = day_data.get("gregorian_date")
            if gregorian_date and gregorian_date.startswith(month_prefix):
                days_by_date[gregorian_date] = day_data

    return [days_by_date[day_key] for day_key in sorted(days_by_date)]


def find_calendar_day_for_gregorian_date(
    gregorian_date: date | str,
) -> Optional[tuple[int, Dict[str, Any]]]:
    if isinstance(gregorian_date, str):
        gregorian_key = gregorian_date
        gregorian_year = int(gregorian_date[:4])
    else:
        gregorian_key = gregorian_date.isoformat()
        gregorian_year = gregorian_date.year

    for tibetan_year in (gregorian_year - 1, gregorian_year, gregorian_year + 1):
        if tibetan_year < MIN_CALENDAR_YEAR or tibetan_year > MAX_CALENDAR_YEAR:
            continue
        try:
            year_data = parse_calendar_year(tibetan_year)
        except FileNotFoundError:
            continue
        day_data = year_data.get(gregorian_key)
        if day_data is not None:
            return tibetan_year, day_data
    return None
