from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.poems.enums import PoemStatus
from pecha_api.poems.models import Poem
from pecha_api.poems.repository import (
    create_poem,
    get_poem_by_id,
    get_poems_list,
    soft_delete_poem,
    update_poem,
)
from pecha_api.poems.response_models import (
    CreatePoemRequest,
    PoemDTO,
    PoemsResponse,
    UpdatePoemRequest,
)
from pecha_api.poems.service import _build_poem_dto


def cms_list_poems_service(
    token: str,
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[PoemStatus] = None,
    chapter_name: Optional[str] = None,
    author_name: Optional[str] = None,
    language: Optional[LanguageCode] = None,
) -> PoemsResponse:
    """List poems for CMS (all statuses)."""
    validate_cms_author_details(token=token)

    with SessionLocal() as db:
        poems, total = get_poems_list(
            db=db,
            skip=skip,
            limit=limit,
            status=status_filter,
            chapter_name=chapter_name,
            author_name=author_name,
            language=language,
        )

        poem_dtos = [_build_poem_dto(poem) for poem in poems]

        return PoemsResponse(
            poems=poem_dtos,
            skip=skip,
            limit=limit,
            total=total,
        )


def cms_get_poem_detail_service(token: str, poem_id: UUID) -> PoemDTO:
    """Get a poem by ID for CMS."""
    validate_cms_author_details(token=token)

    with SessionLocal() as db:
        poem = get_poem_by_id(db=db, poem_id=poem_id)

        if poem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poem not found",
            )

        return _build_poem_dto(poem)


def cms_create_poem_service(token: str, request: CreatePoemRequest) -> PoemDTO:
    """Create a new poem."""
    author = validate_cms_author_details(token=token)

    published_at = None
    if request.status == PoemStatus.PUBLISHED:
        published_at = datetime.now(timezone.utc)

    poem = Poem(
        title=request.title,
        content=request.content,
        author_name=request.author_name,
        chapter_name=request.chapter_name,
        language=request.language,
        image_key=request.image_key,
        status=request.status,
        published_at=published_at,
        created_by=author.email,
    )

    with SessionLocal() as db:
        saved_poem = create_poem(db=db, poem=poem)
        return _build_poem_dto(saved_poem)


def cms_update_poem_service(
    token: str,
    poem_id: UUID,
    request: UpdatePoemRequest,
) -> PoemDTO:
    """Update an existing poem."""
    author = validate_cms_author_details(token=token)

    with SessionLocal() as db:
        poem = get_poem_by_id(db=db, poem_id=poem_id)

        if poem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poem not found",
            )

        if request.title is not None:
            poem.title = request.title
        if request.content is not None:
            poem.content = request.content
        if request.author_name is not None:
            poem.author_name = request.author_name
        if "chapter_name" in request.model_fields_set:
            poem.chapter_name = request.chapter_name
        if request.language is not None:
            poem.language = request.language
        if "image_key" in request.model_fields_set:
            poem.image_key = request.image_key
        if request.status is not None:
            old_status = poem.status
            poem.status = request.status
            if old_status != PoemStatus.PUBLISHED and request.status == PoemStatus.PUBLISHED:
                poem.published_at = datetime.now(timezone.utc)

        poem.updated_by = author.email

        updated_poem = update_poem(db=db, poem=poem)
        return _build_poem_dto(updated_poem)


def cms_delete_poem_service(token: str, poem_id: UUID) -> None:
    """Soft delete a poem."""
    author = validate_cms_author_details(token=token)

    with SessionLocal() as db:
        poem = get_poem_by_id(db=db, poem_id=poem_id)

        if poem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poem not found",
            )

        soft_delete_poem(db=db, poem=poem, deleted_by=author.email)
