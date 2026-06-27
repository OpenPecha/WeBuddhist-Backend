import json
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid5

from pecha_api.traditions.tradition_constants import (
    DEFAULT_CHAT_LANGUAGE,
    TRADITION_ID_NAMESPACE,
    TRADITION_TAXONOMY_PATH,
)


def tradition_id_from_code(code: str) -> UUID:
    return uuid5(TRADITION_ID_NAMESPACE, code)


@lru_cache(maxsize=1)
def load_tradition_taxonomy() -> dict[str, Any]:
    with TRADITION_TAXONOMY_PATH.open(encoding="utf-8") as taxonomy_file:
        return json.load(taxonomy_file)


def get_tradition_entry(code: str) -> dict[str, Any] | None:
    for entry in load_tradition_taxonomy()["traditions"]:
        if entry["id"] == code:
            return entry
    return None


def get_tradition_display_name(entry: dict[str, Any], language: str = DEFAULT_CHAT_LANGUAGE) -> str:
    names = entry.get("names", {})
    language_entry = names.get(language) or names.get(DEFAULT_CHAT_LANGUAGE) or next(iter(names.values()), {})
    return language_entry.get("name", entry["id"])


def build_tradition_catalog(language: str = DEFAULT_CHAT_LANGUAGE) -> str:
    lines: list[str] = []
    for entry in load_tradition_taxonomy()["traditions"]:
        parent = entry.get("parent") or ""
        name = get_tradition_display_name(entry, language)
        lines.append(f'{entry["id"]}|{name}|{entry["level"]}|{parent}')
    return "\n".join(lines)


def list_tradition_codes() -> set[str]:
    return {entry["id"] for entry in load_tradition_taxonomy()["traditions"]}
