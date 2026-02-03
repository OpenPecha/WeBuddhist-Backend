import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_response_model import (
    SubTaskDTO,
    SubTaskRequest,
    SubTaskRequestFields,
    SubTaskResponse,
    UpdateSubTaskRequest,
    SubTaskOrderRequest,
    SubtaskOrderItem,
)
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services import (
    create_new_sub_tasks,
    update_sub_task_by_task_id,
    change_subtask_order_service,
)
from pecha_api.plans.response_message import BAD_REQUEST, FORBIDDEN, UNAUTHORIZED_TASK_ACCESS
from pecha_api.plans.plans_enums import ContentType


@pytest.mark.asyncio
async def test_create_new_sub_tasks_builds_and_saves_with_incremented_display_order():
    task_id = uuid.uuid4()
    request = SubTaskRequest(
        task_id=task_id,
        sub_tasks=[
            SubTaskRequestFields(content_type="TEXT", content="First", duration="10"),
            SubTaskRequestFields(content_type="TEXT", content="Second", duration="10"),
        ]
    )

    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    saved_items = [
        SimpleNamespace(
            id=uuid.uuid4(), content_type="TEXT", content="First", duration="10", display_order=6, source_text_id=None, pecha_segment_id=None,
        ),
        SimpleNamespace(
            id=uuid.uuid4(), content_type="TEXT", content="Second", duration="10", display_order=7, source_text_id=None, pecha_segment_id=None,
        ),
    ]

    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ) as mock_validate, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ) as mock_session, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=SimpleNamespace(id=task_id, created_by="author@example.com"),
    ) as mock_get_task, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.get_max_display_order_for_sub_task",
        return_value=5,
    ) as mock_get_max, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.PlanSubTask",
    ) as MockPlanSubTask, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.save_sub_tasks_bulk",
        return_value=saved_items,
    ) as mock_save:
        constructed_1 = SimpleNamespace(
            task_id=task_id,
            content_type="TEXT",
            content="First",
            duration="10",
            display_order=6,
            created_by="author@example.com",
        )
        constructed_2 = SimpleNamespace(
            task_id=task_id,
            content_type="TEXT",
            content="Second",
            duration="10",
            display_order=7,
            created_by="author@example.com",
        )

        MockPlanSubTask.side_effect = [constructed_1, constructed_2]

        resp = await create_new_sub_tasks(
            token="token123",
            create_task_request=request,
        )

        assert mock_validate.call_count == 1
        assert mock_validate.call_args.kwargs == {"token": "token123"}

        assert mock_session.call_count == 1
        assert mock_get_task.call_count == 1

        assert mock_get_max.call_count == 1
        assert mock_get_max.call_args.kwargs == {"db": db_mock, "task_id": task_id}

        call1 = MockPlanSubTask.call_args_list[0].kwargs
        call2 = MockPlanSubTask.call_args_list[1].kwargs
        assert call1 == {
            "task_id": task_id,
            "content_type": "TEXT",
            "content": "First",
            "duration": "10",
            "source_text_id": None,
            "pecha_segment_id": None,
            "display_order": 6,
            "created_by": "author@example.com",
        }
        assert call2 == {
            "task_id": task_id,
            "content_type": "TEXT",
            "content": "Second",
            "duration": "10",
            "source_text_id": None,
            "pecha_segment_id": None,
            "display_order": 7,
            "created_by": "author@example.com",
        }

        assert mock_save.call_count == 1
        save_kwargs = mock_save.call_args.kwargs
        assert save_kwargs["db"] is db_mock
        assert save_kwargs["sub_tasks"] == [constructed_1, constructed_2]

        expected = SubTaskResponse(
            sub_tasks=[
                SubTaskDTO(
                    id=saved_items[0].id,
                    content_type=saved_items[0].content_type,
                    content=saved_items[0].content,
                    duration=saved_items[0].duration,
                    display_order=saved_items[0].display_order,
                ),
                SubTaskDTO(
                    id=saved_items[1].id,
                    content_type=saved_items[1].content_type,
                    content=saved_items[1].content,
                    duration=saved_items[1].duration,
                    display_order=saved_items[1].display_order,
                ),
            ]
        )

        assert resp == expected


