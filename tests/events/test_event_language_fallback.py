from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.events.event_service import (
    get_event_by_id_service,
    get_events_service,
    _event_to_dto,
)

MODULE = "pecha_api.events.event_service"


def _metadata(language, name):
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        description=None,
        language=language,
    )


def _event(metadata_entries):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        plan_id=None,
        accumulator_id=None,
        mantra_id=None,
        timer_id=None,
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        image_url=None,
        metadata_entries=metadata_entries,
        created_at=now,
        created_by="author@example.com",
        updated_at=None,
    )


# --------------------------- _event_to_dto fallback behaviour ---------------------------


def test_returns_selected_language_when_available():
    event = _event([_metadata("bo", "Tibetan"), _metadata("en", "English")])

    dto = _event_to_dto(event, language="bo", fallback=True)

    assert dto.metadata is not None
    assert dto.metadata.language == "bo"
    assert dto.metadata.name == "Tibetan"


def test_falls_back_to_english_when_selected_language_missing():
    event = _event([_metadata("en", "English")])

    dto = _event_to_dto(event, language="bo", fallback=True)

    assert dto.metadata is not None
    assert dto.metadata.language == "en"
    assert dto.metadata.name == "English"


def test_returns_null_metadata_when_neither_selected_nor_english_exists():
    event = _event([_metadata("fr", "French")])

    dto = _event_to_dto(event, language="bo", fallback=True)

    # Event is still returned; only the metadata is empty.
    assert dto.metadata is None
    assert dto.id == event.id


def test_event_not_excluded_when_no_metadata_at_all():
    event = _event([])

    dto = _event_to_dto(event, language="bo", fallback=True)

    assert dto.metadata is None
    assert dto.id == event.id


def test_no_fallback_returns_null_when_selected_language_missing():
    # CMS / strict path (fallback=False): English is not substituted.
    event = _event([_metadata("en", "English")])

    dto = _event_to_dto(event, language="bo", fallback=False)

    assert dto.metadata is None


# --------------------------- public services thread fallback=True ---------------------------


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_events")
def test_get_events_service_public_uses_fallback(mock_get_events, mock_session):
    mock_session.return_value.__enter__.return_value = MagicMock()
    event = _event([_metadata("en", "English")])
    mock_get_events.return_value = ([event], 1)

    response = get_events_service(language="bo", fallback=True)

    assert response.total == 1
    assert response.events[0].metadata.language == "en"


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_events")
def test_get_events_service_cms_default_no_fallback(mock_get_events, mock_session):
    mock_session.return_value.__enter__.return_value = MagicMock()
    event = _event([_metadata("en", "English")])
    mock_get_events.return_value = ([event], 1)

    # Default fallback=False (the CMS path leaves it unset).
    response = get_events_service(language="bo")

    assert response.total == 1
    assert response.events[0].metadata is None


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_event_by_id")
def test_get_event_by_id_service_uses_fallback(mock_get_by_id, mock_session):
    mock_session.return_value.__enter__.return_value = MagicMock()
    event = _event([_metadata("en", "English")])
    mock_get_by_id.return_value = event

    dto = get_event_by_id_service(event_id=event.id, language="bo")

    assert dto.metadata is not None
    assert dto.metadata.language == "en"
