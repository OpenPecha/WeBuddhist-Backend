import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status

from pecha_api.plans.tags.tag_response_models import CreateTagRequest, UpdateTagRequest
from pecha_api.plans.tags.tag_service import (
    create_new_tag,
    delete_tag,
    get_cms_tag_detail,
    get_cms_tags_list,
    update_existing_tag,
    validate_tag_ids,
)


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def _make_author(email="author@example.com"):
    author = MagicMock()
    author.email = email
    author.id = uuid.uuid4()
    return author


def _make_tag(
    name="Meditation",
    image_key=None,
    description=None,
    featured=False,
    plans=None,
):
    tag = MagicMock()
    tag.id = uuid.uuid4()
    tag.name = name
    tag.image_key = image_key
    tag.description = description
    tag.featured = featured
    tag.plans = plans or []
    return tag


def _make_plan(plan_id=None, deleted_at=None):
    plan = MagicMock()
    plan.id = plan_id or uuid.uuid4()
    plan.deleted_at = deleted_at
    return plan


def test_create_new_tag_success():
    author = _make_author()
    request = CreateTagRequest(
        name="  Meditation  ",
        image_key="images/tags/cover.jpg",
        description="Daily practice",
    )
    saved = _make_tag(name="Meditation", image_key=request.image_key, description=request.description)

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.save_tag",
        return_value=saved,
    ) as mock_save, patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=saved,
    ), patch(
        "pecha_api.plans.tags.tag_service.generate_tag_image_url",
        return_value="https://signed/cover.jpg",
    ):
        _session_local_context(mock_session)
        dto = create_new_tag(token="tok", create_tag_request=request)

    mock_save.assert_called_once()
    passed_tag = mock_save.call_args.kwargs["tag"]
    assert passed_tag.name == "Meditation"
    assert passed_tag.image_key == request.image_key
    assert passed_tag.updated_by == author.email
    assert dto.name == "Meditation"
    assert dto.image_key == request.image_key
    assert dto.image == "https://signed/cover.jpg"
    assert dto.plan_ids == []


def test_create_new_tag_with_plan_ids():
    author = _make_author()
    plan_id = uuid.uuid4()
    request = CreateTagRequest(name="Sleep", plan_ids=[plan_id])
    saved = _make_tag(name="Sleep")
    active_plan = _make_plan(plan_id=plan_id)
    saved_with_plans = _make_tag(name="Sleep", plans=[active_plan])

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_plan_by_id",
        return_value=active_plan,
    ), patch(
        "pecha_api.plans.tags.tag_service.save_tag",
        return_value=saved,
    ), patch(
        "pecha_api.plans.tags.tag_service.set_tag_plans",
        return_value=saved_with_plans,
    ) as mock_set_plans, patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=saved_with_plans,
    ):
        db = _session_local_context(mock_session)
        dto = create_new_tag(token="tok", create_tag_request=request)

    mock_set_plans.assert_called_once_with(db=db, tag=saved, plan_ids=[plan_id])
    assert dto.plan_ids == [plan_id]


def test_create_new_tag_sets_featured_value():
    author = _make_author()
    request = CreateTagRequest(name="Featured Tag", featured=True)
    saved = _make_tag(name="Featured Tag", featured=True)

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.save_tag",
        return_value=saved,
    ) as mock_save, patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=saved,
    ):
        _session_local_context(mock_session)
        dto = create_new_tag(token="tok", create_tag_request=request)

    passed_tag = mock_save.call_args.kwargs["tag"]
    assert passed_tag.featured is True
    assert dto.featured is True


def test_create_new_tag_duplicate_name_raises_400():
    existing = _make_tag(name="Meditation")
    request = CreateTagRequest(name="Meditation")

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=existing,
    ), patch("pecha_api.plans.tags.tag_service.save_tag") as mock_save:
        _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            create_new_tag(token="tok", create_tag_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    mock_save.assert_not_called()


def test_create_new_tag_deduplicates_duplicate_plan_ids_in_request():
    author = _make_author()
    plan_id = uuid.uuid4()
    request = CreateTagRequest(name="Tag", plan_ids=[plan_id, plan_id])
    saved = _make_tag(name="Tag")
    plan = _make_plan(plan_id=plan_id)

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_plan_by_id",
        return_value=plan,
    ) as mock_get_plan, patch(
        "pecha_api.plans.tags.tag_service.save_tag",
        return_value=saved,
    ), patch(
        "pecha_api.plans.tags.tag_service.set_tag_plans",
        return_value=saved,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=saved,
    ):
        _session_local_context(mock_session)
        create_new_tag(token="tok", create_tag_request=request)

    mock_get_plan.assert_called_once()


