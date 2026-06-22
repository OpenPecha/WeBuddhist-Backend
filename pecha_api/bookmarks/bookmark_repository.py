from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from starlette import status
from typing import List
from uuid import UUID

from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST, NOT_FOUND
from pecha_api.bookmarks.bookmark_models import Bookmark


def save_bookmark(db: Session, bookmark: Bookmark) -> None:
    try:
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error="CONFLICT",
                message="Bookmark already exists for this item"
            ).model_dump()
        )


def get_bookmarks_by_user_id(db: Session, user_id: UUID) -> List[Bookmark]:
    return db.query(Bookmark).filter(
        Bookmark.user_id == user_id
    ).order_by(Bookmark.created_at.desc()).all()


def delete_bookmark(db: Session, user_id: UUID, bookmark_id: UUID) -> None:
    try:
        bookmark = db.query(Bookmark).filter(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == user_id
        ).first()
        
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=NOT_FOUND,
                    message=f"Bookmark with ID {bookmark_id} not found for this user"
                ).model_dump()
            )
        
        db.delete(bookmark)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(
                error=BAD_REQUEST,
                message=f"Database integrity error: {str(e.orig)}"
            ).model_dump()
        )