@pytest.mark.asyncio
async def test_create_new_sub_tasks_task_not_found_raises_http_exception():
    task_id = uuid.uuid4()
    request = SubTaskRequest(
        task_id=task_id,
        sub_tasks=[SubTaskRequestFields(content_type="TEXT", content="First")]
    )

    from fastapi import HTTPException
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        side_effect=HTTPException(status_code=404, detail={"error": BAD_REQUEST, "message": "Task not found"}),
    ):
        with pytest.raises(HTTPException) as exc:
            await create_new_sub_tasks(
                token="token123",
                create_task_request=request,
            )

        assert exc.value.status_code == 404
        detail = exc.value.detail
        assert detail["error"] == BAD_REQUEST
        assert "not found" in detail["message"].lower()



@pytest.mark.asyncio
async def test_update_sub_task_by_task_id_deletes_missing_and_updates_existing_and_returns_none():
    task_id = uuid.uuid4()
    existing_to_keep_id = uuid.uuid4()
    existing_to_delete_id = uuid.uuid4()

    request = UpdateSubTaskRequest(
        task_id=task_id,
        sub_tasks=[
            SubTaskDTO(id=existing_to_keep_id, content_type="TEXT", content="First updated", duration="10", display_order=1),
        ],
    )

    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ) as mock_validate, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ) as mock_session, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=SimpleNamespace(id=task_id, created_by="author@example.com"),
    ) as mock_get_task, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.get_sub_tasks_by_task_id",
        return_value=[
            SimpleNamespace(id=existing_to_keep_id),
            SimpleNamespace(id=existing_to_delete_id),
        ],
    ) as mock_get_subtasks, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.delete_sub_tasks_bulk",
    ) as mock_delete_bulk, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.update_sub_tasks_bulk",
    ) as mock_update_bulk:
        resp = await update_sub_task_by_task_id(
            token="token123",
            update_sub_task_request=request,
        )

        assert mock_validate.call_count == 1
        assert mock_validate.call_args.kwargs == {"token": "token123"}

        assert mock_session.call_count == 1
        assert mock_get_task.call_count == 1

        assert mock_get_subtasks.call_count == 1
        assert mock_get_subtasks.call_args.kwargs == {"db": db_mock, "task_id": task_id}

        assert mock_delete_bulk.call_count == 1
        delete_kwargs = mock_delete_bulk.call_args.kwargs
        assert delete_kwargs["db"] is db_mock
        assert delete_kwargs["sub_tasks_ids"] == [existing_to_delete_id]

        assert mock_update_bulk.call_count == 1
        update_kwargs = mock_update_bulk.call_args.kwargs
        assert update_kwargs["db"] is db_mock
        assert update_kwargs["sub_tasks"] == request.sub_tasks

        assert resp is None


@pytest.mark.asyncio
async def test_update_sub_task_by_task_id_unauthorized_raises_http_exception_403():
    task_id = uuid.uuid4()

    request = UpdateSubTaskRequest(
        task_id=task_id,
        sub_tasks=[
            SubTaskDTO(id=uuid.uuid4(), content_type="TEXT", content="X", duration="10", display_order=1),
        ],
    )

    from fastapi import HTTPException
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        side_effect=HTTPException(status_code=403, detail={"error": FORBIDDEN, "message": UNAUTHORIZED_TASK_ACCESS}),
    ):

        with pytest.raises(HTTPException) as exc:
            await update_sub_task_by_task_id(
                token="token123",
                update_sub_task_request=request,
            )

        assert exc.value.status_code == 403
        detail = exc.value.detail
        assert detail["error"] == FORBIDDEN
        assert detail["message"] == UNAUTHORIZED_TASK_ACCESS


