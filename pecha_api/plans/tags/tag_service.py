from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.tags.tag_helpers import generate_tag_image_url, tags_to_summary_dtos
from pecha_api.plans.tags.tag_model import Tag
from pecha_api.plans.tags.tag_repository import (
    get_tag_by_id,
    get_tag_by_name,
    get_tags_paginated,
    get_tags_by_ids,
    save_tag,
    set_tag_plans,
    soft_delete_tag,
    update_tag_row,
)
from pecha_api.plans.tags.tag_response_models import (
    CreateTagRequest,
    TagDTO,
    TagsListResponse,
    UpdateTagRequest,
)


def _active_plan_ids(tag: Tag) -> List[UUID]:
    if not tag.plans:
        return []
    return [p.id for p in tag.plans if p.deleted_at is None]


def _tag_to_dto(tag: Tag) -> TagDTO:
    return TagDTO(
        id=tag.id,
        name=tag.name,
        image=generate_tag_image_url(tag.image_key),
        image_key=tag.image_key,
        description=tag.description,
        plan_ids=_active_plan_ids(tag),
    )


def _validate_plan_ids(db, plan_ids: List[UUID]) -> None:
    if not plan_ids:
        return
    seen = set()
    for plan_id in plan_ids:
        if plan_id in seen:
            continue
        seen.add(plan_id)
        plan = get_plan_by_id(db=db, plan_id=plan_id)
        if plan is None or plan.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{plan_id}' does not exist",
            )


def create_new_tag(token: str, create_tag_request: CreateTagRequest) -> TagDTO:
    author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        existing = get_tag_by_name(db=db_session, name=create_tag_request.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{create_tag_request.name}' already exists",
            )

        plan_ids = create_tag_request.plan_ids or []
        _validate_plan_ids(db=db_session, plan_ids=plan_ids)

        tag = Tag(
            name=create_tag_request.name.strip(),
            image_key=create_tag_request.image_key,
            description=create_tag_request.description,
            updated_by=author.email,
        )
        try:
            tag = save_tag(db=db_session, tag=tag)
            if plan_ids:
                tag = set_tag_plans(db=db_session, tag=tag, plan_ids=plan_ids)
            tag = get_tag_by_id(db=db_session, tag_id=tag.id)
            return _tag_to_dto(tag)
        except IntegrityError:
            db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{create_tag_request.name}' already exists",
            )


def update_existing_tag(token: str, tag_id: UUID, update_tag_request: UpdateTagRequest) -> TagDTO:
    author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        tag = get_tag_by_id(db=db_session, tag_id=tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id '{tag_id}' not found",
            )

        if update_tag_request.name is not None:
            name = update_tag_request.name.strip()
            other = get_tag_by_name(db=db_session, name=name)
            if other and other.id != tag_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tag with name '{name}' already exists",
                )
            tag.name = name

        if update_tag_request.image_key is not None:
            tag.image_key = update_tag_request.image_key
        if update_tag_request.description is not None:
            tag.description = update_tag_request.description

        tag.updated_at = datetime.now(timezone.utc)
        tag.updated_by = author.email

        if update_tag_request.plan_ids is not None:
            _validate_plan_ids(db=db_session, plan_ids=update_tag_request.plan_ids)
            tag = set_tag_plans(db=db_session, tag=tag, plan_ids=update_tag_request.plan_ids)

        try:
            tag = update_tag_row(db=db_session, tag=tag)
            tag = get_tag_by_id(db=db_session, tag_id=tag.id)
            return _tag_to_dto(tag)
        except IntegrityError:
            db_session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag name must be unique",
            )


def delete_tag(token: str, tag_id: UUID) -> None:
    author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        tag = get_tag_by_id(db=db_session, tag_id=tag_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id '{tag_id}' not found",
            )
        soft_delete_tag(db=db_session, tag=tag, deleted_by=author.email)


def get_cms_tags_list(
    token: str,
    search: Optional[str],
    skip: int,
    limit: int,
) -> TagsListResponse:
    validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        rows, total = get_tags_paginated(
            db=db_session,
            search=search,
            skip=skip,
            limit=limit,
        )

    return TagsListResponse(
        tags=[_tag_to_dto(row) for row in rows],
        skip=skip,
        limit=limit,
        total=total,
    )


def get_cms_tag_detail(token: str, tag_id: UUID) -> TagDTO:
    validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        tag = get_tag_by_id(db=db_session, tag_id=tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id '{tag_id}' not found",
        )
    return _tag_to_dto(tag)


def validate_tag_ids(db, tag_ids: List[UUID]) -> None:
    if not tag_ids:
        return
    found = get_tags_by_ids(db=db, tag_ids=tag_ids)
    found_ids = {t.id for t in found}
    for tag_id in tag_ids:
        if tag_id not in found_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with id '{tag_id}' does not exist",
            )
