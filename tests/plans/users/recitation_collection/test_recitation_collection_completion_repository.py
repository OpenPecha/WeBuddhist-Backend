from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from pecha_api.plans.users.recitation_collection.recitation_collection_completion_repository import (
    create_chant_completion,
)


class TestCreateChantCompletion:
    """Test cases for create_chant_completion tolerating a concurrent duplicate insert."""

    def test_create_chant_completion_commits(self):
        """A fresh completion is committed normally."""
        mock_db = MagicMock()

        create_chant_completion(
            db=mock_db,
            user_id=uuid4(),
            chant_id=uuid4(),
            collection_id=uuid4(),
            completion_date=date(2026, 6, 11),
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    def test_create_chant_completion_swallows_concurrent_duplicate(self):
        """A unique-constraint violation from a racing duplicate request is
        absorbed rather than propagating as a 500, preserving the documented
        idempotent response."""
        mock_db = MagicMock()
        mock_db.commit.side_effect = IntegrityError("stmt", {}, Exception("duplicate key"))

        create_chant_completion(
            db=mock_db,
            user_id=uuid4(),
            chant_id=uuid4(),
            collection_id=uuid4(),
            completion_date=date(2026, 6, 11),
        )

        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_called_once()
