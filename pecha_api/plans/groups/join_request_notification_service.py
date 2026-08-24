import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.chat.notification_repository import (
    get_active_push_devices_by_user_ids,
    normalize_platform,
)
from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_model import Author
from pecha_api.plans.groups.groups_enums import (
    AuthorGroupJoinRequestStatus,
    AuthorGroupMemberRole,
)
from pecha_api.plans.groups.groups_models import AuthorGroupJoinRequest, AuthorGroupMember
from pecha_api.plans.groups.join_request_notification_response_models import (
    JoinRequestNotificationRecipientDTO,
    JoinRequestNotificationTargetsResponse,
    JoinRequestPushDeviceTargetDTO,
)
from pecha_api.plans.groups.join_request_sqs_client import (
    JOIN_REQUEST_CREATED_EVENT,
    JOIN_REQUEST_DECIDED_EVENT,
)
from pecha_api.users.users_models import Users

logger = logging.getLogger(__name__)

JOIN_REQUEST_NOT_FOUND = "Join request not found"


def _status_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _group_title(group) -> str:
    entries = getattr(group, "metadata_entries", None) or []
    for entry in entries:
        language = entry.language
        code = language.value if hasattr(language, "value") else str(language)
        if code.upper() == "EN":
            return entry.title
    return entries[0].title if entries else "Group"


def _display_name(user) -> str:
    if user is None:
        return "Someone"
    parts = [user.firstname, user.lastname]
    name = " ".join(part for part in parts if part).strip()
    return name or "Someone"


def _moderator_user_ids(db, group_id: UUID) -> List[UUID]:
    """Studio moderators reachable by push.

    Authors and app users are separate identities linked only by email, so a
    moderator without an app account is simply skipped here."""
    emails = [
        row[0]
        for row in db.query(Author.email)
        .join(AuthorGroupMember, AuthorGroupMember.author_id == Author.id)
        .filter(
            AuthorGroupMember.group_id == group_id,
            AuthorGroupMember.role.in_(
                [AuthorGroupMemberRole.OWNER.value, AuthorGroupMemberRole.ADMIN.value]
            ),
        )
        .all()
        if row[0]
    ]
    if not emails:
        return []
    lowered = [email.lower() for email in emails]
    return [
        row[0]
        for row in db.query(Users.id).filter(Users.email.in_(lowered)).all()
    ]


def _notification_copy(*, event_type: str, group_name: str, requester_name: str, status_value: str):
    if event_type == JOIN_REQUEST_CREATED_EVENT:
        return (
            f"Request to join {group_name}",
            f"{requester_name} asked to join {group_name}.",
        )
    if status_value == AuthorGroupJoinRequestStatus.APPROVED.value:
        return (
            f"You've joined {group_name}",
            f"Your request to join {group_name} was approved.",
        )
    return (
        f"Request to join {group_name} declined",
        f"Your request to join {group_name} was not approved.",
    )


def get_join_request_notification_targets(
    *,
    join_request_id: UUID,
    skip: int,
    limit: int,
    event_type: Optional[str] = None,
) -> JoinRequestNotificationTargetsResponse:
    with SessionLocal() as db:
        join_request = (
            db.query(AuthorGroupJoinRequest)
            .filter(AuthorGroupJoinRequest.id == join_request_id)
            .first()
        )
        if not join_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=JOIN_REQUEST_NOT_FOUND,
            )

        status_value = _status_value(join_request.status)
        # The queued event decides who is notified. Inferring it from current
        # status would turn a late CREATED event into a duplicate decision push.
        if event_type not in (JOIN_REQUEST_CREATED_EVENT, JOIN_REQUEST_DECIDED_EVENT):
            event_type = (
                JOIN_REQUEST_CREATED_EVENT
                if status_value == AuthorGroupJoinRequestStatus.PENDING.value
                else JOIN_REQUEST_DECIDED_EVENT
            )

        group_name = _group_title(join_request.group)
        requester = db.query(Users).filter(Users.id == join_request.user_id).first()
        requester_name = _display_name(requester)

        if event_type == JOIN_REQUEST_CREATED_EVENT:
            recipient_ids = _moderator_user_ids(db, join_request.group_id)
        else:
            recipient_ids = [join_request.user_id]

        total = len(recipient_ids)
        page_ids = recipient_ids[skip : skip + limit]
        devices_by_user = get_active_push_devices_by_user_ids(db=db, user_ids=page_ids)

        recipients: List[JoinRequestNotificationRecipientDTO] = []
        for user_id in page_ids:
            devices = devices_by_user.get(user_id) or []
            if not devices:
                continue
            recipients.append(
                JoinRequestNotificationRecipientDTO(
                    user_id=user_id,
                    push_devices=[
                        JoinRequestPushDeviceTargetDTO(
                            id=device.id,
                            token=device.token,
                            platform=normalize_platform(device.platform),
                        )
                        for device in devices
                    ],
                )
            )

        title, body = _notification_copy(
            event_type=event_type,
            group_name=group_name,
            requester_name=requester_name,
            status_value=status_value,
        )

        return JoinRequestNotificationTargetsResponse(
            join_request_id=join_request.id,
            group_id=join_request.group_id,
            event_type=event_type,
            status=status_value,
            group_name=group_name,
            requester_name=requester_name,
            title=title,
            body=body,
            recipients=recipients,
            skip=skip,
            limit=limit,
            total=total,
            has_more=(skip + limit) < total,
        )
