from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime, timezone

from pecha_api.app import api
from pecha_api.bookmarks.bookmark_response_models import BookmarkDTO, BookmarksResponse, BookmarkExistsResponse
from pecha_api.bookmarks.bookmark_enums import BookmarkType, BookmarkFilterType

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
        assert "name" not in data


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
        ],
        total=2,
        skip=0,
        limit=20,
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
        assert "name" not in data["bookmarks"][1]


def test_get_bookmarks_passes_pagination_and_language_to_service():
    mock_response = BookmarksResponse(bookmarks=[], total=0, skip=10, limit=5)

    with patch("pecha_api.bookmarks.bookmark_views.get_bookmarks_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            "/users/me/bookmarks?type=PLAN&language=bo&skip=10&limit=5",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            token="test_token",
            type=BookmarkFilterType.PLAN,
            language="bo",
            skip=10,
            limit=5,
        )


def test_get_bookmarks_empty():
    mock_response = BookmarksResponse(bookmarks=[], total=0, skip=0, limit=20)

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


def test_bookmark_exists_true():
    bookmark_id = uuid4()
    source_id = str(uuid4())

    mock_response = BookmarkExistsResponse(exists=True, id=bookmark_id)

    with patch("pecha_api.bookmarks.bookmark_views.bookmark_exists_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            f"/users/me/bookmarks/exists?type=PLAN&source_id={source_id}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["id"] == str(bookmark_id)
        mock_service.assert_called_once()
        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs["token"] == "test_token"
        assert call_kwargs["bookmark_exists_query"].type == BookmarkType.PLAN
        assert call_kwargs["bookmark_exists_query"].source_id == source_id


def test_bookmark_exists_false():
    mock_response = BookmarkExistsResponse(exists=False)

    with patch("pecha_api.bookmarks.bookmark_views.bookmark_exists_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            f"/users/me/bookmarks/exists?type=SERIES&source_id={uuid4()}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert "id" not in data


def test_bookmark_exists_verse_type():
    verse_locator = "segment-ref-abc-123"
    bookmark_id = uuid4()

    mock_response = BookmarkExistsResponse(exists=True, id=bookmark_id)

    with patch("pecha_api.bookmarks.bookmark_views.bookmark_exists_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            f"/users/me/bookmarks/exists?type=VERSE&source_id={verse_locator}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        mock_service.assert_called_once()
        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs["token"] == "test_token"
        assert call_kwargs["bookmark_exists_query"].type == BookmarkType.VERSE
        assert call_kwargs["bookmark_exists_query"].source_id == verse_locator


def test_bookmark_exists_without_type():
    source_id = str(uuid4())
    bookmark_id = uuid4()

    mock_response = BookmarkExistsResponse(exists=True, id=bookmark_id)

    with patch("pecha_api.bookmarks.bookmark_views.bookmark_exists_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            f"/users/me/bookmarks/exists?source_id={source_id}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        mock_service.assert_called_once()
        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs["bookmark_exists_query"].type is None
        assert call_kwargs["bookmark_exists_query"].source_id == source_id


def test_bookmark_exists_without_type_allows_non_uuid_source_id():
    verse_locator = "segment-ref-abc-123"

    mock_response = BookmarkExistsResponse(exists=False)

    with patch("pecha_api.bookmarks.bookmark_views.bookmark_exists_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            f"/users/me/bookmarks/exists?source_id={verse_locator}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs["bookmark_exists_query"].type is None
        assert call_kwargs["bookmark_exists_query"].source_id == verse_locator


def test_bookmark_exists_invalid_uuid():
    response = client.get(
        "/users/me/bookmarks/exists?type=PLAN&source_id=not-a-uuid",
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 422


def test_bookmark_exists_text_type_allows_non_uuid_source_id():
    openpecha_text_id = "48q7hw4yg2R9PUS5J8CNH"
    mock_response = BookmarkExistsResponse(exists=False)

    with patch("pecha_api.bookmarks.bookmark_views.bookmark_exists_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            f"/users/me/bookmarks/exists?type=TEXT&source_id={openpecha_text_id}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs["bookmark_exists_query"].type == BookmarkType.TEXT
        assert call_kwargs["bookmark_exists_query"].source_id == openpecha_text_id


def test_bookmark_exists_unauthorized():
    response = client.get(
        f"/users/me/bookmarks/exists?type=PLAN&source_id={uuid4()}",
    )

    assert response.status_code == 403
