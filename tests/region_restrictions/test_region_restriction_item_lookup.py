import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_item_lookup import (
    resolve_titles_for_rows,
    search_restriction_candidates,
)


def test_resolve_titles_for_plans():
    plan_id = uuid.uuid4()
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=plan_id, title="Morning Practice")
    ]

    titles = resolve_titles_for_rows(
        db,
        item_type=RestrictedItemType.PLAN,
        item_ids=[plan_id],
    )

    assert titles == {plan_id: "Morning Practice"}


def test_search_restriction_candidates_plans():
    plan_id = uuid.uuid4()
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.count.return_value = 1
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
        SimpleNamespace(id=plan_id, title="Morning Practice")
    ]

    items, total = search_restriction_candidates(
        db,
        item_type=RestrictedItemType.PLAN,
        search="morning",
        skip=0,
        limit=20,
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].id == plan_id
    assert items[0].title == "Morning Practice"


def test_search_recitations_uses_order_loader():
    text_id = uuid.uuid4()
    fake_response = SimpleNamespace(
        recitations=[SimpleNamespace(text_id=text_id, title="Heart Sutra")],
        total=1,
    )

    with patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup._get_ordered_recitations_response",
        return_value=fake_response,
    ):
        items, total = search_restriction_candidates(
            MagicMock(),
            item_type=RestrictedItemType.RECITATION,
            search="heart",
            skip=0,
            limit=20,
        )

    assert total == 1
    assert items[0].id == text_id
    assert items[0].title == "Heart Sutra"
