from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, Optional
import re

PHUGPA_CALENDAR_DIR = Path(__file__).resolve().parent / "Phugpa_calendar"


def get_calendar_file_for_year(year: int) -> Path:
    """Return the Phugpa calendar file path for a given Tibetan calendar year."""
    file_path = PHUGPA_CALENDAR_DIR / f"{year}.txt"
    if not file_path.is_file():
        raise FileNotFoundError(f"No calendar file for year {year}: {file_path}")
    return file_path


def parse_calendar_year(year: int) -> Dict[str, Dict[str, Any]]:
    """Parse the Phugpa calendar file named after the given year."""
    return parse_calendar_file(str(get_calendar_file_for_year(year)))


def get_calendar_day(
    year: int, gregorian_date: date | str
) -> Optional[Dict[str, Any]]:
    """
    Load the calendar for `year` and return data for a single Gregorian date.

    Args:
        year: Tibetan calendar year (matches `{year}.txt` in Phugpa_calendar).
        gregorian_date: ISO date string (YYYY-MM-DD) or date object.
    """
    if isinstance(gregorian_date, str):
        gregorian_key = gregorian_date
    else:
        gregorian_key = gregorian_date.isoformat()
    return parse_calendar_year(year).get(gregorian_key)


def parse_calendar_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse a calendar file and return datewise data mapping each Gregorian date to lunar/solar details.

    Args:
        file_path (str): Path to the calendar text file.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping from "YYYY-MM-DD" (ISO) Gregorian date to details.
    """
    data = {}
    lunar_date = None
    lunar_month = None
    new_year = None

    # Patterns
    re_new_year = re.compile(r"New Year:\s+(\d{4}),\s*(.+)")
    re_lunar_month = re.compile(r"Tibetan Lunar Month:\s+(\d+)\s*-\s*(.+)")
    re_day = re.compile(r"^(\d{1,2})(:|\. Omitted:)\s*(.*?);?\s*(\d{1,2}\s\w+\.\s+.+;)?\s*([0-9]{1,2} \w+ \d{4})?")
    re_date = re.compile(r"([0-9]{1,2} [A-Za-z]{3,} \d{4})")
    re_solar = re.compile(r"^\s*Solar:\s+(.+)\.\s+([A-Za-z]+)\s*(\d+)?")
    re_lunar_props = re.compile(r"^\s*([^\d]+),\s*([^\d]+),\s*([^\d]+),\s*([^\d]+)\s+([^\d]+)")
    re_hours = re.compile(r"^\s*([\d; ,]+)")

    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    current = {}
    for idx, line in enumerate(lines):
        line_strip = line.strip()

        # New Year
        ny = re_new_year.match(line_strip)
        if ny:
            new_year = {"year": ny.group(1), "designation": ny.group(2)}
            continue

        # Lunar Month
        lm = re_lunar_month.match(line_strip)
        if lm:
            lunar_month = {"month": int(lm.group(1)), "designation": lm.group(2)}
            continue

        # Day entry
        day_match = re_day.match(line_strip)
        if day_match:
            # Line might be e.g. '1: Wed. mon gre. Water-Water; 18 Feb 2026'
            lunar_date = int(day_match.group(1))
            # Seek Gregorian date near end
            gdate_m = re_date.search(line)
            gdate = None
            if gdate_m:
                gdate = gdate_m.group(1)
                try:
                    gregorian_key = datetime.strptime(gdate, "%d %b %Y").date().isoformat()
                except ValueError:
                    gregorian_key = gdate
            else:
                year = new_year["year"] if new_year else "unknown"
                month = lunar_month["month"] if lunar_month else 0
                gregorian_key = f"omitted_{year}_M{month:02d}_D{lunar_date:02d}"

            # Compose base object
            current = {
                "lunar_day": lunar_date,
                "lunar_month": lunar_month.copy() if lunar_month else None,
                "new_year": new_year.copy() if new_year else None,
                "day_summary": line_strip,
                "raw_lines": [line_strip]
            }
            # We'll fill more info from next few lines
            # Look ahead for the next 3-4 lines
            for add_idx in range(1, 6):
                if idx + add_idx >= len(lines):
                    break
                lnext = lines[idx + add_idx].strip()
                if not lnext:
                    continue
                # Properties (like 'mchog can, gdab pa, Tiger, kham 7')
                prop_m = re_lunar_props.match(lnext)
                if prop_m:
                    current["lunar_qualities"] = lnext
                    current["raw_lines"].append(lnext)
                    continue
                # Numbers/hours line ('4;20,10 22;28,5 ...')
                hours_m = re_hours.match(lnext)
                if hours_m:
                    current["lunar_times"] = lnext
                    current["raw_lines"].append(lnext)
                    continue
                # Solar section
                solar_m = re_solar.match(lnext)
                if solar_m:
                    current["solar"] = {
                        "designation": solar_m.group(1).strip(),
                        "zodiac": solar_m.group(2).strip(),
                        "number": solar_m.group(3).strip() if solar_m.group(3) else None
                    }
                    current["raw_lines"].append(lnext)
                    continue
                # End of current day block if we run into next day or empty line
                if re_day.match(lnext) or re_lunar_month.match(lnext) or re_new_year.match(lnext):
                    break
                current["raw_lines"].append(lnext)
            data[gregorian_key] = current
    return data


def phugpa_calendar_day_for_date(date_str: str) -> None:
    """
    Print lunar day and solar info for a particular date (YYYY-MM-DD).
    The year will be deduced from the provided date string.
    """
    from datetime import datetime

    try:
        year = int(datetime.strptime(date_str, "%Y-%m-%d").year)
    except Exception as e:
        print(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")
        return

    data = get_calendar_day(year, date_str)
    return data
    