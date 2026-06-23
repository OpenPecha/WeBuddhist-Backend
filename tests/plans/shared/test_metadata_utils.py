from types import SimpleNamespace

from pecha_api.plans.shared.metadata_utils import filter_by_language_with_fallback


def _entry(language):
    return SimpleNamespace(language=language)


def _language_of(entry):
    return entry.language


def test_returns_all_entries_when_no_language():
    entries = [_entry("en"), _entry("bo")]
    assert filter_by_language_with_fallback(entries, None, _language_of) == entries


def test_returns_matching_language_entries():
    en, bo = _entry("en"), _entry("bo")
    result = filter_by_language_with_fallback([en, bo], "bo", _language_of)
    assert result == [bo]


def test_match_is_case_insensitive():
    bo = _entry("BO")
    result = filter_by_language_with_fallback([_entry("en"), bo], "bo", _language_of)
    assert result == [bo]


def test_falls_back_to_en_when_requested_language_missing():
    en = _entry("en")
    result = filter_by_language_with_fallback([en], "bo", _language_of)
    assert result == [en]


def test_returns_empty_when_neither_requested_nor_en_present():
    result = filter_by_language_with_fallback([_entry("zh")], "bo", _language_of)
    assert result == []


def test_empty_entries_returns_empty():
    assert filter_by_language_with_fallback([], "bo", _language_of) == []
