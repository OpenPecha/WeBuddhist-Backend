from typing import Callable, List, Optional, TypeVar, Union

T = TypeVar("T")

DEFAULT_FALLBACK_LANGUAGE = "en"


def format_metadata_response(
    metadata_list: List[T],
    language: Optional[str],
) -> Union[T, List[T], None]:
    if language:
        return metadata_list[0] if metadata_list else None
    return metadata_list


def filter_by_language_with_fallback(
    entries: List[T],
    language: Optional[str],
    language_of: Callable[[T], str],
    fallback_language: str = DEFAULT_FALLBACK_LANGUAGE,
) -> List[T]:
    """Keep entries matching ``language``; if none match, fall back to ``fallback_language``.

    When ``language`` is falsy, all entries are returned unchanged. ``language_of``
    extracts the (string) language code from an entry. Returns a (possibly empty)
    list; callers decide how to render an empty result.
    """
    if not language or not entries:
        return entries

    requested = language.upper()
    matched = [entry for entry in entries if language_of(entry).upper() == requested]
    if matched:
        return matched

    fallback = fallback_language.upper()
    if fallback != requested:
        fallback_matched = [
            entry for entry in entries if language_of(entry).upper() == fallback
        ]
        if fallback_matched:
            return fallback_matched

    return matched
