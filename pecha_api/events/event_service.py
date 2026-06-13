from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.shared.metadata_utils import format_metadata_response
from pecha_api.plans.shared.permissions import (
    require_can_create_content,
    require_cms_write_access,
    require_group_member,
    is_super_admin,
)

from .event_model import Event
from .event_response_models import (
    CreateEventRequest,
    UpdateEventRequest,
    EventDTO,
    EventMetadataDTO,
    EventsResponse,
    _validate_date_range,
)
from .event_repository import (
    save_event,
    get_event_by_id,
    update_event,
    delete_event,
    get_events,
)

_CONTENT_EDIT_ROLES = {
    AuthorGroupMemberRole.OWNER,
    AuthorGroupMemberRole.ADMIN,
    AuthorGroupMemberRole.AUTHOR,
}


def _language_value(language) -> str:
    if hasattr(language, "value"):
        return language.value
    return str(language)


def _metadata_to_dtos(entries, language: Optional[str] = None) -> List[EventMetadataDTO]:
    if not entries:
        return []
    if language:
        language_upper = language.upper()
        entries = [
            entry for entry in entries
            if _language_value(entry.language).upper() == language_upper
        ]
    return sorted(
        [
            EventMetadataDTO(
                id=entry.id,
                name=entry.name,
                description=entry.description,
                language=_language_value(entry.language),
            )
            for entry in entries
        ],
        key=lambda metadata_dto: metadata_dto.language,
    )


def _metadata_response(entries, language: Optional[str] = None):
    return format_metadata_response(
        _metadata_to_dtos(entries, language=language),
        language=language,
    )


def _event_to_dto(event: Event, language: Optional[str] = None) -> EventDTO:
    return EventDTO(
        id=event.id,
        plan_id=event.plan_id,
        accumulator_id=event.accumulator_id,
        mantra_id=event.mantra_id,
        timer_id=event.timer_id,
        group_id=event.group_id,
        start_date=event.start_date,
        end_date=event.end_date,
        is_one_day=event.end_date == event.start_date,
        metadata=_metadata_response(event.metadata_entries, language=language),
        created_at=event.created_at,
        created_by=event.created_by,
        updated_at=event.updated_at,
    )


def _require_can_edit_event(db, group_id: UUID, author) -> None:
    require_cms_write_access(author)
    if is_super_admin(author):
        return
    require_group_member(
        db=db,
        group_id=group_id,
        author=author,
        allowed_roles=_CONTENT_EDIT_ROLES,
    )


def get_events_service(
    group_id: Optional[UUID] = None,
    plan_id: Optional[UUID] = None,
    accumulator_id: Optional[UUID] = None,
    mantra_id: Optional[UUID] = None,
    timer_id: Optional[UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> EventsResponse:
    with SessionLocal() as db:
        events, total = get_events(
            db,
            group_id=group_id,
            plan_id=plan_id,
            accumulator_id=accumulator_id,
            mantra_id=mantra_id,
            timer_id=timer_id,
            from_date=from_date,
            to_date=to_date,
            skip=skip,
            limit=limit,
        )
        return EventsResponse(
            events=[_event_to_dto(event, language=language) for event in events],
            total=total,
            skip=skip,
            limit=limit,
        )


def get_event_by_id_service(event_id: UUID, language: Optional[str] = None) -> EventDTO:
    with SessionLocal() as db:
        event = get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id '{event_id}' not found",
            )
        return _event_to_dto(event, language=language)


def create_event_service(token: str, request: CreateEventRequest) -> EventDTO:
    current_author = validate_cms_author_details(token=token)

    event = Event(
        plan_id=request.plan_id,
        accumulator_id=request.accumulator_id,
        mantra_id=request.mantra_id,
        timer_id=request.timer_id,
        group_id=request.group_id,
        start_date=request.start_date,
        end_date=request.end_date,
        created_by=current_author.email,
    )

    with SessionLocal() as db:
        require_can_create_content(
            db=db,
            group_id=request.group_id,
            author=current_author,
        )
        saved = save_event(db, event, request.metadata)
        return _event_to_dto(saved)


def update_event_service(token: str, event_id: UUID, request: UpdateEventRequest) -> EventDTO:
    current_author = validate_cms_author_details(token=token)

    with SessionLocal() as db:
        event = get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id '{event_id}' not found",
            )

        _require_can_edit_event(db, event.group_id, current_author)

        start_date = request.start_date if request.start_date is not None else event.start_date
        end_date = request.end_date if request.end_date is not None else event.end_date
        _validate_date_range(start_date, end_date)

        if request.group_id is not None:
            event.group_id = request.group_id
        if request.start_date is not None:
            event.start_date = request.start_date
        if request.end_date is not None:
            event.end_date = request.end_date
        if request.plan_id is not None:
            event.plan_id = request.plan_id
        if request.accumulator_id is not None:
            event.accumulator_id = request.accumulator_id
        if request.mantra_id is not None:
            event.mantra_id = request.mantra_id
        if request.timer_id is not None:
            event.timer_id = request.timer_id

        event.updated_at = datetime.now(timezone.utc)

        saved = update_event(db, event, metadata_entries=request.metadata)
        return _event_to_dto(saved)


def delete_event_service(token: str, event_id: UUID) -> None:
    current_author = validate_cms_author_details(token=token)

    with SessionLocal() as db:
        event = get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id '{event_id}' not found",
            )

        _require_can_edit_event(db, event.group_id, current_author)
        delete_event(db, event)
