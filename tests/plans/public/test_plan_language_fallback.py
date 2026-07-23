"""Language fallback for published-plan queries.

Plans are stored per-language, so a requested language with no authored plans
(e.g. 'LA' for Ladakhi) must fall back to English rather than returning an
empty result. See ``plan_repository._with_language_fallback`` and
``plan_repository.resolve_plans_language``.
"""
from unittest.mock import MagicMock, patch

from pecha_api.plans.public.plan_repository import (
    DEFAULT_LANGUAGE,
    _with_language_fallback,
    resolve_plans_language,
)


class FakeQuery:
    """Records the languages filtered on and replays canned results."""

    def __init__(self, results_by_language, language=None, calls=None):
        self._results_by_language = results_by_language
        self._language = language
        self.calls = calls if calls is not None else []

    def filter(self, criterion):
        # criterion is ``Plan.language == <value>``; pull the bound value out.
        language = criterion.right.value
        self.calls.append(language)
        return FakeQuery(self._results_by_language, language, self.calls)

    def result(self):
        return self._results_by_language.get(self._language, [])


def _fetch(query):
    return query.result()


class TestWithLanguageFallback:
    def test_returns_requested_language_when_present(self):
        query = FakeQuery({"BO": ["bo-plan"], "EN": ["en-plan"]})

        assert _with_language_fallback(query, "bo", _fetch) == ["bo-plan"]
        assert query.calls == ["BO"]

    def test_falls_back_to_english_when_language_has_no_plans(self):
        query = FakeQuery({"EN": ["en-plan"], "ZH": []})

        assert _with_language_fallback(query, "zh", _fetch) == ["en-plan"]
        assert query.calls == ["ZH", "EN"]

    def test_language_outside_db_enum_queries_english_only(self):
        query = FakeQuery({"EN": ["en-plan"]})

        assert _with_language_fallback(query, "xx", _fetch) == ["en-plan"]
        assert query.calls == ["EN"]

    def test_supported_language_la_is_queried_before_english(self):
        query = FakeQuery({"LA": ["la-plan"], "EN": ["en-plan"]})

        assert _with_language_fallback(query, "la", _fetch) == ["la-plan"]
        assert query.calls == ["LA"]

    def test_language_is_upper_cased(self):
        query = FakeQuery({"BO": ["bo-plan"]})

        _with_language_fallback(query, "bo", _fetch)

        assert query.calls == ["BO"]

    def test_no_second_query_when_english_requested(self):
        query = FakeQuery({})

        assert _with_language_fallback(query, "en", _fetch) == []
        assert query.calls == ["EN"]

    def test_empty_result_when_neither_language_has_plans(self):
        query = FakeQuery({})

        assert _with_language_fallback(query, "zh", _fetch) == []
        assert query.calls == ["ZH", "EN"]

    def test_unfiltered_when_language_is_none(self):
        query = FakeQuery({None: ["any-plan"]})

        assert _with_language_fallback(query, None, _fetch) == ["any-plan"]
        assert query.calls == []


class TestResolvePlansLanguage:
    def _db_returning(self, has_plans):
        db = MagicMock()
        db.query.return_value.scalar.return_value = has_plans
        return db

    def test_keeps_requested_language_when_plans_exist(self):
        db = self._db_returning(True)

        assert resolve_plans_language(db=db, language="bo") == "BO"

    def test_falls_back_to_english_when_no_plans_exist(self):
        db = self._db_returning(False)

        assert resolve_plans_language(db=db, language="zh") == DEFAULT_LANGUAGE

    def test_language_outside_db_enum_skips_the_query(self):
        db = self._db_returning(False)

        assert resolve_plans_language(db=db, language="xx") == DEFAULT_LANGUAGE
        db.query.assert_not_called()

    def test_defaults_to_english_when_language_missing(self):
        db = self._db_returning(False)

        assert resolve_plans_language(db=db, language=None) == DEFAULT_LANGUAGE
        db.query.assert_not_called()

    def test_english_short_circuits_without_query(self):
        db = self._db_returning(False)

        assert resolve_plans_language(db=db, language="en") == DEFAULT_LANGUAGE
        db.query.assert_not_called()
