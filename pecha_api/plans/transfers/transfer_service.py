from datetime import datetime, timezone
from typing import List, Optional, Set
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.notification.notification_repository import mark_all_notifications_read_by_reference
from pecha_api.notification.notification_service import create_notification_record
from pecha_api.plans.authors.plan_authors_model import Author
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.groups.groups_models import AuthorGroupMember
from pecha_api.plans.groups.groups_repository import get_group_by_id
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_repository import get_series_by_id
from pecha_api.plans.shared.permissions import (
    get_member_role,
    is_super_admin,
    require_active_author,
    require_can_request_transfer,
    require_can_respond_transfer,
    require_cms_write_access,
)
from pecha_api.plans.transfers.transfer_enums import (
    NOTIFICATION_CATEGORY_CONTENT_TRANSFER,
    ContentTransferStatus,
    TransferEntityType,
    normalize_transfer_status,
)
from pecha_api.plans.transfers.transfer_invite_email import send_content_transfer_invitation_email
from pecha_api.plans.transfers.transfer_models import ContentTransferRequest
from pecha_api.plans.transfers.transfer_repository import (
    create_transfer_request,
    get_transfer_by_id,
    has_pending_transfer,
    list_incoming_transfers,
    list_outgoing_transfers,
    save_transfer,
)
from pecha_api.plans.transfers.transfer_response_models import (
    CreateTransferRequestBody,
    TransferRequestCreatedResponse,
    TransferRequestDTO,
    TransferRequestListResponse,
)


def _group_title(group) -> str:
    if not group or not group.metadata_entries:
        return "Group"
    return group.metadata_entries[0].title


def _requester_display_name(author: Author) -> str:
    return f"{author.first_name} {author.last_name}".strip() or author.email


def _entity_title(db: Session, entity_type: TransferEntityType, entity_id: UUID) -> str:
    if entity_type == TransferEntityType.PLAN:
        plan = get_plan_by_id(db=db, plan_id=entity_id)
        return plan.title if plan else "Plan"
    series = get_series_by_id(db=db, series_id=entity_id)
    if not series or not series.metadata_entries:
        return "Series"
    return series.metadata_entries[0].title


def _to_dto(
    db: Session,
    transfer,
    *,
    entity_title: Optional[str] = None,
) -> TransferRequestDTO:
    from_group = get_group_by_id(db=db, group_id=transfer.from_group_id)
    to_group = get_group_by_id(db=db, group_id=transfer.to_group_id)
    entity_type = TransferEntityType(
        transfer.entity_type.value if hasattr(transfer.entity_type, "value") else transfer.entity_type
    )
    return TransferRequestDTO(
        id=transfer.id,
        entity_type=entity_type,
        entity_id=transfer.entity_id,
        from_group_id=transfer.from_group_id,
        to_group_id=transfer.to_group_id,
        status=normalize_transfer_status(transfer.status),
        requested_by=transfer.requested_by,
        expires_at=transfer.expires_at,
        created_at=transfer.created_at,
        entity_title=entity_title or _entity_title(db, entity_type, transfer.entity_id),
        from_group_title=_group_title(from_group),
        to_group_title=_group_title(to_group),
    )


def _managed_group_ids(db: Session, author: Author) -> List[UUID]:
    if is_super_admin(author):
        rows = db.query(AuthorGroupMember.group_id).distinct().all()
        return [row[0] for row in rows]
    rows = (
        db.query(AuthorGroupMember.group_id)
        .filter(
            AuthorGroupMember.author_id == author.id,
            AuthorGroupMember.role.in_(
                [
                    AuthorGroupMemberRole.OWNER.value,
                    AuthorGroupMemberRole.ADMIN.value,
                ]
            ),
        )
        .all()
    )
    return [row[0] for row in rows]


def _target_responder_emails(db: Session, group_id: UUID) -> Set[str]:
    rows = (
        db.query(AuthorGroupMember)
        .options()
        .join(Author, Author.id == AuthorGroupMember.author_id)
        .filter(
            AuthorGroupMember.group_id == group_id,
            AuthorGroupMember.role.in_(
                [
                    AuthorGroupMemberRole.OWNER.value,
                    AuthorGroupMemberRole.ADMIN.value,
                ]
            ),
        )
        .all()
    )
    emails: Set[str] = set()
    for member in rows:
        if member.author and member.author.email:
            emails.add(member.author.email)
    return emails


