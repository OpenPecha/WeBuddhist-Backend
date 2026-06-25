from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime, timezone

from pecha_api.app import api
from pecha_api.bookmarks.bookmark_response_models import BookmarkDTO, BookmarksResponse
from pecha_api.bookmarks.bookmark_enums import BookmarkType

client = TestClient(api)


def test_create_bookmark_success():
    bookmark_id = uuid4()
    source_id = str(uuid4())
    now = datetime.now(timezone.utc)

    mock_bookmark = BookmarkDTO(
        id=bookmark_id,
        type=BookmarkType.PLAN,
        source_id=source_id,
        name="My Bookmark",
        created_at=now,
        updated_at=now
    )

    with patch("pecha_api.bookmarks.bookmark_views.create_bookmark_service") as mock_service:
        mock_service.return_value = mock_bookmark

        response = client.post(
            "/users/me/bookmarks",
            json={
                "type": "PLAN",
                "source_id": source_id,
                "name": "My Bookmark"
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(bookmark_id)
        assert data["type"] == "PLAN"
        assert data["source_id"] == source_id
        assert data["name"] == "My Bookmark"


def test_create_bookmark_verse_type():
    bookmark_id = uuid4()
    verse_locator = "segment-ref-abc-123"
    now = datetime.now(timezone.utc)

    mock_bookmark = BookmarkDTO(
        id=bookmark_id,
        type=BookmarkType.VERSE,
        source_id=verse_locator,
        name=None,
        created_at=now,
        updated_at=now
    )

    with patch("pecha_api.bookmarks.bookmark_views.create_bookmark_service") as mock_service:
        mock_service.return_value = mock_bookmark

        response = client.post(
            "/users/me/bookmarks",
            json={
                "type": "VERSE",
                "source_id": verse_locator
            },
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "VERSE"
        assert data["source_id"] == verse_locator
        assert data["name"] is None


def test_create_bookmark_invalid_uuid_for_non_verse_type():
    response = client.post(
        "/users/me/bookmarks",
        json={
            "type": "PLAN",
            "source_id": "not-a-uuid"
        },
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422


def test_create_bookmark_invalid_type():
    response = client.post(
        "/users/me/bookmarks",
        json={
            "type": "UNKNOWN",
            "source_id": str(uuid4())
        },
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422


def test_create_bookmark_blank_source_id_verse():
    response = client.post(
        "/users/me/bookmarks",
        json={
            "type": "VERSE",
            "source_id": "   "
        },
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422


def test_create_bookmark_unauthorized():
    response = client.post(
        "/users/me/bookmarks",
        json={
            "type": "PLAN",
            "source_id": str(uuid4())
        }
    )

    assert response.status_code == 403


def test_get_bookmarks_rejects_verse_filter():
    response = client.get(
        "/users/me/bookmarks?type=VERSE",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422


def test_get_bookmarks_success():
    bookmark1_id = uuid4()
    bookmark2_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_response = BookmarksResponse(
        bookmarks=[
            BookmarkDTO(
                id=bookmark1_id,
                type=BookmarkType.SERIES,
                source_id=str(uuid4()),
                name="Bookmark 1",
                created_at=now,
                updated_at=now
            ),
            BookmarkDTO(
                id=bookmark2_id,
                type=BookmarkType.VERSE,
                source_id="segment-ref-002",
                name=None,
                created_at=now,
                updated_at=now
            )
        ]
    )

    with patch("pecha_api.bookmarks.bookmark_views.get_bookmarks_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            "/users/me/bookmarks",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["bookmarks"]) == 2
        assert data["bookmarks"][0]["type"] == "SERIES"
        assert data["bookmarks"][1]["source_id"] == "segment-ref-002"
        assert data["bookmarks"][1]["name"] is None


def test_get_bookmarks_empty():
    mock_response = BookmarksResponse(bookmarks=[])

    with patch("pecha_api.bookmarks.bookmark_views.get_bookmarks_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            "/users/me/bookmarks",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        assert response.json()["bookmarks"] == []


def test_get_bookmarks_unauthorized():
    response = client.get("/users/me/bookmarks")

    assert response.status_code == 403


def test_delete_bookmark_success():
    bookmark_id = uuid4()

    with patch("pecha_api.bookmarks.bookmark_views.delete_bookmark_service") as mock_service:
        mock_service.return_value = None

        response = client.delete(
            f"/users/me/bookmarks/{bookmark_id}",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 204


def test_delete_bookmark_unauthorized():
    bookmark_id = uuid4()

    response = client.delete(f"/users/me/bookmarks/{bookmark_id}")

    assert response.status_code == 403


def test_delete_bookmark_invalid_uuid():
    response = client.delete(
        "/users/me/bookmarks/invalid-uuid",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422
