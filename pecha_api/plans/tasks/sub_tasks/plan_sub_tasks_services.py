from typing import List
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.tasks.plan_tasks_services import _get_author_task
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.response_message import BAD_REQUEST, FORBIDDEN, UNAUTHORIZED_TASK_ACCESS, SUBTASK_ORDER_FAILED
from pecha_api.plans.tasks.plan_tasks_repository import get_task_by_id
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_repository import (
    get_max_display_order_for_sub_task,
    save_sub_tasks_bulk,
    get_sub_tasks_by_task_id,
    delete_sub_tasks_bulk,
    update_sub_task_order_in_bulk_by_task_id,
    update_sub_tasks_bulk,
    get_sub_task_by_id,
    update_sub_task_order,
    update_sub_tasks
)

from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_response_model import (
    SubTaskDTO,
    SubTaskRequest,
    SubTaskResponse,
    UpdateSubTaskRequest,
    SubTaskOrderRequest,
    SubTaskOrderResponse
)
from pecha_api.error_contants import ErrorConstants
from pecha_api.plans.response_message import SUBTASK_ORDER_FAILED

async def create_new_sub_tasks(token: str, create_task_request: SubTaskRequest) -> SubTaskResponse:
    current_author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db:
        _get_author_task(db=db, task_id=create_task_request.task_id, current_author=current_author,is_admin=current_author.is_admin)

        next_display_order = get_max_display_order_for_sub_task(db=db, task_id=create_task_request.task_id) + 1

        new_sub_tasks: List[PlanSubTask] = []
        for index, sub in enumerate(create_task_request.sub_tasks, start=0):
            
            new_sub_tasks.append(
                PlanSubTask(
                    task_id=create_task_request.task_id,
                    content_type=sub.content_type,
                    content=sub.content,
                    duration=sub.duration,
                    source_text_id=sub.source_text_id,          
                    pecha_segment_id=sub.pecha_segment_id,
                    display_order=next_display_order + index,
                    created_by=current_author.email,
                )
            )

        saved_sub_tasks = save_sub_tasks_bulk(db=db, sub_tasks=new_sub_tasks)
        created_sub_tasks=[
                SubTaskDTO(
                    id=item.id,
                    content_type=item.content_type,
                    content=item.content,
                    duration=item.duration,
                    source_text_id=item.source_text_id,          
                    pecha_segment_id=item.pecha_segment_id,
                    display_order=item.display_order,
                )
                for item in saved_sub_tasks
            ]
        return SubTaskResponse(
            sub_tasks=created_sub_tasks,
        )

async def update_sub_task_by_task_id(token: str, update_sub_task_request: UpdateSubTaskRequest) -> None:
    current_author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db:
        _get_author_task(db=db, task_id=update_sub_task_request.task_id, current_author=current_author,is_admin=current_author.is_admin)

        existing_sub_tasks_to_update: List[SubTaskDTO] = [
            subtask for subtask in update_sub_task_request.sub_tasks if subtask.id is not None
        ]

        new_sub_tasks_to_create: List[PlanSubTask] = [
            PlanSubTask(
                task_id=update_sub_task_request.task_id,
                content_type=subtask.content_type,
                content=subtask.content,
                duration=subtask.duration,
                source_text_id=subtask.source_text_id,
                pecha_segment_id=subtask.pecha_segment_id,
                display_order=subtask.display_order,
                created_by=current_author.email,
            )
            for subtask in update_sub_task_request.sub_tasks
            if subtask.id is None
        ]

        existing_in_db = get_sub_tasks_by_task_id(db=db, task_id=update_sub_task_request.task_id)
        existing_ids_in_db = [sub_task.id for sub_task in existing_in_db]
        requested_existing_ids = [sub_task.id for sub_task in existing_sub_tasks_to_update]
        sub_tasks_ids_to_delete = [id for id in existing_ids_in_db if id not in requested_existing_ids]

        delete_sub_tasks_bulk(db=db, sub_tasks_ids=sub_tasks_ids_to_delete)

        update_sub_tasks_bulk(db=db, sub_tasks=existing_sub_tasks_to_update)

        if new_sub_tasks_to_create:
            save_sub_tasks_bulk(db=db, sub_tasks=new_sub_tasks_to_create)


async def change_subtask_order_service(token: str, task_id: UUID, update_subtask_order: SubTaskOrderRequest) -> None:
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        task = _get_author_task(db=db, task_id=task_id, current_author=current_author,is_admin=current_author.is_admin)
        
        update_sub_task_order_in_bulk_by_task_id(db=db, sub_task_list=update_subtask_order.subtasks,task_id=task.id)