def _notify_target_admins(
    db: Session,
    *,
    transfer,
    requester: Author,
    entity_label: str,
    entity_title: str,
    from_group_title: str,
    to_group_title: str,
) -> Optional[UUID]:
    target_members = (
        db.query(AuthorGroupMember)
        .options(selectinload(AuthorGroupMember.author))
        .filter(
            AuthorGroupMember.group_id == transfer.to_group_id,
            AuthorGroupMember.role.in_(
                [
                    AuthorGroupMemberRole.OWNER.value,
                    AuthorGroupMemberRole.ADMIN.value,
                ]
            ),
        )
        .all()
    )
    first_notification_id: Optional[UUID] = None
    requester_name = _requester_display_name(requester)
    for member in target_members:
        notification = create_notification_record(
            recipient_author_id=member.author_id,
            title=f"Transfer request: {entity_title}",
            description=(
                f"{requester_name} requested to transfer {entity_label} "
                f"from {from_group_title} to {to_group_title}."
            ),
            category=NOTIFICATION_CATEGORY_CONTENT_TRANSFER,
            reference_id=transfer.id,
        )
        if first_notification_id is None:
            first_notification_id = notification.id
        if member.author and member.author.email:
            send_content_transfer_invitation_email(
                target_email=member.author.email,
                requester_name=requester_name,
                requester_email=requester.email,
                entity_label=entity_label,
                entity_title=entity_title,
                from_group_title=from_group_title,
                to_group_title=to_group_title,
            )
    return first_notification_id


def _mark_transfer_notifications_read(db: Session, *, transfer_id: UUID) -> None:
    mark_all_notifications_read_by_reference(
        db=db,
        category=NOTIFICATION_CATEGORY_CONTENT_TRANSFER,
        reference_id=transfer_id,
    )


def _create_transfer(
    token: str,
    *,
    entity_type: TransferEntityType,
    entity_id: UUID,
    body: CreateTransferRequestBody,
) -> TransferRequestCreatedResponse:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    require_cms_write_access(author)

    with SessionLocal() as db:
        if entity_type == TransferEntityType.PLAN:
            plan = get_plan_by_id(db=db, plan_id=entity_id)
            if not plan or plan.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
            if plan.series_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Plan is attached to a series; transfer the series or detach the plan first",
                )
            from_group_id = plan.group_id
            entity_title = plan.title
            entity_label = "plan"
        else:
            series = get_series_by_id(db=db, series_id=entity_id)
            if not series or series.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
            from_group_id = series.group_id
            entity_title = _entity_title(db, entity_type, entity_id)
            entity_label = "series"

        if body.target_group_id == from_group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target group must differ from the current group",
            )
        target_group = get_group_by_id(db=db, group_id=body.target_group_id)
        if not target_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target group not found")

        require_can_request_transfer(db=db, from_group_id=from_group_id, author=author)
        target_role = get_member_role(db=db, group_id=body.target_group_id, author_id=author.id)
        if not is_super_admin(author) and target_role is None:
            pass

        if has_pending_transfer(db=db, entity_type=entity_type, entity_id=entity_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pending transfer request already exists for this content",
            )

        transfer = create_transfer_request(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            from_group_id=from_group_id,
            to_group_id=body.target_group_id,
            requested_by=author.email,
        )
        from_group = get_group_by_id(db=db, group_id=from_group_id)
        to_group = get_group_by_id(db=db, group_id=body.target_group_id)
        from_group_title = _group_title(from_group)
        to_group_title = _group_title(to_group)
        notification_id = _notify_target_admins(
            db=db,
            transfer=transfer,
            requester=author,
            entity_label=entity_label,
            entity_title=entity_title,
            from_group_title=from_group_title,
            to_group_title=to_group_title,
        )
        dto = _to_dto(db, transfer, entity_title=entity_title)

    return TransferRequestCreatedResponse(transfer=dto, notification_id=notification_id)


def create_plan_transfer_request(
    token: str,
    plan_id: UUID,
    body: CreateTransferRequestBody,
) -> TransferRequestCreatedResponse:
    return _create_transfer(
        token=token,
        entity_type=TransferEntityType.PLAN,
        entity_id=plan_id,
        body=body,
    )


def create_series_transfer_request(
    token: str,
    series_id: UUID,
    body: CreateTransferRequestBody,
) -> TransferRequestCreatedResponse:
    return _create_transfer(
        token=token,
        entity_type=TransferEntityType.SERIES,
        entity_id=series_id,
        body=body,
    )


def list_incoming_transfer_requests(
    token: str,
    status_filter: Optional[ContentTransferStatus] = None,
) -> TransferRequestListResponse:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    with SessionLocal() as db:
        group_ids = _managed_group_ids(db=db, author=author)
        rows = list_incoming_transfers(db=db, group_ids=group_ids, status=status_filter)
        dtos = [_to_dto(db, row) for row in rows]
    return TransferRequestListResponse(transfers=dtos, total=len(dtos))


def list_outgoing_transfer_requests(
    token: str,
    status_filter: Optional[ContentTransferStatus] = None,
) -> TransferRequestListResponse:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    with SessionLocal() as db:
        if is_super_admin(author):
            query = db.query(ContentTransferRequest)
            if status_filter is not None:
                query = query.filter(ContentTransferRequest.status == status_filter.value)
            rows = query.order_by(ContentTransferRequest.created_at.desc()).all()
        else:
            source_group_ids = (
                db.query(AuthorGroupMember.group_id)
                .filter(AuthorGroupMember.author_id == author.id)
                .distinct()
                .all()
            )
            group_ids = [row[0] for row in source_group_ids]
            rows = list_outgoing_transfers(db=db, group_ids=group_ids, status=status_filter)
        dtos = [_to_dto(db, row) for row in rows]
    return TransferRequestListResponse(transfers=dtos, total=len(dtos))


