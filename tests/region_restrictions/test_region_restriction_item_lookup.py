import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_item_lookup import (
    _accumulator_display_title,
    _mantra_display_title,
    _pick_metadata_text,
    resolve_titles_for_rows,
    search_restriction_candidates,
)


def test_pick_metadata_text_prefers_english():
    entries = [
        SimpleNamespace(language="BO", title="བོད་"),
        SimpleNamespace(language="EN", title="English"),
        SimpleNamespace(language="ZH", title="中文"),
    ]
    assert _pick_metadata_text(entries) == "English"


def test_pick_metadata_text_falls_back_to_first_nonempty():
    entries = [
        SimpleNamespace(language="XX", title=""),
        SimpleNamespace(language="YY", title="Fallback"),
    ]
    assert _pick_metadata_text(entries) == "Fallback"
    assert _pick_metadata_text([]) is None


def test_mantra_display_title_uses_title_then_mantra_text():
    mantra = SimpleNamespace(
        metadata_entries=[SimpleNamespace(language="EN", title="Om", mantra=None)]
    )
    assert _mantra_display_title(mantra) == "Om"

    long_mantra = "x" * 100
    mantra_only = SimpleNamespace(
        metadata_entries=[
            SimpleNamespace(language="EN", title=None, mantra=long_mantra)
        ]
    )
    title = _mantra_display_title(mantra_only)
    assert title is not None
    assert title.startswith("xxx")
    assert title.endswith("…")
    assert len(title) <= 80


def test_accumulator_display_title_falls_back_to_mantra():
    mantra_id = uuid.uuid4()
    acc = SimpleNamespace(metadata_entries=[], mantra_id=mantra_id)
    mantra = SimpleNamespace(
        metadata_entries=[SimpleNamespace(language="EN", title="Mantra Name", mantra=None)]
    )
    assert _accumulator_display_title(acc, {mantra_id: mantra}) == "Mantra Name"
    assert _accumulator_display_title(acc, {}) is None


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

    assert titles == {str(plan_id): "Morning Practice"}


def test_resolve_titles_empty_ids():
    assert resolve_titles_for_rows(MagicMock(), item_type=RestrictedItemType.PLAN, item_ids=[]) == {}


def test_resolve_titles_for_series_group_mantra_group_accumulator_collection():
    series_id = uuid.uuid4()
    group_id = uuid.uuid4()
    mantra_id = uuid.uuid4()
    ga_id = uuid.uuid4()
    collection_id = uuid.uuid4()

    series = SimpleNamespace(
        id=series_id,
        metadata_entries=[SimpleNamespace(language="EN", title="Series A")],
    )
    group = SimpleNamespace(
        id=group_id,
        metadata_entries=[SimpleNamespace(language="EN", title="Group A")],
    )
    mantra = SimpleNamespace(
        id=mantra_id,
        metadata_entries=[SimpleNamespace(language="EN", title="Mantra A", mantra=None)],
    )
    ga = SimpleNamespace(id=ga_id, title=" Group Acc ")
    collection = SimpleNamespace(id=collection_id, name="My Collection")

    db = MagicMock()

    with patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup.selectinload",
        return_value=MagicMock(),
    ):
        # SERIES
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            series
        ]
        assert resolve_titles_for_rows(
            db, item_type=RestrictedItemType.SERIES, item_ids=[series_id]
        ) == {str(series_id): "Series A"}

        # GROUP
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            group
        ]
        assert resolve_titles_for_rows(
            db, item_type=RestrictedItemType.GROUP, item_ids=[group_id]
        ) == {str(group_id): "Group A"}

        # MANTRA
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            mantra
        ]
        assert resolve_titles_for_rows(
            db, item_type=RestrictedItemType.MANTRA, item_ids=[mantra_id]
        ) == {str(mantra_id): "Mantra A"}

    # GROUP_ACCUMULATOR
    db.query.return_value.filter.return_value.all.return_value = [ga]
    assert resolve_titles_for_rows(
        db, item_type=RestrictedItemType.GROUP_ACCUMULATOR, item_ids=[ga_id]
    ) == {str(ga_id): "Group Acc"}

    # RECITATION_COLLECTION
    db.query.return_value.filter.return_value.all.return_value = [collection]
    assert resolve_titles_for_rows(
        db, item_type=RestrictedItemType.RECITATION_COLLECTION, item_ids=[collection_id]
    ) == {str(collection_id): "My Collection"}


def test_resolve_titles_for_accumulator_uses_metadata():
    acc_id = uuid.uuid4()
    acc = SimpleNamespace(
        id=acc_id,
        mantra_id=None,
        metadata_entries=[SimpleNamespace(language="EN", name="Acc Name")],
    )
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.all.return_value = [acc]

    with patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup.selectinload",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup.get_mantras_by_ids",
        return_value={},
    ):
        titles = resolve_titles_for_rows(
            db, item_type=RestrictedItemType.ACCUMULATOR, item_ids=[acc_id]
        )

    assert titles == {str(acc_id): "Acc Name"}


