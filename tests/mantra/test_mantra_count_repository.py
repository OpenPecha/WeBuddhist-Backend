from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.mantra.mantra_count_repository import (
    UserMantraCountRow,
    _user_mantra_counts_query,
    get_user_mantra_count_for_mantra,
    get_user_mantra_counts,
)


class TestUserMantraCountsQuery:
    def test_includes_soft_deleted_accumulators(self):
        db = MagicMock()
        user_id = uuid4()

        base = MagicMock()
        filtered = MagicMock()
        grouped = MagicMock()

        db.query.return_value = base
        base.filter.return_value = filtered
        filtered.group_by.return_value = grouped

        result = _user_mantra_counts_query(db, user_id)

        assert result is grouped
        filter_expr = base.filter.call_args[0][0]
        assert "deleted_at" not in str(filter_expr)


class TestUserMantraCountRow:
    def test_stores_fields(self):
        mantra_id = uuid4()
        updated_at = datetime.now(timezone.utc)
        row = UserMantraCountRow(
            mantra_id=mantra_id,
            total_count=108,
            updated_at=updated_at,
        )

        assert row.mantra_id == mantra_id
        assert row.total_count == 108
        assert row.updated_at == updated_at


class TestGetUserMantraCountsRepository:
    @patch("pecha_api.mantra.mantra_count_repository._user_mantra_counts_query")
    def test_get_user_mantra_counts_returns_rows_and_total(self, mock_counts_query):
        mantra_id = uuid4()
        updated_at = datetime.now(timezone.utc)
        db = MagicMock()

        grouped = MagicMock()
        mock_base_query = MagicMock()
        mock_base_query.subquery.return_value = grouped
        mock_counts_query.return_value = mock_base_query

        sum_query = MagicMock()
        sum_query.scalar.return_value = 800

        row = MagicMock()
        row.mantra_id = mantra_id
        row.total_count = 300
        row.updated_at = updated_at

        rows_query = MagicMock()
        rows_query.order_by.return_value = rows_query
        rows_query.offset.return_value = rows_query
        rows_query.limit.return_value = rows_query
        rows_query.all.return_value = [row]

        db.query.side_effect = [sum_query, rows_query]

        user_id = uuid4()
        rows, total = get_user_mantra_counts(db=db, user_id=user_id, skip=0, limit=20)

        assert total == 800
        assert len(rows) == 1
        assert rows[0].mantra_id == mantra_id
        assert rows[0].total_count == 300
        assert rows[0].updated_at == updated_at
        mock_counts_query.assert_called_once_with(db, user_id)

    @patch("pecha_api.mantra.mantra_count_repository._user_mantra_counts_query")
    def test_get_user_mantra_counts_handles_null_scalar_and_total_count(self, mock_counts_query):
        db = MagicMock()

        grouped = MagicMock()
        mock_base_query = MagicMock()
        mock_base_query.subquery.return_value = grouped
        mock_counts_query.return_value = mock_base_query

        sum_query = MagicMock()
        sum_query.scalar.return_value = None

        row = MagicMock()
        row.mantra_id = uuid4()
        row.total_count = None
        row.updated_at = None

        rows_query = MagicMock()
        rows_query.order_by.return_value = rows_query
        rows_query.offset.return_value = rows_query
        rows_query.limit.return_value = rows_query
        rows_query.all.return_value = [row]

        db.query.side_effect = [sum_query, rows_query]

        rows, total = get_user_mantra_counts(db=db, user_id=uuid4())

        assert total == 0
        assert rows[0].total_count == 0


class TestGetUserMantraCountForMantraRepository:
    @patch("pecha_api.mantra.mantra_count_repository._user_mantra_counts_query")
    def test_returns_count_and_updated_at(self, mock_counts_query):
        db = MagicMock()
        updated_at = datetime.now(timezone.utc)

        row = MagicMock()
        row.total_count = 500
        row.updated_at = updated_at

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = row
        mock_counts_query.return_value = query

        total_count, result_updated_at = get_user_mantra_count_for_mantra(
            db=db,
            user_id=uuid4(),
            mantra_id=uuid4(),
        )

        assert total_count == 500
        assert result_updated_at == updated_at

    @patch("pecha_api.mantra.mantra_count_repository._user_mantra_counts_query")
    def test_returns_zero_when_no_row(self, mock_counts_query):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = None
        mock_counts_query.return_value = query

        total_count, updated_at = get_user_mantra_count_for_mantra(
            db=db,
            user_id=uuid4(),
            mantra_id=uuid4(),
        )

        assert total_count == 0
        assert updated_at is None

    @patch("pecha_api.mantra.mantra_count_repository._user_mantra_counts_query")
    def test_returns_zero_when_total_count_is_null(self, mock_counts_query):
        db = MagicMock()
        row = MagicMock()
        row.total_count = None
        row.updated_at = None

        query = MagicMock()
        query.filter.return_value = query
        query.first.return_value = row
        mock_counts_query.return_value = query

        total_count, updated_at = get_user_mantra_count_for_mantra(
            db=db,
            user_id=uuid4(),
            mantra_id=uuid4(),
        )

        assert total_count == 0
        assert updated_at is None