@pytest.mark.asyncio
async def test_update_sub_task_by_task_id_creates_new_sub_tasks_for_none_ids():
    task_id = uuid.uuid4()
    existing_id = uuid.uuid4()

    request = UpdateSubTaskRequest(
        task_id=task_id,
        sub_tasks=[
            SubTaskDTO(id=existing_id, content_type="TEXT", content="Keep updated", duration="10", display_order=1),
            SubTaskDTO(id=None, content_type="TEXT", content="New A", duration="10", display_order=2),
            SubTaskDTO(id=None, content_type="TEXT", content="New B", duration="10", display_order=3),
        ],
    )

    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    constructed_a = SimpleNamespace(
        task_id=task_id,
        content_type="TEXT",
        content="New A",
        duration="10",
        display_order=2,
        created_by="author@example.com",
    )
    constructed_b = SimpleNamespace(
        task_id=task_id,
        content_type="TEXT",
        content="New B",
        duration="10",
        cdisplay_order=3,
        created_by="author@example.com",
    )

    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=SimpleNamespace(id=task_id, created_by="author@example.com"),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.get_sub_tasks_by_task_id",
        return_value=[SimpleNamespace(id=existing_id)],
    ) as mock_get_subtasks, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.delete_sub_tasks_bulk",
    ) as mock_delete_bulk, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.update_sub_tasks_bulk",
    ) as mock_update_bulk, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.PlanSubTask",
    ) as MockPlanSubTask, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.save_sub_tasks_bulk",
    ) as mock_save_bulk:
        MockPlanSubTask.side_effect = [constructed_a, constructed_b]

        resp = await update_sub_task_by_task_id(
            token="token123",
            update_sub_task_request=request,
        )

        assert mock_get_subtasks.call_count == 1
        assert mock_delete_bulk.call_count == 1
        assert mock_delete_bulk.call_args.kwargs["sub_tasks_ids"] == []

        assert mock_update_bulk.call_count == 1
        assert mock_update_bulk.call_args.kwargs["sub_tasks"] == [request.sub_tasks[0]]

        assert MockPlanSubTask.call_count == 2
        call1 = MockPlanSubTask.call_args_list[0].kwargs
        call2 = MockPlanSubTask.call_args_list[1].kwargs
        assert call1 == {
            "task_id": task_id,
            "content_type": ContentType.TEXT,
            "content": "New A",
            "duration": "10",
            "display_order": 2,
            "created_by": "author@example.com",
        }
        assert call2 == {
            "task_id": task_id,
            "content_type": ContentType.TEXT,
            "content": "New B",
            "duration": "10",
            "display_order": 3,
            "created_by": "author@example.com",
        }

        assert mock_save_bulk.call_count == 1
        assert mock_save_bulk.call_args.kwargs["db"] is db_mock
        assert mock_save_bulk.call_args.kwargs["sub_tasks"] == [constructed_a, constructed_b]

        assert resp is None


@pytest.mark.asyncio
async def test_update_sub_task_by_task_id_task_not_found_raises_http_exception_400():
    task_id = uuid.uuid4()

    request = UpdateSubTaskRequest(
        task_id=task_id,
        sub_tasks=[],
    )

    from fastapi import HTTPException
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        side_effect=HTTPException(status_code=404, detail={"error": BAD_REQUEST, "message": "Task not found"}),
    ):
        with pytest.raises(HTTPException) as exc:
            await update_sub_task_by_task_id(
                token="token123",
                update_sub_task_request=request,
            )

        assert exc.value.status_code == 404
        detail = exc.value.detail
        assert detail["error"] == BAD_REQUEST
        assert "not found" in detail["message"].lower()

