from uuid import UUID
from typing import Optional

from pecha_api.db.database import SessionLocal
from pecha_api.bookmarks.bookmark_enums import BookmarkType
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.bookmarks.bookmark_models import Bookmark
from pecha_api.bookmarks.bookmark_repository import (
    save_bookmark,
    get_bookmarks_by_user_id,
    delete_bookmark
)
from pecha_api.bookmarks.bookmark_response_models import (
    CreateBookmarkRequest,
    BookmarksResponse,
    BookmarkDTO
)


async def create_bookmark_service(token: str, create_bookmark_request: CreateBookmarkRequest) -> BookmarkDTO:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        new_bookmark = Bookmark(
            user_id=current_user.id,
            type=create_bookmark_request.type,
            source_id=create_bookmark_request.source_id,
            name=create_bookmark_request.name
        )
        save_bookmark(db=db, bookmark=new_bookmark)

        return BookmarkDTO(
            id=new_bookmark.id,
            type=new_bookmark.type,
            source_id=new_bookmark.source_id,
            name=new_bookmark.name,
            created_at=new_bookmark.created_at,
            updated_at=new_bookmark.updated_at
        )


async def get_bookmarks_service(token: str, type: Optional[BookmarkType] = None) -> BookmarksResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        bookmarks = get_bookmarks_by_user_id(db=db, user_id=current_user.id, type=type)

        bookmarks_dto = [
            BookmarkDTO(
                id=bookmark.id,
                type=bookmark.type,
                source_id=bookmark.source_id,
                name=bookmark.name,
                created_at=bookmark.created_at,
                updated_at=bookmark.updated_at
            )
            for bookmark in bookmarks
        ]

        return BookmarksResponse(bookmarks=bookmarks_dto)


async def delete_bookmark_service(token: str, bookmark_id: UUID) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        delete_bookmark(db=db, user_id=current_user.id, bookmark_id=bookmark_id)
