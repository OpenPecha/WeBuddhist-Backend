import json
from functools import lru_cache

from pecha_api.region_restrictions.region_restriction_constants import CHINESE_TIMEZONE_PATH


@lru_cache(maxsize=1)
def get_chinese_timezone_ids() -> frozenset[str]:
    with CHINESE_TIMEZONE_PATH.open(encoding="utf-8") as timezone_file:
        entries = json.load(timezone_file)
    return frozenset(entry["id"] for entry in entries if entry.get("id"))


def is_china_timezone(timezone_name: str | None) -> bool:
    if not timezone_name or not timezone_name.strip():
        return False
    return timezone_name.strip() in get_chinese_timezone_ids()
