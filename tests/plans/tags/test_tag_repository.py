import uuid
from unittest.mock import MagicMock, patch

from pecha_api.plans.authors.plan_authors_model import Author  # noqa: F401
from pecha_api.plans.plans_models import Plan  # noqa: F401
from pecha_api.plans.tags.tag_model import Tag
from pecha_api.plans.tags.tag_repository import (
    get_tag_by_id,
    get_tag_by_name,
    get_tags_by_ids,
    get_tags_paginated,
    get_published_tags_for_language,
    save_tag,
    set_plan_tags,
    set_tag_plans,
    soft_delete_tag,
    update_tag_row,
)


def _mock_query_chain(return_value=None):
    chain = MagicMock()
    chain.options.return_value = chain
    chain.filter.return_value = chain
    chain.join.return_value = chain
    chain.distinct.return_value = chain
    chain.order_by.return_value = chain
    chain.offset.return_value = chain
    chain.limit.return_value = chain
    chain.first.return_value = return_value
    chain.all.return_value = return_value if isinstance(return_value, list) else []
    if isinstance(return_value, list):
        chain.count.return_value = len(return_value)
    else:
        chain.count.return_value = 0 if return_value is None else 1
    return chain


def test_get_tag_by_id_returns_row():
    db = MagicMock()
    tag = MagicMock(spec=Tag)
    db.query.return_value = _mock_query_chain(tag)

    result = get_tag_by_id(db=db, tag_id=uuid.uuid4())

    assert result is tag
    db.query.assert_called_with(Tag)


def test_get_tag_by_name_returns_row():
    db = MagicMock()
    tag = MagicMock(spec=Tag)
    db.query.return_value = _mock_query_chain(tag)

    result = get_tag_by_name(db=db, name="Meditation")

    assert result is tag


def test_get_tags_paginated_with_search():
    db = MagicMock()
    tag = MagicMock(spec=Tag)
    chain = _mock_query_chain([tag])
    chain.count.return_value = 1
    db.query.return_value = chain

    rows, total = get_tags_paginated(db=db, search="med", skip=0, limit=10)

    assert rows == [tag]
    assert total == 1


def test_save_tag_commits():
    db = MagicMock()
    tag = MagicMock(spec=Tag)

    result = save_tag(db=db, tag=tag)

    db.add.assert_called_once_with(tag)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(tag)
    assert result is tag


def test_update_tag_row_commits():
    db = MagicMock()
    tag = MagicMock(spec=Tag)

    result = update_tag_row(db=db, tag=tag)

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(tag)
    assert result is tag


def test_soft_delete_tag_sets_deleted_fields():
    db = MagicMock()
    tag = MagicMock(spec=Tag)

    soft_delete_tag(db=db, tag=tag, deleted_by="user@example.com")

    assert tag.deleted_by == "user@example.com"
    assert tag.deleted_at is not None
    db.commit.assert_called_once()


def test_get_tags_by_ids_empty_list():
    db = MagicMock()
    assert get_tags_by_ids(db=db, tag_ids=[]) == []
    db.query.assert_not_called()


def test_get_tags_by_ids_returns_matches():
    db = MagicMock()
    tag = MagicMock(spec=Tag)
    db.query.return_value = _mock_query_chain([tag])

    result = get_tags_by_ids(db=db, tag_ids=[uuid.uuid4()])

    assert result == [tag]


def test_set_tag_plans_empty_clears_association():
    db = MagicMock()
    tag = MagicMock(spec=Tag)
    tag.plans = [MagicMock()]

    result = set_tag_plans(db=db, tag=tag, plan_ids=[])

    assert tag.plans == []
    db.commit.assert_called_once()
    assert result is tag


def test_set_tag_plans_loads_active_plans():
    db = MagicMock()
    tag = MagicMock(spec=Tag)
    plan = MagicMock()
    plan.deleted_at = None
    db.query.return_value.filter.return_value.all.return_value = [plan]

    set_tag_plans(db=db, tag=tag, plan_ids=[uuid.uuid4()])

    assert tag.plans == [plan]


def test_set_plan_tags_none_is_noop():
    db = MagicMock()
    plan = MagicMock()

    result = set_plan_tags(db=db, plan=plan, tag_ids=None)

    assert result is plan
    db.commit.assert_not_called()


def test_set_plan_tags_assigns_tags():
    db = MagicMock()
    plan = MagicMock()
    tag = MagicMock(spec=Tag)
    tag_id = uuid.uuid4()

    with patch(
        "pecha_api.plans.tags.tag_repository.get_tags_by_ids",
        return_value=[tag],
    ):
        set_plan_tags(db=db, plan=plan, tag_ids=[tag_id])

    assert plan.tag_list == [tag]
    db.commit.assert_called_once()


def test_get_published_tags_for_language():
    db = MagicMock()
    tag = MagicMock(spec=Tag)
    db.query.return_value = _mock_query_chain([tag])

    result = get_published_tags_for_language(db=db, language="EN")

    assert result == [tag]
