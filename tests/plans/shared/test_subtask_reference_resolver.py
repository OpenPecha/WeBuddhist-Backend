import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from pecha_api.plans.plans_enums import ContentType, LanguageCode, REFERENCE_CONTENT_TYPES
from pecha_api.plans.shared.subtask_reference_resolver import (
    _pick_metadata,
    REFERENCE_ID_NOT_ALLOWED,
    REFERENCE_ID_REQUIRED,
    REFERENCE_NOT_FOUND,
    SubTaskReferenceDTO,
    resolve_subtask_references,
    validate_subtask_reference,
)

MODULE = "pecha_api.plans.shared.subtask_reference_resolver"


def _subtask(content_type, reference_id=None):
    return SimpleNamespace(content_type=content_type, reference_id=reference_id)


def _reference(reference_id, content_type, group_id):
    return SubTaskReferenceDTO(
        id=reference_id,
        content_type=content_type,
        title="Linked content",
        group_id=group_id,
    )


def test_reference_content_types_cover_the_four_linkable_entities():
    assert REFERENCE_CONTENT_TYPES == frozenset(
        {
            ContentType.GROUP_ACCUMULATION,
            ContentType.GROUP_COLLECTION,
            ContentType.EVENT,
            ContentType.POST,
        }
    )


def test_resolve_returns_none_per_subtask_when_nothing_references():
    subtasks = [_subtask(ContentType.TEXT), _subtask(ContentType.IMAGE)]

    assert resolve_subtask_references(subtasks=subtasks, db=MagicMock()) == [None, None]


def test_resolve_hydrates_reference_subtasks_index_aligned():
    group_id = uuid.uuid4()
    event_id = uuid.uuid4()
    post_id = uuid.uuid4()
    subtasks = [
        _subtask(ContentType.TEXT),
        _subtask(ContentType.EVENT, event_id),
        _subtask(ContentType.POST, post_id),
    ]

    loaders = {
        ContentType.EVENT: lambda db, ids, language: {
            event_id: _reference(event_id, ContentType.EVENT, group_id)
        },
        ContentType.POST: lambda db, ids, language: {
            post_id: _reference(post_id, ContentType.POST, group_id)
        },
    }

    with patch.dict(f"{MODULE}._LOADERS", loaders):
        resolved = resolve_subtask_references(subtasks=subtasks, db=MagicMock())

    assert resolved[0] is None
    assert resolved[1].id == event_id
    assert resolved[1].content_type == ContentType.EVENT
    assert resolved[2].id == post_id


def test_resolve_returns_none_for_a_reference_whose_target_is_gone():
    """A deleted target must not shift the other subtasks' positions."""
    missing_id = uuid.uuid4()
    subtasks = [_subtask(ContentType.GROUP_COLLECTION, missing_id), _subtask(ContentType.TEXT)]

    with patch.dict(
        f"{MODULE}._LOADERS",
        {ContentType.GROUP_COLLECTION: lambda db, ids, language: {}},
    ):
        resolved = resolve_subtask_references(subtasks=subtasks, db=MagicMock())

    assert resolved == [None, None]


def test_resolve_survives_a_failing_loader():
    reference_id = uuid.uuid4()

    def _boom(db, ids, language):
        raise RuntimeError("upstream down")

    with patch.dict(f"{MODULE}._LOADERS", {ContentType.EVENT: _boom}):
        resolved = resolve_subtask_references(
            subtasks=[_subtask(ContentType.EVENT, reference_id)], db=MagicMock()
        )

    assert resolved == [None]


def test_resolve_opens_its_own_session_when_none_is_passed():
    group_id = uuid.uuid4()
    reference_id = uuid.uuid4()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = MagicMock()

    loaders = {
        ContentType.EVENT: lambda db, ids, language: {
            reference_id: _reference(reference_id, ContentType.EVENT, group_id)
        }
    }

    with patch.dict(f"{MODULE}._LOADERS", loaders), patch(
        "pecha_api.db.database.SessionLocal", return_value=session_cm
    ) as mock_session:
        resolved = resolve_subtask_references(
            subtasks=[_subtask(ContentType.EVENT, reference_id)]
        )

    assert mock_session.call_count == 1
    assert resolved[0].id == reference_id


