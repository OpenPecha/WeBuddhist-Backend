from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.timezone_utils import get_day_bounds_in_timezone
from pecha_api.plans.authors.plan_authors_service import (
    safe_get_image_url,
    validate_cms_author_details,
)
from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.groups.groups_repository import get_author_group_ids
from pecha_api.group_recitation_collection.repository import get_collection_by_id
from pecha_api.plans.shared.metadata_utils import (
    filter_by_language_with_fallback,
    format_metadata_response,
)
from pecha_api.plans.shared.permissions import (
    require_can_create_content,
    require_can_read_group_content,
    require_cms_write_access,
    require_group_member,
    require_can_change_status,
    is_reviewer,
    is_super_admin,
)
from pecha_api.users.users_service import validate_and_extract_user_details

from .event_model import Event
from .event_response_models import (
    CreateEventRequest,
    UpdateEventRequest,
    EventDTO,
    EventMetadataDTO,
    EventLinkDTO,
    EventsResponse,
    _validate_date_range,
)
from .event_repository import (
    save_event,
    get_event_by_id,
    update_event,
    delete_event,
    get_events,
    get_featured_events,
)
from .event_participant_repository import (
    get_event_participant_count,
    get_event_participant_counts,
    get_joined_event_ids_by_user,
    is_user_joined_event,
)
from .location_repository import get_location_without_group_filter
from .location_response_models import LocationDTO

_CONTENT_EDIT_ROLES = {
    AuthorGroupMemberRole.OWNER,
    AuthorGroupMemberRole.ADMIN,
    AuthorGroupMemberRole.AUTHOR,
}


def _language_value(language) -> str:
    if hasattr(language, "value"):
        return language.value
    return str(language)


def _metadata_to_dtos(
    entries, language: Optional[str] = None, fallback: bool = False
) -> List[EventMetadataDTO]:
    if not entries:
        return []
    if fallback:
        entries = filter_by_language_with_fallback(
            entries=list(entries),
            language=language,
            language_of=lambda entry: _language_value(entry.language),
        )
    elif language:
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


def _metadata_response(entries, language: Optional[str] = None, fallback: bool = False):
    return format_metadata_response(
        _metadata_to_dtos(entries, language=language, fallback=fallback),
        language=language,
    )


def _links_to_dtos(links: Optional[List]) -> List[EventLinkDTO]:
    if not links:
        return []
    return [
        EventLinkDTO(
            id=link.id,
            type=link.type,
            url=link.url,
            label=link.label,
            display_order=link.display_order,
        )
        for link in sorted(links, key=lambda link: link.display_order)
    ]


def _location_to_dto(event: Event) -> Optional[LocationDTO]:
    location = event.location
    if location is None:
        return None
    return LocationDTO(
        id=location.id,
        group_id=location.group_id,
        name=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
    )


def _event_to_dto(
    event: Event,
    language: Optional[str] = None,
    fallback: bool = False,
    participant_count: int = 0,
    is_joined: Optional[bool] = None,
) -> EventDTO:
    return EventDTO(
        id=event.id,
        plan_id=event.plan_id,
        accumulator_id=event.accumulator_id,
        mantra_id=event.mantra_id,
        timer_id=event.timer_id,
        group_recitation_collection_id=event.group_recitation_collection_id,
        group_id=event.group_id,
        location_id=event.location_id,
        location=_location_to_dto(event),
        start_date=event.start_date,
        end_date=event.end_date,
        is_one_day=event.end_date == event.start_date,
        featured=event.featured,
        metadata=_metadata_response(
            event.metadata_entries, language=language, fallback=fallback
        ),
        links=_links_to_dtos(event.links),
        image=safe_get_image_url(
            event.image_url, resource_id=event.id, resource_type="event"
        ),
        image_url=event.image_url,
        participant_count=participant_count,
        is_joined=is_joined,
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


def _validate_group_recitation_collection(
    db, collection_id: Optional[UUID], group_id: UUID
) -> None:
    if collection_id is None:
        return
    collection = get_collection_by_id(
        db=db, collection_id=collection_id, group_id=group_id
    )
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Group recitation collection '{collection_id}' not found "
                f"or does not belong to group '{group_id}'"
            ),
        )