def test_create_new_tag_invalid_plan_id_raises_400():
    missing_id = uuid.uuid4()
    request = CreateTagRequest(name="New", plan_ids=[missing_id])

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_plan_by_id",
        return_value=None,
    ), patch("pecha_api.plans.tags.tag_service.save_tag") as mock_save:
        _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            create_new_tag(token="tok", create_tag_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    mock_save.assert_not_called()


def test_create_new_tag_deleted_plan_raises_400():
    plan_id = uuid.uuid4()
    deleted_plan = _make_plan(plan_id=plan_id, deleted_at=datetime.now(timezone.utc))
    request = CreateTagRequest(name="New", plan_ids=[plan_id])

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_plan_by_id",
        return_value=deleted_plan,
    ), patch("pecha_api.plans.tags.tag_service.save_tag") as mock_save:
        _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            create_new_tag(token="tok", create_tag_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    mock_save.assert_not_called()


def test_create_new_tag_integrity_error_raises_400():
    request = CreateTagRequest(name="Duplicate")

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.save_tag",
        side_effect=IntegrityError("insert", {}, Exception("unique")),
    ):
        mock_db = _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            create_new_tag(token="tok", create_tag_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    mock_db.rollback.assert_called_once()


def test_update_existing_tag_success():
    tag_id = uuid.uuid4()
    author = _make_author()
    existing = _make_tag(name="Old")
    refreshed = _make_tag(name="New Name", image_key="images/new.jpg", description="Updated")

    request = UpdateTagRequest(
        name="  New Name  ",
        image_key="images/new.jpg",
        description="Updated",
    )

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        side_effect=[existing, refreshed],
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.update_tag_row",
        return_value=existing,
    ) as mock_update_row:
        _session_local_context(mock_session)
        dto = update_existing_tag(token="tok", tag_id=tag_id, update_tag_request=request)

    mock_update_row.assert_called_once()
    assert existing.name == "New Name"
    assert existing.image_key == "images/new.jpg"
    assert existing.description == "Updated"
    assert existing.updated_by == author.email
    assert dto.name == "New Name"


def test_update_existing_tag_updates_featured():
    tag_id = uuid.uuid4()
    existing = _make_tag(featured=False)
    refreshed = _make_tag(featured=True)
    request = UpdateTagRequest(featured=True)

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        side_effect=[existing, refreshed],
    ), patch(
        "pecha_api.plans.tags.tag_service.update_tag_row",
        return_value=existing,
    ):
        _session_local_context(mock_session)
        dto = update_existing_tag(token="tok", tag_id=tag_id, update_tag_request=request)

    assert existing.featured is True
    assert dto.featured is True


def test_update_existing_tag_not_found():
    tag_id = uuid.uuid4()
    request = UpdateTagRequest(name="X")

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=None,
    ), patch("pecha_api.plans.tags.tag_service.update_tag_row") as mock_update:
        _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            update_existing_tag(token="tok", tag_id=tag_id, update_tag_request=request)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    mock_update.assert_not_called()


def test_update_existing_tag_duplicate_name_raises_400():
    tag_id = uuid.uuid4()
    other_id = uuid.uuid4()
    existing = _make_tag(name="Keep")
    other = _make_tag(name="Taken")
    other.id = other_id
    request = UpdateTagRequest(name="Taken")

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=existing,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=other,
    ), patch("pecha_api.plans.tags.tag_service.update_tag_row") as mock_update:
        _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            update_existing_tag(token="tok", tag_id=tag_id, update_tag_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    mock_update.assert_not_called()


def test_update_existing_tag_replaces_plan_ids():
    tag_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    existing = _make_tag()
    plan = _make_plan(plan_id=plan_id)
    refreshed = _make_tag(plans=[plan])
    request = UpdateTagRequest(plan_ids=[plan_id])

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        side_effect=[existing, refreshed],
    ), patch(
        "pecha_api.plans.tags.tag_service.get_plan_by_id",
        return_value=plan,
    ), patch(
        "pecha_api.plans.tags.tag_service.set_tag_plans",
        return_value=refreshed,
    ) as mock_set, patch(
        "pecha_api.plans.tags.tag_service.update_tag_row",
        return_value=existing,
    ):
        db = _session_local_context(mock_session)
        dto = update_existing_tag(token="tok", tag_id=tag_id, update_tag_request=request)

    mock_set.assert_called_once_with(db=db, tag=existing, plan_ids=[plan_id])
    assert dto.plan_ids == [plan_id]