def test_resolve_titles_for_recitation():
    text_id = uuid.uuid4()
    fake_response = SimpleNamespace(
        recitations=[SimpleNamespace(text_id=text_id, title="Heart Sutra")],
        total=1,
    )

    with patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup._get_ordered_recitations_response",
        return_value=fake_response,
    ):
        titles = resolve_titles_for_rows(
            MagicMock(),
            item_type=RestrictedItemType.RECITATION,
            item_ids=[text_id],
        )

    assert titles == {str(text_id): "Heart Sutra"}


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
    assert items[0].id == str(plan_id)
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
    assert items[0].id == str(text_id)
    assert items[0].title == "Heart Sutra"


def test_search_recitations_returns_empty_on_loader_failure():
    with patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup._get_ordered_recitations_response",
        side_effect=ValueError("boom"),
    ):
        items, total = search_restriction_candidates(
            MagicMock(),
            item_type=RestrictedItemType.RECITATION,
            search="heart",
            skip=0,
            limit=20,
        )

    assert items == []
    assert total == 0


def test_search_group_accumulators():
    ga_id = uuid.uuid4()
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.count.return_value = 1
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
        SimpleNamespace(id=ga_id, title="Group Acc")
    ]

    items, total = search_restriction_candidates(
        db,
        item_type=RestrictedItemType.GROUP_ACCUMULATOR,
        search="group",
        skip=0,
        limit=20,
    )

    assert total == 1
    assert items[0].id == str(ga_id)
    assert items[0].title == "Group Acc"


def test_search_recitation_collections():
    collection_id = uuid.uuid4()
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.count.return_value = 1
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
        SimpleNamespace(id=collection_id, name="Collection")
    ]

    items, total = search_restriction_candidates(
        db,
        item_type=RestrictedItemType.RECITATION_COLLECTION,
        search=None,
        skip=0,
        limit=20,
    )

    assert total == 1
    assert items[0].title == "Collection"


def test_search_series_groups_mantras_accumulators_with_selectinload_mocked():
    series_id = uuid.uuid4()
    group_id = uuid.uuid4()
    mantra_id = uuid.uuid4()
    acc_id = uuid.uuid4()

    series = SimpleNamespace(
        id=series_id,
        metadata_entries=[SimpleNamespace(language="EN", title="Series Search")],
    )
    group = SimpleNamespace(
        id=group_id,
        slug="group-a",
        metadata_entries=[SimpleNamespace(language="EN", title="Group Search")],
    )
    mantra = SimpleNamespace(
        id=mantra_id,
        metadata_entries=[
            SimpleNamespace(language="EN", title="Mantra Search", mantra=None)
        ],
    )
    acc = SimpleNamespace(
        id=acc_id,
        mantra_id=None,
        metadata_entries=[SimpleNamespace(language="EN", name="Acc Search")],
    )

    def _query_chain(rows):
        query = MagicMock()
        query.options.return_value = query
        query.filter.return_value = query
        query.count.return_value = len(rows)
        query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            rows
        )
        return query

    with patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup.selectinload",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup.get_mantras_by_ids",
        return_value={},
    ), patch(
        "pecha_api.region_restrictions.region_restriction_item_lookup.exists",
        return_value=MagicMock(),
    ):
        db = MagicMock()
        db.query.return_value = _query_chain([series])
        items, total = search_restriction_candidates(
            db, item_type=RestrictedItemType.SERIES, search="series", skip=0, limit=10
        )
        assert total == 1
        assert items[0].title == "Series Search"

        db.query.return_value = _query_chain([group])
        items, total = search_restriction_candidates(
            db, item_type=RestrictedItemType.GROUP, search="group", skip=0, limit=10
        )
        assert total == 1
        assert items[0].title == "Group Search"

        db.query.return_value = _query_chain([mantra])
        items, total = search_restriction_candidates(
            db, item_type=RestrictedItemType.MANTRA, search="mantra", skip=0, limit=10
        )
        assert total == 1
        assert items[0].title == "Mantra Search"

        db.query.return_value = _query_chain([acc])
        items, total = search_restriction_candidates(
            db,
            item_type=RestrictedItemType.ACCUMULATOR,
            search="acc",
            skip=0,
            limit=10,
        )
        assert total == 1
        assert items[0].title == "Acc Search"


def test_search_whitespace_search_treated_as_none_for_plans():
    plan_id = uuid.uuid4()
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.count.return_value = 1
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
        SimpleNamespace(id=plan_id, title="Any")
    ]

    items, total = search_restriction_candidates(
        db,
        item_type=RestrictedItemType.PLAN,
        search="   ",
        skip=0,
        limit=5,
    )

    assert total == 1
    assert items[0].id == str(plan_id)