def test_resolve_without_references_never_opens_a_session():
    with patch("pecha_api.db.database.SessionLocal") as mock_session:
        resolved = resolve_subtask_references(subtasks=[_subtask(ContentType.TEXT)])

    assert mock_session.call_count == 0
    assert resolved == [None]


def test_validate_accepts_a_target_in_the_plans_group():
    group_id = uuid.uuid4()
    reference_id = uuid.uuid4()

    loaders = {
        ContentType.GROUP_ACCUMULATION: lambda db, ids, language: {
            reference_id: _reference(reference_id, ContentType.GROUP_ACCUMULATION, group_id)
        }
    }

    with patch.dict(f"{MODULE}._LOADERS", loaders):
        validate_subtask_reference(
            db=MagicMock(),
            content_type=ContentType.GROUP_ACCUMULATION,
            reference_id=reference_id,
            group_id=group_id,
        )


def test_validate_rejects_a_target_owned_by_another_group():
    reference_id = uuid.uuid4()
    other_group_id = uuid.uuid4()

    loaders = {
        ContentType.EVENT: lambda db, ids, language: {
            reference_id: _reference(reference_id, ContentType.EVENT, other_group_id)
        }
    }

    with patch.dict(f"{MODULE}._LOADERS", loaders):
        with pytest.raises(HTTPException) as exc:
            validate_subtask_reference(
                db=MagicMock(),
                content_type=ContentType.EVENT,
                reference_id=reference_id,
                group_id=uuid.uuid4(),
            )

    assert exc.value.status_code == 400
    assert exc.value.detail["message"] == REFERENCE_NOT_FOUND


def test_validate_rejects_a_missing_target():
    with patch.dict(f"{MODULE}._LOADERS", {ContentType.POST: lambda db, ids, language: {}}):
        with pytest.raises(HTTPException) as exc:
            validate_subtask_reference(
                db=MagicMock(),
                content_type=ContentType.POST,
                reference_id=uuid.uuid4(),
                group_id=uuid.uuid4(),
            )

    assert exc.value.detail["message"] == REFERENCE_NOT_FOUND


def test_validate_requires_a_reference_id_for_reference_types():
    with pytest.raises(HTTPException) as exc:
        validate_subtask_reference(
            db=MagicMock(),
            content_type="EVENT",
            reference_id=None,
            group_id=uuid.uuid4(),
        )

    assert exc.value.detail["message"] == REFERENCE_ID_REQUIRED


def test_validate_rejects_a_reference_id_on_a_plain_content_type():
    with pytest.raises(HTTPException) as exc:
        validate_subtask_reference(
            db=MagicMock(),
            content_type=ContentType.TEXT,
            reference_id=uuid.uuid4(),
            group_id=uuid.uuid4(),
        )

    assert exc.value.detail["message"] == REFERENCE_ID_NOT_ALLOWED


def test_validate_passes_through_a_plain_content_type_without_a_reference():
    validate_subtask_reference(
        db=MagicMock(),
        content_type="TEXT",
        reference_id=None,
        group_id=uuid.uuid4(),
    )


def test_pick_metadata_matches_a_language_code_enum():
    """Plans carry a LanguageCode enum, not a bare string."""
    english = SimpleNamespace(language=LanguageCode.EN, name="Losar")
    tibetan = SimpleNamespace(language=LanguageCode.BO, name="ལོ་གྲསྡྷ")

    assert _pick_metadata([tibetan, english], LanguageCode.EN) is english
    assert _pick_metadata([tibetan, english], "en") is english
    assert _pick_metadata([tibetan, english], LanguageCode.BO) is tibetan


def test_pick_metadata_falls_back_to_the_first_entry():
    first = SimpleNamespace(language=LanguageCode.BO, name="First")
    second = SimpleNamespace(language=LanguageCode.ZH, name="Second")

    assert _pick_metadata([first, second], LanguageCode.EN) is first
    assert _pick_metadata([first, second], None) is first
    assert _pick_metadata([], LanguageCode.EN) is None
