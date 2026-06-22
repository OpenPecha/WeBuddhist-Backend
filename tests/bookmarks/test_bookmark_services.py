import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from pecha_api.bookmarks.bookmark_services import (
    create_bookmark_service,
    get_bookmarks_service,
    delete_bookmark_service
)
from pecha_api.bookmarks.bookmark_response_models import CreateBookmarkRequest
from pecha_api.bookmarks.bookmark_enums import BookmarkType


@pytest.mark.asyncio
async def test_create_bookmark_service_success():
    user_id = uuid4()
    source_id = str(uuid4())
    bookmark_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_bookmark = MagicMock()
    mock_bookmark.id = bookmark_id
    mock_bookmark.user_id = user_id
    mock_bookmark.type = BookmarkType.PLAN
    mock_bookmark.source_id = source_id
    mock_bookmark.name = "Test Bookmark"
    mock_bookmark.created_at = now
    mock_bookmark.updated_at = now

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    request = CreateBookmarkRequest(
        type=BookmarkType.PLAN,
        source_id=source_id,
        name="Test Bookmark"
    )

    with patch("pecha_api.bookmarks.bookmark_services.validate_and_extract_user_details") as mock_validate, \
         patch("pecha_api.bookmarks.bookmark_services.SessionLocal") as mock_session, \
         patch("pecha_api.bookmarks.bookmark_services.save_bookmark") as mock_save, \
         patch("pecha_api.bookmarks.bookmark_services.Bookmark") as mock_bookmark_class:

        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db
        mock_bookmark_class.return_value = mock_bookmark

        result = await create_bookmark_service(token="test_token", create_bookmark_request=request)

        assert result.id == bookmark_id
        assert result.type == BookmarkType.PLAN
        assert result.source_id == source_id
        assert result.name == "Test Bookmark"
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_create_bookmark_service_verse_type():
    user_id = uuid4()
    verse_locator = "segment-ref-abc-123"
    bookmark_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_bookmark = MagicMock()
    mock_bookmark.id = bookmark_id
    mock_bookmark.user_id = user_id
    mock_bookmark.type = BookmarkType.VERSE
    mock_bookmark.source_id = verse_locator
    mock_bookmark.name = None
    mock_bookmark.created_at = now
    mock_bookmark.updated_at = now

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    request = CreateBookmarkRequest(
        type=BookmarkType.VERSE,
        source_id=verse_locator,
        name=None
    )

    with patch("pecha_api.bookmarks.bookmark_services.validate_and_extract_user_details") as mock_validate, \
         patch("pecha_api.bookmarks.bookmark_services.SessionLocal") as mock_session, \
         patch("pecha_api.bookmarks.bookmark_services.save_bookmark") as mock_save, \
         patch("pecha_api.bookmarks.bookmark_services.Bookmark") as mock_bookmark_class:

        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db
        mock_bookmark_class.return_value = mock_bookmark

        result = await create_bookmark_service(token="test_token", create_bookmark_request=request)

        assert result.type == BookmarkType.VERSE
        assert result.source_id == verse_locator
        assert result.name is None


@pytest.mark.asyncio
async def test_get_bookmarks_service_success():
    user_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_bookmark1 = MagicMock()
    mock_bookmark1.id = uuid4()
    mock_bookmark1.type = BookmarkType.SERIES
    mock_bookmark1.source_id = str(uuid4())
    mock_bookmark1.name = "Bookmark 1"
    mock_bookmark1.created_at = now
    mock_bookmark1.updated_at = now

    mock_bookmark2 = MagicMock()
    mock_bookmark2.id = uuid4()
    mock_bookmark2.type = BookmarkType.VERSE
    mock_bookmark2.source_id = "segment-ref-002"
    mock_bookmark2.name = None
    mock_bookmark2.created_at = now
    mock_bookmark2.updated_at = now

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.bookmarks.bookmark_services.validate_and_extract_user_details") as mock_validate, \
         patch("pecha_api.bookmarks.bookmark_services.SessionLocal") as mock_session, \
         patch("pecha_api.bookmarks.bookmark_services.get_bookmarks_by_user_id") as mock_get:

        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db
        mock_get.return_value = [mock_bookmark1, mock_bookmark2]

        result = await get_bookmarks_service(token="test_token")

        assert len(result.bookmarks) == 2
        assert result.bookmarks[0].type == BookmarkType.SERIES
        assert result.bookmarks[1].source_id == "segment-ref-002"
        assert result.bookmarks[1].name is None


@pytest.mark.asyncio
async def test_get_bookmarks_service_empty():
    user_id = uuid4()

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.bookmarks.bookmark_services.validate_and_extract_user_details") as mock_validate, \
         patch("pecha_api.bookmarks.bookmark_services.SessionLocal") as mock_session, \
         patch("pecha_api.bookmarks.bookmark_services.get_bookmarks_by_user_id") as mock_get:

        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db
        mock_get.return_value = []

        result = await get_bookmarks_service(token="test_token")

        assert len(result.bookmarks) == 0


@pytest.mark.asyncio
async def test_delete_bookmark_service_success():
    user_id = uuid4()
    bookmark_id = uuid4()

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.bookmarks.bookmark_services.validate_and_extract_user_details") as mock_validate, \
         patch("pecha_api.bookmarks.bookmark_services.SessionLocal") as mock_session, \
         patch("pecha_api.bookmarks.bookmark_services.delete_bookmark") as mock_delete:

        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db

        await delete_bookmark_service(token="test_token", bookmark_id=bookmark_id)

        mock_delete.assert_called_once_with(db=mock_db, user_id=user_id, bookmark_id=bookmark_id)
