from uuid import UUID
from typing import List
from fastapi import HTTPException
from starlette import status
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST, PLAN_NOT_FOUND, DUPLICATE_DAY_NUMBERS, PLAN_DAY_NOT_FOUND
from .plan_items_repository import (
    save_plan_item,
    save_plan_items,
    get_last_day_number,
    delete_days_by_ids,
    get_days_by_plan_id,
    get_days_by_plan_id_and_day_ids,
    update_day_by_id,
    update_days_in_bulk_by_plan_id,
    get_plan_day_by_id_with_tasks_and_subtasks,
)
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id, get_plan_by_id_and_created_by
from .plan_items_models import PlanItem
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.authors.plan_authors_model import Author
from .plan_items_response_models import ItemDTO, ReorderDaysRequest, CreateDaysRequest, DeleteDaysRequest
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from pecha_api.plans.audio.sub_task_timestamps_models import SubTaskTimestamp
from pecha_api.db.database import SessionLocal

def create_plan_item(token: str, plan_id: UUID, create_days_request: CreateDaysRequest) -> List[ItemDTO]:
    current_author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        plan = _get_author_plan(plan_id=plan_id, current_author=current_author, is_admin=current_author.is_admin)
        last_day_number = get_last_day_number(db=db_session, plan_id=plan.id)

        new_plan_items = [
            PlanItem(
                plan_id=plan.id,
                day_number=last_day_number + offset,
                created_by=current_author.email,
            )
            for offset in range(1, create_days_request.number_of_days + 1)
        ]
        saved_items = save_plan_items(db=db_session, plan_items=new_plan_items)
        created_days = [
            ItemDTO(
                id=saved_item.id,
                plan_id=saved_item.plan_id,
                day_number=saved_item.day_number,
            )
            for saved_item in saved_items
        ]

        if create_days_request.source_day_id:
            source_day = get_plan_day_by_id_with_tasks_and_subtasks(
                db=db_session,
                plan_id=plan.id,
                day_id=create_days_request.source_day_id,
            )
            _copy_tasks_and_subtasks_to_days(
                db=db_session,
                source_day=source_day,
                target_days=saved_items,
                created_by=current_author.email,
            )

    return created_days

def delete_plan_days(token: str, plan_id: UUID, delete_days_request: DeleteDaysRequest) -> None:
    if not delete_days_request.day_ids:
        return

    current_author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        plan = _get_author_plan(plan_id=plan_id, current_author=current_author, is_admin=current_author.is_admin)

        unique_day_ids = list(dict.fromkeys(delete_days_request.day_ids))
        days = get_days_by_plan_id_and_day_ids(db=db_session, plan_id=plan.id, day_ids=unique_day_ids)
        if len(days) != len(unique_day_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message=PLAN_DAY_NOT_FOUND).model_dump(),
            )

        delete_days_by_ids(db=db_session, plan_id=plan.id, day_ids=unique_day_ids)
        _reorder_day_display_order(db=db_session, plan_id=plan.id)

def update_plans_day_number(token: str, plan_id: UUID, reorder_days_request: ReorderDaysRequest) -> None:
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db_session:
        plan = _get_author_plan(plan_id=plan_id, current_author=current_author,is_admin=current_author.is_admin)
        _check_duplicate_day_number_payload(payload=reorder_days_request)
        update_days_in_bulk_by_plan_id(db=db_session, plan_id=plan.id, days=reorder_days_request.days)

def _reorder_day_display_order(db: SessionLocal(), plan_id: UUID) -> None:

    items = get_days_by_plan_id(db=db, plan_id=plan_id)
    sorted_items = sorted(items, key=lambda x: x.day_number)
    
    for index, item in enumerate(sorted_items, start=1):
        update_day_by_id(db=db, plan_id=plan_id, day_id=item.id, day_number=index)


def _get_author_plan(plan_id: UUID, current_author: Author, is_admin: bool) -> Plan:
    with SessionLocal() as db_session:
        plan = get_plan_by_id_and_created_by(db=db_session, plan_id=plan_id, created_by=current_author.email, is_admin=is_admin)
        if not is_admin and plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump())
        return plan

def _check_duplicate_day_number_payload(payload: ReorderDaysRequest) -> None:

    #store the day numbers which is unique using set function...
    day_numbers = set([day.day_number for day in payload.days])
    if len(day_numbers) != len(payload.days):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=DUPLICATE_DAY_NUMBERS).model_dump())


def _copy_tasks_and_subtasks_to_days(
    db: SessionLocal(),
    source_day: PlanItem,
    target_days: List[PlanItem],
    created_by: str,
) -> None:
    source_tasks = sorted(source_day.tasks, key=lambda task: task.display_order)
    if not source_tasks:
        return

    try:
        for target_day in target_days:
            for source_task in source_tasks:
                new_task = PlanTask(
                    plan_item_id=target_day.id,
                    title=source_task.title,
                    display_order=source_task.display_order,
                    estimated_time=source_task.estimated_time,
                    is_required=source_task.is_required,
                    created_by=created_by,
                )
                db.add(new_task)
                db.flush()

                for source_sub_task in sorted(source_task.sub_tasks, key=lambda sub_task: sub_task.display_order):
                    new_sub_task = PlanSubTask(
                        task_id=new_task.id,
                        content_type=source_sub_task.content_type,
                        content=source_sub_task.content,
                        duration=source_sub_task.duration,
                        source_text_id=source_sub_task.source_text_id,
                        pecha_segment_id=source_sub_task.pecha_segment_id,
                        segment_ids=source_sub_task.segment_ids,
                        display_order=source_sub_task.display_order,
                        created_by=created_by,
                    )
                    db.add(new_sub_task)
                    db.flush()

                    if source_sub_task.timestamp:
                        db.add(
                            SubTaskTimestamp(
                                sub_task_id=new_sub_task.id,
                                start_ms=source_sub_task.timestamp.start_ms,
                                end_ms=source_sub_task.timestamp.end_ms,
                                created_by=created_by,
                            )
                        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump(),
        )