def _validate_location(db, location_id: Optional[UUID], group_id: UUID) -> None:
    if location_id is None:
        return
    location = get_location_without_group_filter(db=db, location_id=location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id '{location_id}' not found",
        )
    if location.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "LOCATION_GROUP_MISMATCH",
                "message": (
                    f"Location '{location_id}' does not belong to group '{group_id}'"
                ),
            },
        )


def get_events_service(
    group_id: Optional[UUID] = None,
    plan_id: Optional[UUID] = None,
    accumulator_id: Optional[UUID] = None,
    mantra_id: Optional[UUID] = None,
    timer_id: Optional[UUID] = None,
    group_recitation_collection_id: Optional[UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    language: Optional[str] = None,
    restrict_group_ids: Optional[List[UUID]] = None,
    fallback: bool = False,
    skip: int = 0,
    limit: int = 20,
    token: Optional[str] = None,
) -> EventsResponse:
    with SessionLocal() as db:
        events, total = get_events(
            db,
            group_id=group_id,
            plan_id=plan_id,
            accumulator_id=accumulator_id,
            mantra_id=mantra_id,
            timer_id=timer_id,
            group_recitation_collection_id=group_recitation_collection_id,
            from_date=from_date,
            to_date=to_date,
            restrict_group_ids=restrict_group_ids,
            skip=skip,
            limit=limit,
        )
        event_ids = [event.id for event in events]
        counts_by_event = get_event_participant_counts(db=db, event_ids=event_ids)

        joined_ids: set[UUID] = set()
        if token:
            current_user = validate_and_extract_user_details(token=token)
            joined_ids = set(
                get_joined_event_ids_by_user(
                    db=db,
                    user_id=current_user.id,
                    event_ids=event_ids,
                )
            )

        return EventsResponse(
            events=[
                _event_to_dto(
                    event,
                    language=language,
                    fallback=fallback,
                    participant_count=counts_by_event.get(event.id, 0),
                    is_joined=(event.id in joined_ids) if token else None,
                )
                for event in events
            ],
            total=total,
            skip=skip,
            limit=limit,
        )


def get_cms_events_service(
    token: str,
    group_id: Optional[UUID] = None,
    plan_id: Optional[UUID] = None,
    accumulator_id: Optional[UUID] = None,
    mantra_id: Optional[UUID] = None,
    timer_id: Optional[UUID] = None,
    group_recitation_collection_id: Optional[UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> EventsResponse:
    current_author = validate_cms_author_details(token=token)

    restrict_group_ids: Optional[List[UUID]] = None
    if not is_super_admin(current_author) and not is_reviewer(current_author):
        with SessionLocal() as db:
            member_group_ids = get_author_group_ids(db=db, author_id=current_author.id)
        if not member_group_ids:
            return EventsResponse(events=[], total=0, skip=skip, limit=limit)
        restrict_group_ids = member_group_ids

    return get_events_service(
        group_id=group_id,
        plan_id=plan_id,
        accumulator_id=accumulator_id,
        mantra_id=mantra_id,
        timer_id=timer_id,
        group_recitation_collection_id=group_recitation_collection_id,
        from_date=from_date,
        to_date=to_date,
        language=language,
        restrict_group_ids=restrict_group_ids,
        skip=skip,
        limit=limit,
    )


def get_cms_event_by_id_service(
    token: str, event_id: UUID, language: Optional[str] = None
) -> EventDTO:
    current_author = validate_cms_author_details(token=token)
    with SessionLocal() as db:
        event = get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id '{event_id}' not found",
            )
        require_can_read_group_content(db=db, group_id=event.group_id, author=current_author)
        participant_count = get_event_participant_count(db=db, event_id=event_id)
        return _event_to_dto(
            event, language=language, participant_count=participant_count
        )


def get_events_today_service(
    timezone: Optional[str] = None,
    group_id: Optional[UUID] = None,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    token: Optional[str] = None,
) -> EventsResponse:
    from_date, to_date = get_day_bounds_in_timezone(timezone)
    return get_events_service(
        group_id=group_id,
        from_date=from_date,
        to_date=to_date,
        language=language,
        fallback=True,
        skip=skip,
        limit=limit,
        token=token,
    )


def get_event_by_id_service(
    event_id: UUID,
    language: Optional[str] = None,
    token: Optional[str] = None,
) -> EventDTO:
    with SessionLocal() as db:
        event = get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id '{event_id}' not found",
            )
        participant_count = get_event_participant_count(db=db, event_id=event_id)
        is_joined = None
        if token:
            current_user = validate_and_extract_user_details(token=token)
            is_joined = is_user_joined_event(
                db=db, event_id=event_id, user_id=current_user.id
            )
        return _event_to_dto(
            event,
            language=language,
            fallback=True,
            participant_count=participant_count,
            is_joined=is_joined,
        )


def create_event_service(token: str, request: CreateEventRequest) -> EventDTO:
    current_author = validate_cms_author_details(token=token)

    event = Event(
        plan_id=request.plan_id,
        accumulator_id=request.accumulator_id,
        mantra_id=request.mantra_id,
        timer_id=request.timer_id,
        group_recitation_collection_id=request.group_recitation_collection_id,
        group_id=request.group_id,
        location_id=request.location_id,
        start_date=request.start_date,
        end_date=request.end_date,
        image_url=request.image_url,
        created_by=current_author.email,
    )

    with SessionLocal() as db:
        require_can_create_content(
            db=db,
            group_id=request.group_id,
            author=current_author,
        )
        _validate_group_recitation_collection(
            db=db,
            collection_id=request.group_recitation_collection_id,
            group_id=request.group_id,
        )
        _validate_location(
            db=db, location_id=request.location_id, group_id=request.group_id
        )
        saved = save_event(db, event, request.metadata, request.links)
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
        if "group_recitation_collection_id" in request.model_fields_set:
            _validate_group_recitation_collection(
                db=db,
                collection_id=request.group_recitation_collection_id,
                group_id=event.group_id,
            )
            event.group_recitation_collection_id = request.group_recitation_collection_id
        if "location_id" in request.model_fields_set:
            _validate_location(
                db=db, location_id=request.location_id, group_id=event.group_id
            )
            event.location_id = request.location_id
        if request.image_url is not None:
            event.image_url = request.image_url

        event.updated_at = datetime.now(timezone.utc)

        saved = update_event(db, event, metadata_entries=request.metadata, link_entries=request.links)
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


def get_featured_events_service(
    language: Optional[str] = None,
    limit: int = 10,
    token: Optional[str] = None,
) -> List[EventDTO]:
    with SessionLocal() as db:
        events = get_featured_events(db, limit=limit)
        event_ids = [event.id for event in events]
        counts_by_event = get_event_participant_counts(db=db, event_ids=event_ids)

        joined_ids: set[UUID] = set()
        if token:
            current_user = validate_and_extract_user_details(token=token)
            joined_ids = set(
                get_joined_event_ids_by_user(
                    db=db,
                    user_id=current_user.id,
                    event_ids=event_ids,
                )
            )

        return [
            _event_to_dto(
                event,
                language=language,
                fallback=True,
                participant_count=counts_by_event.get(event.id, 0),
                is_joined=(event.id in joined_ids) if token else None,
            )
            for event in events
        ]


def update_event_featured_service(token: str, event_id: UUID) -> None:
    current_author = validate_cms_author_details(token=token)
    with SessionLocal() as db:
        event = get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id '{event_id}' not found",
            )
        require_can_change_status(db=db, group_id=event.group_id, author=current_author)
        event.featured = not event.featured
        event.updated_at = datetime.now(timezone.utc)
        update_event(db, event)