@pytest.mark.asyncio
async def test_change_subtask_order_service_success():
    """Test successful subtask order change with proper authentication and all operations"""
    task_id = uuid.uuid4()
    sub_task_id_1 = uuid.uuid4()
    sub_task_id_2 = uuid.uuid4()
    sub_task_id_3 = uuid.uuid4()
    
    task = SimpleNamespace(id=task_id, created_by="author@example.com")
    
    request = SubTaskOrderRequest(
        subtasks=[
            SubtaskOrderItem(id=sub_task_id_1, display_order=3),
            SubtaskOrderItem(id=sub_task_id_2, display_order=1),
            SubtaskOrderItem(id=sub_task_id_3, display_order=2),
        ]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ) as mock_validate, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=task,
    ) as mock_get_task, patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.update_sub_task_order_in_bulk_by_task_id",
        return_value=None,
    ) as mock_update_bulk:
        
        result = await change_subtask_order_service(
            token="token123",
            task_id=task_id,
            update_subtask_order=request,
        )
        
        mock_validate.assert_called_once_with(token="token123")
        
        mock_get_task.assert_called_once_with(
            db=db_mock,
            task_id=task_id,
            current_author=mock_validate.return_value,
            is_admin=mock_validate.return_value.is_admin
        )
        
        mock_update_bulk.assert_called_once_with(
            db=db_mock,
            sub_task_list=request.subtasks,
            task_id=task.id
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_change_subtask_order_service_move_up():
    """Test moving subtask from position 5 to position 2"""
    task_id = uuid.uuid4()
    sub_task_ids = [uuid.uuid4() for _ in range(5)]
    
    task = SimpleNamespace(id=task_id, created_by="author@example.com")
    
    request = SubTaskOrderRequest(
        subtasks=[
            SubtaskOrderItem(id=sub_task_ids[0], display_order=1),
            SubtaskOrderItem(id=sub_task_ids[4], display_order=2),  # Moved from 5 to 2
            SubtaskOrderItem(id=sub_task_ids[1], display_order=3),
            SubtaskOrderItem(id=sub_task_ids[2], display_order=4),
            SubtaskOrderItem(id=sub_task_ids[3], display_order=5),
        ]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=task,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.update_sub_task_order_in_bulk_by_task_id",
        return_value=None,
    ) as mock_update_bulk:
        
        result = await change_subtask_order_service(
            token="token456",
            task_id=task_id,
            update_subtask_order=request,
        )
        
        assert mock_update_bulk.call_count == 1
        assert len(mock_update_bulk.call_args.kwargs["sub_task_list"]) == 5
        assert result is None


@pytest.mark.asyncio
async def test_change_subtask_order_service_move_down():
    """Test moving subtask from position 2 to position 5"""
    task_id = uuid.uuid4()
    sub_task_ids = [uuid.uuid4() for _ in range(5)]
    
    task = SimpleNamespace(id=task_id, created_by="author@example.com")
    
    request = SubTaskOrderRequest(
        subtasks=[
            SubtaskOrderItem(id=sub_task_ids[0], display_order=1),
            SubtaskOrderItem(id=sub_task_ids[2], display_order=2),
            SubtaskOrderItem(id=sub_task_ids[3], display_order=3),
            SubtaskOrderItem(id=sub_task_ids[4], display_order=4),
            SubtaskOrderItem(id=sub_task_ids[1], display_order=5),
        ]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=task,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.update_sub_task_order_in_bulk_by_task_id",
        return_value=None,
    ) as mock_update_bulk:
        
        result = await change_subtask_order_service(
            token="test_token",
            task_id=task_id,
            update_subtask_order=request,
        )
        
        assert mock_update_bulk.call_count == 1
        assert len(mock_update_bulk.call_args.kwargs["sub_task_list"]) == 5
        assert result is None


@pytest.mark.asyncio
async def test_change_subtask_order_service_to_first_position():
    """Test moving subtask to first position (order 1)"""
    task_id = uuid.uuid4()
    sub_task_ids = [uuid.uuid4() for _ in range(3)]
    
    task = SimpleNamespace(id=task_id, created_by="author@example.com")
    
    request = SubTaskOrderRequest(
        subtasks=[
            SubtaskOrderItem(id=sub_task_ids[2], display_order=1),
            SubtaskOrderItem(id=sub_task_ids[0], display_order=2),
            SubtaskOrderItem(id=sub_task_ids[1], display_order=3),
        ]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=task,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.update_sub_task_order_in_bulk_by_task_id",
        return_value=None,
    ):
        
        result = await change_subtask_order_service(
            token="auth_token",
            task_id=task_id,
            update_subtask_order=request,
        )
        
        assert result is None


@pytest.mark.asyncio
async def test_change_subtask_order_service_invalid_token():
    """Test subtask order change with invalid authentication token (401 Unauthorized)"""
    from fastapi import HTTPException
    
    task_id = uuid.uuid4()
    sub_task_id = uuid.uuid4()
    
    request = SubTaskOrderRequest(
        subtasks=[SubtaskOrderItem(id=sub_task_id, display_order=1)]
    )
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        side_effect=HTTPException(status_code=401, detail="Invalid or expired token"),
    ):
        
        with pytest.raises(HTTPException) as exc:
            await change_subtask_order_service(
                token="expired_token",
                task_id=task_id,
                update_subtask_order=request,
            )
        
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_change_subtask_order_service_task_not_found():
    """Test subtask order change when task doesn't exist (404 Not Found)"""
    from fastapi import HTTPException
    
    task_id = uuid.uuid4()
    sub_task_id = uuid.uuid4()
    
    request = SubTaskOrderRequest(
        subtasks=[SubtaskOrderItem(id=sub_task_id, display_order=1)]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        side_effect=HTTPException(status_code=404, detail="Task not found"),
    ):
        
        with pytest.raises(HTTPException) as exc:
            await change_subtask_order_service(
                token="valid_token",
                task_id=task_id,
                update_subtask_order=request,
            )
        
        assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_change_subtask_order_service_unauthorized():
    """Test subtask order change with unauthorized user (403 Forbidden)"""
    from fastapi import HTTPException
    
    task_id = uuid.uuid4()
    sub_task_id = uuid.uuid4()
    
    request = SubTaskOrderRequest(
        subtasks=[SubtaskOrderItem(id=sub_task_id, display_order=1)]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        side_effect=HTTPException(status_code=403, detail={"error": FORBIDDEN, "message": UNAUTHORIZED_TASK_ACCESS}),
    ):
        
        with pytest.raises(HTTPException) as exc:
            await change_subtask_order_service(
                token="invalid_token",
                task_id=task_id,
                update_subtask_order=request,
            )
        
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_change_subtask_order_service_database_error():
    """Test subtask order change with database error (500 Internal Server Error)"""
    from fastapi import HTTPException
    
    task_id = uuid.uuid4()
    sub_task_ids = [uuid.uuid4() for _ in range(3)]
    
    task = SimpleNamespace(id=task_id, created_by="author@example.com")
    
    request = SubTaskOrderRequest(
        subtasks=[
            SubtaskOrderItem(id=sub_task_ids[0], display_order=1),
            SubtaskOrderItem(id=sub_task_ids[1], display_order=2),
            SubtaskOrderItem(id=sub_task_ids[2], display_order=3),
        ]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        side_effect=Exception("Database connection error"),
    ):
        
        with pytest.raises(Exception) as exc:
            await change_subtask_order_service(
                token="valid_token",
                task_id=task_id,
                update_subtask_order=request,
            )
        
        assert "Database connection error" in str(exc.value)


@pytest.mark.asyncio
async def test_change_subtask_order_service_update_failed():
    """Test subtask order change when update operation fails (400 Bad Request)"""
    from fastapi import HTTPException
    
    task_id = uuid.uuid4()
    sub_task_ids = [uuid.uuid4() for _ in range(2)]
    
    task = SimpleNamespace(id=task_id, created_by="author@example.com")
    
    request = SubTaskOrderRequest(
        subtasks=[
            SubtaskOrderItem(id=sub_task_ids[0], display_order=2),
            SubtaskOrderItem(id=sub_task_ids[1], display_order=1),
        ]
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.validate_and_extract_author_details",
        return_value=SimpleNamespace(email="author@example.com", is_admin=False),
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services._get_author_task",
        return_value=task,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services.update_sub_task_order_in_bulk_by_task_id",
        side_effect=HTTPException(status_code=400, detail={"error": BAD_REQUEST, "message": "Subtask order update failed"}),
    ):
        
        with pytest.raises(HTTPException) as exc:
            await change_subtask_order_service(
                token="valid_token",
                task_id=task_id,
                update_subtask_order=request,
            )
        
        assert exc.value.status_code == 400