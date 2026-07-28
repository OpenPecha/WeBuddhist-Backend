from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette import status

from pecha_api.app import api
from pecha_api.events.event_response_models import (
    EventDTO,
    EventLinkInput,
    CreateEventRequest,
    UpdateEventRequest,
)
from pecha_api.events.event_service import (
    _links_to_dtos,
    create_event_service,
    update_event_service,
)

client = TestClient(api)


# --------------------------- EventLinkInput validation ---------------------------

def test_event_link_input_accepts_valid_http_and_https() -> None:
    http_link = EventLinkInput(type="web", url="http://example.com/info")
    https_link = EventLinkInput(type="google-meet", url="https://meet.google.com/abc")
    assert http_link.url == "http://example.com/info"
    assert https_link.display_order == 1  # default


def test_event_link_input_trims_type_and_url() -> None:
    link = EventLinkInput(type="  web  ", url="  https://example.com  ")
    assert link.type == "web"
    assert link.url == "https://example.com"


@pytest.mark.parametrize(
    "bad_url",
    ["ftp://example.com", "notaurl", "javascript:alert(1)", "http://", "https://", "mailto:a@b.com"],
)
def test_event_link_input_rejects_non_http_url(bad_url: str) -> None:
    with pytest.raises(ValidationError):
        EventLinkInput(type="web", url=bad_url)


@pytest.mark.parametrize("bad_type", ["", "   "])
def test_event_link_input_rejects_empty_type(bad_type: str) -> None:
    with pytest.raises(ValidationError):
        EventLinkInput(type=bad_type, url="https://example.com")


def test_event_link_input_rejects_oversized_fields() -> None:
    # type > 50, url > 2000, label > 255 must be rejected at validation, not at the DB
    with pytest.raises(ValidationError):
        EventLinkInput(type="x" * 51, url="https://example.com")
    with pytest.raises(ValidationError):
        EventLinkInput(type="web", url="https://example.com/" + "a" * 2000)
    with pytest.raises(ValidationError):
        EventLinkInput(type="web", url="https://example.com", label="y" * 256)


# --------------------------- request defaults ---------------------------

def test_create_event_request_defaults_links_to_empty_list() -> None:
    now = datetime.now(timezone.utc)
    request = CreateEventRequest(
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        metadata=[{"name": "Event", "language": "EN"}],
    )
    assert request.links == []


def test_update_event_request_defaults_links_to_none() -> None:
    request = UpdateEventRequest()
    assert request.links is None


# --------------------------- _links_to_dtos ordering ---------------------------

def _link(display_order: int, type_: str = "web") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        type=type_,
        url="https://example.com",
        label=None,
        display_order=display_order,
    )


def test_links_to_dtos_orders_by_display_order() -> None:
    links = [_link(3), _link(1), _link(2)]
    dtos = _links_to_dtos(links)
    assert [dto.display_order for dto in dtos] == [1, 2, 3]


def test_links_to_dtos_empty_returns_empty_list() -> None:
    assert _links_to_dtos([]) == []
    assert _links_to_dtos(None) == []


# --------------------------- EventDTO serialization ---------------------------

def test_event_dto_serializes_links_ordered() -> None:
    now = datetime.now(timezone.utc)
    event = EventDTO(
        id=uuid4(),
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        is_one_day=True,
        featured=False,
        metadata=[],
        links=_links_to_dtos([_link(2, "web"), _link(1, "google-meet")]),
        created_at=now,
        created_by="author@example.com",
    )
    dumped = event.model_dump()
    assert [link["type"] for link in dumped["links"]] == ["google-meet", "web"]
    # label is None -> excluded via ser_json_exclude_none
    assert "label" not in event.model_dump(exclude_none=True)["links"][0]


# --------------------------- endpoint 400 on bad link ---------------------------

def test_create_event_endpoint_rejects_bad_url() -> None:
    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/cms/events",
        headers={"Authorization": "Bearer token"},
        json={
            "group_id": str(uuid4()),
            "start_date": now,
            "end_date": now,
            "metadata": [{"name": "Event", "language": "EN"}],
            "links": [{"type": "web", "url": "ftp://bad.example.com"}],
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_event_endpoint_rejects_empty_type() -> None:
    now = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/cms/events",
        headers={"Authorization": "Bearer token"},
        json={
            "group_id": str(uuid4()),
            "start_date": now,
            "end_date": now,
            "metadata": [{"name": "Event", "language": "EN"}],
            "links": [{"type": "  ", "url": "https://ok.example.com"}],
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --------------------------- service passes links to repository ---------------------------

def _saved_event_stub() -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        plan_id=None,
        accumulator_id=None,
        mantra_id=None,
        timer_id=None,
        group_recitation_collection_id=None,
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        image_url=None,
        featured=False,
        metadata_entries=[],
        links=[],
        created_at=now,
        created_by="author@example.com",
        updated_at=None,
    )


def test_create_event_service_passes_links_to_save() -> None:
    now = datetime.now(timezone.utc)
    request = CreateEventRequest(
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        metadata=[{"name": "Event", "language": "EN"}],
        links=[{"type": "web", "url": "https://example.com"}],
    )
    author = SimpleNamespace(id=uuid4(), email="author@example.com")

    with patch(
        "pecha_api.events.event_service.validate_cms_author_details",
        return_value=author,
    ), patch(
        "pecha_api.events.event_service.require_can_create_content",
    ), patch(
        "pecha_api.events.event_service.save_event",
        return_value=_saved_event_stub(),
    ) as mock_save:
        create_event_service(token="token", request=request)

    # links are forwarded as the 4th positional arg
    _, args, kwargs = mock_save.mock_calls[0]
    forwarded_links = args[3] if len(args) > 3 else kwargs.get("link_entries")
    assert forwarded_links == request.links


def test_update_event_service_replaces_links() -> None:
    now = datetime.now(timezone.utc)
    request = UpdateEventRequest(
        links=[{"type": "google-meet", "url": "https://meet.google.com/abc"}],
    )
    author = SimpleNamespace(id=uuid4(), email="author@example.com")
    existing = _saved_event_stub()

    with patch(
        "pecha_api.events.event_service.validate_cms_author_details",
        return_value=author,
    ), patch(
        "pecha_api.events.event_service.get_event_by_id",
        return_value=existing,
    ), patch(
        "pecha_api.events.event_service._require_can_edit_event",
    ), patch(
        "pecha_api.events.event_service.update_event",
        return_value=existing,
    ) as mock_update:
        update_event_service(token="token", event_id=existing.id, request=request)

    _, _, kwargs = mock_update.mock_calls[0]
    assert kwargs["link_entries"] == request.links