def list_incoming_transfer_requests_for_group(
    token: str,
    group_id: UUID,
    status_filter: Optional[ContentTransferStatus] = None,
) -> TransferRequestListResponse:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    with SessionLocal() as db:
        if not get_group_by_id(db=db, group_id=group_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        if not is_super_admin(author):
            require_can_respond_transfer(db=db, to_group_id=group_id, author=author)
        rows = list_incoming_transfers(db=db, group_ids=[group_id], status=status_filter)
        dtos = [_to_dto(db, row) for row in rows]
    return TransferRequestListResponse(transfers=dtos, total=len(dtos))


def list_outgoing_transfer_requests_for_group(
    token: str,
    group_id: UUID,
    status_filter: Optional[ContentTransferStatus] = None,
) -> TransferRequestListResponse:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    with SessionLocal() as db:
        if not get_group_by_id(db=db, group_id=group_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        if not is_super_admin(author):
            member = (
                db.query(AuthorGroupMember.id)
                .filter(
                    AuthorGroupMember.group_id == group_id,
                    AuthorGroupMember.author_id == author.id,
                )
                .first()
            )
            if member is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a member of this group",
                )
        rows = list_outgoing_transfers(db=db, group_ids=[group_id], status=status_filter)
        dtos = [_to_dto(db, row) for row in rows]
    return TransferRequestListResponse(transfers=dtos, total=len(dtos))


def _apply_transfer_accept(db: Session, transfer) -> None:
    entity_type = TransferEntityType(
        transfer.entity_type.value if hasattr(transfer.entity_type, "value") else transfer.entity_type
    )
    if entity_type == TransferEntityType.PLAN:
        plan = get_plan_by_id(db=db, plan_id=transfer.entity_id)
        if plan:
            plan.group_id = transfer.to_group_id
            db.add(plan)
    else:
        series = get_series_by_id(db=db, series_id=transfer.entity_id)
        if series:
            series.group_id = transfer.to_group_id
            db.add(series)
            for plan in series.plans or []:
                if plan.deleted_at is None:
                    plan.group_id = transfer.to_group_id
                    db.add(plan)
    db.commit()


def accept_transfer_request(token: str, transfer_id: UUID) -> TransferRequestDTO:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    require_cms_write_access(author)
    with SessionLocal() as db:
        transfer = get_transfer_by_id(db=db, transfer_id=transfer_id)
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")
        if normalize_transfer_status(transfer.status) != ContentTransferStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer request is not pending")
        if transfer.expires_at < datetime.now(timezone.utc):
            transfer.status = ContentTransferStatus.EXPIRED
            save_transfer(db=db, transfer=transfer)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer request has expired")
        require_can_respond_transfer(db=db, to_group_id=transfer.to_group_id, author=author)
        transfer.status = ContentTransferStatus.ACCEPTED
        transfer.responded_by = author.email
        transfer.accepted_at = datetime.now(timezone.utc)
        save_transfer(db=db, transfer=transfer)
        _apply_transfer_accept(db=db, transfer=transfer)
        _mark_transfer_notifications_read(db=db, transfer_id=transfer.id)
        dto = _to_dto(db, transfer)
    return dto


def reject_transfer_request(token: str, transfer_id: UUID) -> TransferRequestDTO:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    require_cms_write_access(author)
    with SessionLocal() as db:
        transfer = get_transfer_by_id(db=db, transfer_id=transfer_id)
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")
        if normalize_transfer_status(transfer.status) != ContentTransferStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer request is not pending")
        require_can_respond_transfer(db=db, to_group_id=transfer.to_group_id, author=author)
        transfer.status = ContentTransferStatus.REJECTED
        transfer.responded_by = author.email
        transfer.rejected_at = datetime.now(timezone.utc)
        saved = save_transfer(db=db, transfer=transfer)
        _mark_transfer_notifications_read(db=db, transfer_id=saved.id)
        dto = _to_dto(db, saved)
    return dto


def revoke_transfer_request(token: str, transfer_id: UUID) -> TransferRequestDTO:
    author = validate_and_extract_author_details(token=token)
    require_active_author(author)
    require_cms_write_access(author)
    with SessionLocal() as db:
        transfer = get_transfer_by_id(db=db, transfer_id=transfer_id)
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")
        if normalize_transfer_status(transfer.status) != ContentTransferStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transfer request is not pending")
        if not is_super_admin(author) and transfer.requested_by != author.email:
            require_can_request_transfer(db=db, from_group_id=transfer.from_group_id, author=author)
        transfer.status = ContentTransferStatus.REVOKED
        transfer.responded_by = author.email
        transfer.revoked_at = datetime.now(timezone.utc)
        saved = save_transfer(db=db, transfer=transfer)
        dto = _to_dto(db, saved)
    return dto
