import uuid
from unittest.mock import MagicMock, patch

from pecha_api.plans.users.plan_user_series_repository import (
    ensure_series_partner,
    soft_delete_series_partner,
)


def test_ensure_series_partner_reactivates_soft_deleted_row():
    series_id, group_id = uuid.uuid4(), uuid.uuid4()
    existing = MagicMock()
    existing.deleted_at = object()

    db = MagicMock()
    with patch(
        "pecha_api.plans.users.plan_user_series_repository.get_series_partner",
        return_value=existing,
    ):
        result = ensure_series_partner(db=db, series_id=series_id, group_id=group_id)

    assert result is existing
    assert existing.deleted_at is None
    db.add.assert_not_called()
    db.flush.assert_called_once()


def test_ensure_series_partner_returns_existing_active_row_untouched():
    db = MagicMock()
    existing = MagicMock()
    existing.deleted_at = None

    with patch(
        "pecha_api.plans.users.plan_user_series_repository.get_series_partner",
        return_value=existing,
    ):
        result = ensure_series_partner(db=db, series_id=uuid.uuid4(), group_id=uuid.uuid4())

    assert result is existing
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_ensure_series_partner_creates_when_absent():
    db = MagicMock()
    with patch(
        "pecha_api.plans.users.plan_user_series_repository.get_series_partner",
        return_value=None,
    ):
        result = ensure_series_partner(db=db, series_id=uuid.uuid4(), group_id=uuid.uuid4())

    db.add.assert_called_once_with(result)
    db.flush.assert_called_once()


def test_soft_delete_series_partner_sets_deleted_at():
    db = MagicMock()
    partner = MagicMock()
    partner.deleted_at = None
    db.query.return_value.filter.return_value.first.return_value = partner

    result = soft_delete_series_partner(db=db, series_id=uuid.uuid4(), group_id=uuid.uuid4())

    assert result is partner
    assert partner.deleted_at is not None
    db.flush.assert_called_once()


def test_soft_delete_series_partner_returns_none_when_absent():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = soft_delete_series_partner(db=db, series_id=uuid.uuid4(), group_id=uuid.uuid4())

    assert result is None
    db.flush.assert_not_called()
