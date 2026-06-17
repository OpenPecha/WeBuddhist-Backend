from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.mantra.mantra_repository import get_mantras_by_ids


class TestGetMantrasByIds:
    """Test cases for get_mantras_by_ids."""

    def test_get_mantras_by_ids_empty_list(self):
        """Empty input should short-circuit without querying."""
        db = MagicMock()

        result = get_mantras_by_ids(db, [])

        assert result == {}
        db.query.assert_not_called()

    def test_get_mantras_by_ids_returns_map(self):
        """Mantras are returned keyed by id."""
        db = MagicMock()
        mantra_id = uuid4()
        mantra = MagicMock()
        mantra.id = mantra_id

        query = db.query.return_value
        query.options.return_value = query
        query.filter.return_value = query
        query.all.return_value = [mantra]

        result = get_mantras_by_ids(db, [mantra_id])

        assert result == {mantra_id: mantra}
        query.filter.assert_called_once()
