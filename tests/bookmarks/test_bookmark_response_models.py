import pytest
from uuid import uuid4

from pydantic import ValidationError

from pecha_api.bookmarks.bookmark_enums import BookmarkType
from pecha_api.bookmarks.bookmark_response_models import CreateBookmarkRequest


def test_create_bookmark_request_normalizes_uuid_source_id():
    source_id = uuid4()

    request = CreateBookmarkRequest(
        type=BookmarkType.PLAN,
        source_id=str(source_id),
    )

    assert request.source_id == str(source_id)


def test_create_bookmark_request_rejects_invalid_uuid_for_uuid_backed_type():
    with pytest.raises(ValidationError):
        CreateBookmarkRequest(
            type=BookmarkType.PLAN,
            source_id="not-a-uuid",
        )


def test_create_bookmark_request_allows_non_uuid_for_verse_type():
    verse_locator = "segment-ref-abc-123"

    request = CreateBookmarkRequest(
        type=BookmarkType.VERSE,
        source_id=verse_locator,
    )

    assert request.source_id == verse_locator


def test_create_bookmark_request_allows_non_uuid_for_text_type():
    openpecha_text_id = "48q7hw4yg2R9PUS5J8CNH"

    request = CreateBookmarkRequest(
        type=BookmarkType.TEXT,
        source_id=openpecha_text_id,
    )

    assert request.source_id == openpecha_text_id


def test_create_bookmark_request_rejects_blank_source_id():
    with pytest.raises(ValidationError):
        CreateBookmarkRequest(
            type=BookmarkType.VERSE,
            source_id="   ",
        )