def test_update_existing_tag_integrity_error_raises_400():
    tag_id = uuid.uuid4()
    existing = _make_tag()
    request = UpdateTagRequest(name="Conflict")

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=existing,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_name",
        return_value=None,
    ), patch(
        "pecha_api.plans.tags.tag_service.update_tag_row",
        side_effect=IntegrityError("update", {}, Exception("unique")),
    ):
        mock_db = _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            update_existing_tag(token="tok", tag_id=tag_id, update_tag_request=request)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    mock_db.rollback.assert_called_once()


def test_delete_tag_success():
    tag_id = uuid.uuid4()
    author = _make_author()
    existing = _make_tag()

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=existing,
    ), patch(
        "pecha_api.plans.tags.tag_service.soft_delete_tag",
    ) as mock_soft_delete:
        db = _session_local_context(mock_session)
        delete_tag(token="tok", tag_id=tag_id)

    mock_soft_delete.assert_called_once_with(db=db, tag=existing, deleted_by=author.email)


def test_delete_tag_not_found():
    tag_id = uuid.uuid4()

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=None,
    ), patch("pecha_api.plans.tags.tag_service.soft_delete_tag") as mock_soft_delete:
        _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            delete_tag(token="tok", tag_id=tag_id)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    mock_soft_delete.assert_not_called()


def test_get_cms_tags_list_success():
    row = _make_tag(name="Alpha")
    author = _make_author()

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tags_paginated",
        return_value=([row], 1),
    ) as mock_paginated:
        _session_local_context(mock_session)
        result = get_cms_tags_list(token="tok", search=None, skip=0, limit=10)

    mock_paginated.assert_called_once()
    assert result.total == 1
    assert result.skip == 0
    assert result.limit == 10
    assert len(result.tags) == 1
    assert result.tags[0].name == "Alpha"


def test_get_cms_tags_list_with_search():
    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tags_paginated",
        return_value=([], 0),
    ) as mock_paginated:
        _session_local_context(mock_session)
        get_cms_tags_list(token="tok", search="med", skip=2, limit=5)

    assert mock_paginated.call_args.kwargs["search"] == "med"
    assert mock_paginated.call_args.kwargs["skip"] == 2
    assert mock_paginated.call_args.kwargs["limit"] == 5


def test_get_cms_tag_detail_success():
    tag_id = uuid.uuid4()
    active = _make_plan()
    deleted = _make_plan(deleted_at=datetime.now(timezone.utc))
    tag = _make_tag(plans=[active, deleted])

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=tag,
    ):
        _session_local_context(mock_session)
        dto = get_cms_tag_detail(token="tok", tag_id=tag_id)

    assert dto.plan_ids == [active.id]


def test_get_cms_tag_detail_not_found():
    tag_id = uuid.uuid4()

    with patch("pecha_api.plans.tags.tag_service.SessionLocal") as mock_session, patch(
        "pecha_api.plans.tags.tag_service.validate_and_extract_author_details",
        return_value=_make_author(),
    ), patch(
        "pecha_api.plans.tags.tag_service.get_tag_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session)

        with pytest.raises(HTTPException) as exc:
            get_cms_tag_detail(token="tok", tag_id=tag_id)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_validate_tag_ids_no_op_for_empty():
    db = MagicMock()
    validate_tag_ids(db=db, tag_ids=[])
    db.query.assert_not_called()


def test_validate_tag_ids_success():
    tag_id = uuid.uuid4()
    found = _make_tag()
    found.id = tag_id

    with patch(
        "pecha_api.plans.tags.tag_service.get_tags_by_ids",
        return_value=[found],
    ):
        validate_tag_ids(db=MagicMock(), tag_ids=[tag_id])


def test_validate_tag_ids_missing_raises_400():
    missing = uuid.uuid4()

    with patch(
        "pecha_api.plans.tags.tag_service.get_tags_by_ids",
        return_value=[],
    ):
        with pytest.raises(HTTPException) as exc:
            validate_tag_ids(db=MagicMock(), tag_ids=[missing])

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
