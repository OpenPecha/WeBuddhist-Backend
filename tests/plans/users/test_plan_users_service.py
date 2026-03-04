import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException

from pecha_api.plans.users.plan_users_response_models import UserPlanEnrollRequest
from pecha_api.plans.users.plan_users_service import (
    enroll_user_in_plan,
    complete_sub_task_service,
    complete_task_service,
    get_user_enrolled_plans,
    get_user_plan_progress,
    get_user_plan_day_details_service,
    delete_task_service,
    unenroll_user_from_plan,
)
from pecha_api.plans.users.plan_users_progress_repository import delete_user_plan_progress
from pecha_api.plans.response_message import (
    BAD_REQUEST,
    PLAN_NOT_FOUND,
    ALREADY_ENROLLED_IN_PLAN,
    SUB_TASK_NOT_FOUND,
    TASK_NOT_FOUND,
)
from pecha_api.plans.plans_response_models import PlanDTO
from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus
from pecha_api.error_contants import ErrorConstants
from pecha_api.plans.plans_enums import ContentType


def _mock_session_with_db():
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    return db_mock, session_cm


def test_enroll_user_in_plan_success():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    enroll_request = UserPlanEnrollRequest(plan_id=plan_id)

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ) as mock_validate, patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_by_id",
        return_value=SimpleNamespace(id=plan_id),
    ) as mock_get_plan, patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=None,
    ) as mock_get_progress, patch(
        "pecha_api.plans.users.plan_users_service.UserPlanProgress",
    ) as MockUserPlanProgress, patch(
        "pecha_api.plans.users.plan_users_service.save_plan_progress",
    ) as mock_save:
        constructed = SimpleNamespace(user_id=user_id, plan_id=plan_id)
        MockUserPlanProgress.return_value = constructed

        result = enroll_user_in_plan(token="token123", enroll_request=enroll_request)

        assert result is None

        mock_validate.assert_called_once_with(token="token123")
        mock_get_plan.assert_called_once_with(db=db_mock, plan_id=plan_id)
        mock_get_progress.assert_called_once_with(db=db_mock, user_id=user_id, plan_id=plan_id)

        ctor_kwargs = MockUserPlanProgress.call_args.kwargs
        assert ctor_kwargs["user_id"] == user_id
        assert ctor_kwargs["plan_id"] == plan_id
        assert ctor_kwargs["streak_count"] == 0
        assert ctor_kwargs["longest_streak"] == 0
        assert "status" in ctor_kwargs  
        assert ctor_kwargs["is_completed"] is False
        assert "created_at" in ctor_kwargs

        mock_save.assert_called_once()
        assert mock_save.call_args.kwargs["db"] is db_mock
        assert mock_save.call_args.kwargs["plan_progress"] is constructed


def test_enroll_user_in_plan_plan_not_found_raises_404():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    enroll_request = UserPlanEnrollRequest(plan_id=plan_id)

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            enroll_user_in_plan(token="tkn", enroll_request=enroll_request)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == PLAN_NOT_FOUND


def test_enroll_user_in_plan_already_enrolled_raises_409():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    enroll_request = UserPlanEnrollRequest(plan_id=plan_id)

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_by_id",
        return_value=SimpleNamespace(id=plan_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        with pytest.raises(HTTPException) as exc_info:
            enroll_user_in_plan(token="tkn", enroll_request=enroll_request)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == ALREADY_ENROLLED_IN_PLAN


def test_complete_sub_task_service_success():
    user_id = uuid.uuid4()
    sub_task_id = uuid.uuid4()
    task_id = uuid.uuid4()
    day_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ) as mock_validate, patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_sub_task_by_subtask_id",
        return_value=SimpleNamespace(id=sub_task_id, task_id=task_id),
    ) as mock_get_sub_task, patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=SimpleNamespace(id=task_id, plan_item_id=day_id),
    ) as mock_get_task, patch(
        "pecha_api.plans.users.plan_users_service.UserSubTaskCompletion",
    ) as MockUserSubTaskCompletion, patch(
        "pecha_api.plans.users.plan_users_service.save_user_sub_task_completions",
    ) as mock_save, patch(
        "pecha_api.plans.users.plan_users_service._check_all_subtasks_completed",
        return_value=False,
    ) as mock_check_all, patch(
        "pecha_api.plans.users.plan_users_service.save_user_task_completion",
    ) as mock_save_task_completion, patch(
        "pecha_api.plans.users.plan_users_service.check_day_completion",
        return_value=None,
    ) as mock_check_day, patch(
        "pecha_api.plans.users.plan_users_service.save_user_day_completion",
    ) as mock_save_day:
        constructed = SimpleNamespace(user_id=user_id, sub_task_id=sub_task_id)
        MockUserSubTaskCompletion.return_value = constructed

        result = complete_sub_task_service(token="token123", id=sub_task_id)

        assert result is None

        mock_validate.assert_called_once_with(token="token123")
        mock_get_sub_task.assert_called_once_with(db=db_mock, id=sub_task_id)
        mock_get_task.assert_called_once_with(db=db_mock, task_id=task_id)

        ctor_kwargs = MockUserSubTaskCompletion.call_args.kwargs
        assert ctor_kwargs["user_id"] == user_id
        assert ctor_kwargs["sub_task_id"] == sub_task_id

        mock_save.assert_called_once()
        assert mock_save.call_args.kwargs["db"] is db_mock
        assert mock_save.call_args.kwargs["user_sub_task_completions"] is constructed
        mock_check_all.assert_called_once()
        assert mock_check_all.call_args.kwargs["user_id"] == user_id
        assert mock_check_all.call_args.kwargs["task_id"] == task_id
        mock_save_task_completion.assert_not_called()
        mock_check_day.assert_called_once_with(db=db_mock, user_id=user_id, day_id=day_id)
        mock_save_day.assert_not_called()


def test_complete_sub_task_service_sub_task_not_found_raises_404():
    user_id = uuid.uuid4()
    sub_task_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_sub_task_by_subtask_id",
        return_value=None,
    ):
        with pytest.raises(AttributeError) as exc_info:
            complete_sub_task_service(token="token123", id=sub_task_id)
        
        assert "'NoneType' object has no attribute 'task_id'" in str(exc_info.value)


def test_complete_sub_task_service_marks_task_completion_when_all_subtasks_done():
    user_id = uuid.uuid4()
    sub_task_id = uuid.uuid4()
    task_id = uuid.uuid4()
    day_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_sub_task_by_subtask_id",
        return_value=SimpleNamespace(id=sub_task_id, task_id=task_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=SimpleNamespace(id=task_id, plan_item_id=day_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserSubTaskCompletion",
    ) as MockUserSubTaskCompletion, patch(
        "pecha_api.plans.users.plan_users_service.save_user_sub_task_completions",
    ) as mock_save_subtask, patch(
        "pecha_api.plans.users.plan_users_service._check_all_subtasks_completed",
        return_value=True,
    ) as mock_check_all, patch(
        "pecha_api.plans.users.plan_users_service.UserTaskCompletion",
    ) as MockUserTaskCompletion, patch(
        "pecha_api.plans.users.plan_users_service.save_user_task_completion",
    ) as mock_save_task, patch(
        "pecha_api.plans.users.plan_users_service.check_day_completion",
        return_value=None,
    ) as mock_check_day, patch(
        "pecha_api.plans.users.plan_users_service.save_user_day_completion",
    ) as mock_save_day:
        constructed_sub = SimpleNamespace(user_id=user_id, sub_task_id=sub_task_id)
        MockUserSubTaskCompletion.return_value = constructed_sub

        constructed_task = SimpleNamespace(user_id=user_id, task_id=task_id)
        MockUserTaskCompletion.return_value = constructed_task

        result = complete_sub_task_service(token="token123", id=sub_task_id)

        assert result is None
        mock_save_subtask.assert_called_once()
        assert mock_save_subtask.call_args.kwargs["db"] is db_mock
        assert mock_save_subtask.call_args.kwargs["user_sub_task_completions"] is constructed_sub

        mock_check_all.assert_called_once()
        assert mock_check_all.call_args.kwargs["user_id"] == user_id
        assert mock_check_all.call_args.kwargs["task_id"] == task_id

        # When all subtasks are completed, task completion should be saved
        mock_save_task.assert_called_once()
        assert mock_save_task.call_args.kwargs["db"] is db_mock
        assert mock_save_task.call_args.kwargs["user_task_completion"] is constructed_task
        
        # check_day_completion should be called
        mock_check_day.assert_called_once_with(db=db_mock, user_id=user_id, day_id=day_id)
        # Day completion should NOT be saved since check_day_completion returned None (not completed)
        mock_save_day.assert_not_called()


def test_complete_sub_task_service_saves_day_completion_when_day_completed():
    """Test that day completion is saved when check_day_completion indicates day is complete"""
    user_id = uuid.uuid4()
    sub_task_id = uuid.uuid4()
    task_id = uuid.uuid4()
    day_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_sub_task_by_subtask_id",
        return_value=SimpleNamespace(id=sub_task_id, task_id=task_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=SimpleNamespace(id=task_id, plan_item_id=day_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserSubTaskCompletion",
    ) as MockUserSubTaskCompletion, patch(
        "pecha_api.plans.users.plan_users_service.save_user_sub_task_completions",
    ), patch(
        "pecha_api.plans.users.plan_users_service._check_all_subtasks_completed",
        return_value=True,
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserTaskCompletion",
    ) as MockUserTaskCompletion, patch(
        "pecha_api.plans.users.plan_users_service.save_user_task_completion",
    ), patch(
        "pecha_api.plans.users.plan_users_service.check_day_completion",
        return_value=True,
    ) as mock_check_day, patch(
        "pecha_api.plans.users.plan_users_service.UserDayCompletion",
    ) as MockUserDayCompletion, patch(
        "pecha_api.plans.users.plan_users_service.save_user_day_completion",
    ) as mock_save_day:
        constructed_sub = SimpleNamespace(user_id=user_id, sub_task_id=sub_task_id)
        MockUserSubTaskCompletion.return_value = constructed_sub

        constructed_task = SimpleNamespace(user_id=user_id, task_id=task_id)
        MockUserTaskCompletion.return_value = constructed_task

        constructed_day = SimpleNamespace(user_id=user_id, day_id=day_id)
        MockUserDayCompletion.return_value = constructed_day

        result = complete_sub_task_service(token="token123", id=sub_task_id)

        assert result is None
        
        # check_day_completion should be called
        mock_check_day.assert_called_once_with(db=db_mock, user_id=user_id, day_id=day_id)
        
        # Day completion SHOULD be saved since check_day_completion returned True
        mock_save_day.assert_called_once()
        assert mock_save_day.call_args.kwargs["db"] is db_mock
        saved_day = mock_save_day.call_args.kwargs["user_day_completion"]
        assert saved_day.user_id == user_id
        assert saved_day.day_id == day_id


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_success():
    from datetime import datetime, timezone
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans

    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    mock_user = SimpleNamespace(id=user_id)
    progress = SimpleNamespace(started_at=datetime.now(timezone.utc))
    # emulate enums with .value
    language = SimpleNamespace(value="EN")
    difficulty = SimpleNamespace(value="BEGINNER")
    plan = SimpleNamespace(
        id=plan_id,
        title="Test Plan",
        description="Test Description",
        language=language,
        difficulty_level=difficulty,
        image_url="images/plan_images/test.jpg",
        tags=["meditation", "mindfulness"],
    )

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ) as mock_validate, patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
        return_value=([(progress, plan, 30)], 1),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get",
        return_value="bucket",
    ), patch(
        "pecha_api.plans.users.plan_users_service.generate_presigned_access_url",
        return_value="https://signed.example.com/plan.jpg",
    ):
        result = await get_user_enrolled_plans(
            token="token123", status_filter=None, skip=0, limit=20
        )

        mock_validate.assert_called_once_with(token="token123")

        assert result.skip == 0
        assert result.limit == 20
        assert result.total == 1
        assert len(result.plans) == 1

        plan_dto = result.plans[0]
        assert plan_dto.id == plan_id
        assert plan_dto.title == "Test Plan"
        assert plan_dto.description == "Test Description"
        assert plan_dto.language == "EN"
        assert plan_dto.difficulty_level == "BEGINNER"
        assert plan_dto.total_days == 30
        assert plan_dto.tags == ["meditation", "mindfulness"]
        assert plan_dto.image_url.startswith("https://signed.")



@pytest.mark.asyncio
async def test_get_user_enrolled_plans_with_status_filter():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans
    from datetime import datetime, timezone

    user_id = uuid.uuid4()
    mock_user = SimpleNamespace(id=user_id)
    progress = SimpleNamespace(started_at=datetime.now(timezone.utc))
    plan = SimpleNamespace(
        id=uuid.uuid4(),
        title="Active Plan",
        description="Test",
        language=SimpleNamespace(value="EN"),
        difficulty_level=SimpleNamespace(value="BEGINNER"),
        image_url=None,
        tags=[],
    )

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
    ) as mock_repo:
        mock_repo.return_value = ([(progress, plan, 10)], 1)

        result = await get_user_enrolled_plans(
            token="token123", status_filter="active", skip=0, limit=20
        )

        # status normalized to uppercase
        assert mock_repo.call_args.kwargs["status"] == "ACTIVE"
        assert result.total == 1


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_with_pagination():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans
    from datetime import datetime, timezone

    user_id = uuid.uuid4()
    mock_user = SimpleNamespace(id=user_id)

    # repo returns only the page slice, but also a total count
    total = 50
    results = []
    for i in range(10):
        pid = uuid.uuid4()
        progress = SimpleNamespace(started_at=datetime.now(timezone.utc))
        plan = SimpleNamespace(
            id=pid,
            title=f"Plan {i}",
            description="Test",
            language=SimpleNamespace(value="EN"),
            difficulty_level=SimpleNamespace(value="BEGINNER"),
            image_url=None,
            tags=[],
        )
        results.append((progress, plan, 10))

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
        return_value=(results, total),
    ):
        result = await get_user_enrolled_plans(
            token="token123", status_filter=None, skip=10, limit=10
        )

        assert result.skip == 10
        assert result.limit == 10
        assert result.total == 50
        assert len(result.plans) == 10


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_empty_result():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans

    user_id = uuid.uuid4()
    mock_user = SimpleNamespace(id=user_id)

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
        return_value=([], 0),
    ):
        result = await get_user_enrolled_plans(
            token="tok", status_filter=None, skip=0, limit=20
        )

        assert result.skip == 0
        assert result.limit == 20
        assert result.total == 0
        assert len(result.plans) == 0


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_success_with_filter_and_pagination():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans
    from datetime import datetime, timezone

    user_id = uuid.uuid4()
    plan_id_1 = uuid.uuid4()
    plan_id_2 = uuid.uuid4()

    progress = SimpleNamespace(started_at=datetime.now(timezone.utc))
    plan1 = SimpleNamespace(
        id=plan_id_1,
        title="Plan 1",
        description="Desc",
        language=SimpleNamespace(value="EN"),
        difficulty_level=SimpleNamespace(value="BEGINNER"),
        image_url=None,
        tags=[],
    )
    plan2 = SimpleNamespace(
        id=plan_id_2,
        title="Plan 2",
        description="Desc",
        language=SimpleNamespace(value="EN"),
        difficulty_level=SimpleNamespace(value="BEGINNER"),
        image_url=None,
        tags=[],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
        return_value=([(progress, plan1, 10)], 1),
    ):
        result = await get_user_enrolled_plans(
            token="tok", status_filter="active", skip=0, limit=1
        )

        assert result.skip == 0
        assert result.limit == 1
        assert result.total == 1
        assert len(result.plans) == 1
        assert result.plans[0].id == plan_id_1


@pytest.mark.asyncio
async def test_get_user_plan_progress_success():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    dto = PlanDTO(
        id=plan_id,
        title="Plan X",
        description="desc",
        language="en",
        total_days=30,
        status=PlanStatus.PUBLISHED,
        subscription_count=0,
        difficulty_level=DifficultyLevel.BEGINNER,
        tags=[],
    )

    mock_progress = [
        {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "plan_id": str(plan_id),
            "started_at": "2024-01-15T10:00:00Z",
            "streak_count": 2,
            "longest_streak": 3,
            "status": "active",
            "is_completed": False,
            "completed_at": None,
            "created_at": "2024-01-15T10:00:00Z",
        }
    ]

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.MOCK_USER_PROGRESS",
        new=mock_progress, create=True,
    ), patch(
        "pecha_api.plans.users.plan_users_service.load_plans_from_json",
        return_value=SimpleNamespace(plans=[SimpleNamespace(id=str(plan_id))]),
    ), patch(
        "pecha_api.plans.users.plan_users_service.convert_plan_model_to_dto",
        return_value=dto,
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserPlanProgress",
    ) as MockUserPlanProgress:
        constructed = SimpleNamespace(
            id=uuid.uuid4(),
            user_id=user_id,
            plan_id=plan_id,
            plan=dto.model_dump(),
            status="active",
        )
        MockUserPlanProgress.return_value = constructed

        result = await get_user_plan_progress(token="tok", plan_id=plan_id)

        ctor_kwargs = MockUserPlanProgress.call_args.kwargs
        assert ctor_kwargs["user_id"] == user_id
        assert ctor_kwargs["plan_id"] == plan_id
        assert ctor_kwargs["plan"]["id"] == plan_id
        assert ctor_kwargs["status"] == "active"

        assert result is constructed


@pytest.mark.asyncio
async def test_get_user_plan_progress_not_enrolled_raises_404():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.MOCK_USER_PROGRESS",
        new=[], create=True,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_plan_progress(token="tok", plan_id=plan_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not enrolled in this plan"


def _mock_session_with_db_and_task_flow():
    db_mock, session_cm = _mock_session_with_db()
    return db_mock, session_cm


def test_complete_task_service_success():
    user_id = uuid.uuid4()
    task_id = uuid.uuid4()
    day_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db_and_task_flow()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=SimpleNamespace(id=task_id, plan_item_id=day_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.complete_all_subtasks_completions",
    ) as mock_complete_all_subtasks, patch(
        "pecha_api.plans.users.plan_users_service.UserTaskCompletion",
    ) as MockUserTaskCompletion, patch(
        "pecha_api.plans.users.plan_users_service.save_user_task_completion",
    ) as mock_save, patch(
        "pecha_api.plans.users.plan_users_service.check_day_completion",
    ) as mock_check_day_completion:
        constructed = SimpleNamespace(user_id=user_id, task_id=task_id)
        MockUserTaskCompletion.return_value = constructed

        result = complete_task_service(token="tok", task_id=task_id)

        assert result is None
        mock_save.assert_called_once()
        assert mock_save.call_args.kwargs["db"] is db_mock
        assert mock_save.call_args.kwargs["user_task_completion"] is constructed

        mock_complete_all_subtasks.assert_called_once()
        assert mock_complete_all_subtasks.call_args.kwargs["db"] is db_mock
        assert mock_complete_all_subtasks.call_args.kwargs["user_id"] == user_id
        assert mock_complete_all_subtasks.call_args.kwargs["task_id"] == task_id

        mock_check_day_completion.assert_called_once()
        assert mock_check_day_completion.call_args.kwargs["db"] is db_mock
        assert mock_check_day_completion.call_args.kwargs["user_id"] == user_id
        assert mock_check_day_completion.call_args.kwargs["day_id"] == day_id


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_without_image():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans
    from datetime import datetime, timezone

    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    mock_user = SimpleNamespace(id=user_id)
    progress = SimpleNamespace(started_at=datetime.now(timezone.utc))
    plan = SimpleNamespace(
        id=plan_id,
        title="Plan Without Image",
        description="Description",
        language=SimpleNamespace(value="BO"),
        difficulty_level=SimpleNamespace(value="INTERMEDIATE"),
        image_url=None,
        tags=[],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
        return_value=([(progress, plan, 0)], 1),
    ):
        result = await get_user_enrolled_plans(
            token="token123", status_filter=None, skip=0, limit=20
        )

        assert len(result.plans) == 1
        assert result.plans[0].id == plan_id
        assert result.plans[0].title == "Plan Without Image"
        assert result.plans[0].image_url == ""
        assert result.skip == 0
        assert result.limit == 20
        assert result.total == 1


def test_complete_task_service_task_not_found_raises_404():
    user_id = uuid.uuid4()
    task_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db_and_task_flow()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            complete_task_service(token="tok", task_id=task_id)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_presigned_url_error():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans
    from datetime import datetime, timezone

    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    mock_user = SimpleNamespace(id=user_id)
    progress = SimpleNamespace(started_at=datetime.now(timezone.utc))
    plan = SimpleNamespace(
        id=plan_id,
        title="Test Plan",
        description="Test Description",
        language=SimpleNamespace(value="EN"),
        difficulty_level=SimpleNamespace(value="BEGINNER"),
        image_url="images/plan_images/test.jpg",
        tags=[],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
        return_value=([(progress, plan, 30)], 1),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get",
        return_value="bucket",
    ), patch(
        "pecha_api.plans.users.plan_users_service.generate_presigned_access_url",
        side_effect=Exception("S3 error"),
    ):
        result = await get_user_enrolled_plans(
            token="token123", status_filter=None, skip=0, limit=20
        )

        assert len(result.plans) == 1
        plan_dto = result.plans[0]
        assert plan_dto.image_url == ""


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_multiple_plans():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans
    from datetime import datetime, timezone

    user_id = uuid.uuid4()
    plan_id_1 = uuid.uuid4()
    plan_id_2 = uuid.uuid4()
    plan_id_3 = uuid.uuid4()

    mock_user = SimpleNamespace(id=user_id)

    progress_1 = SimpleNamespace(started_at=datetime.now(timezone.utc))
    progress_2 = SimpleNamespace(started_at=datetime.now(timezone.utc))
    progress_3 = SimpleNamespace(started_at=datetime.now(timezone.utc))

    plan_1 = SimpleNamespace(
        id=plan_id_1,
        title="Meditation Plan",
        description="Daily meditation",
        language=SimpleNamespace(value="EN"),
        difficulty_level=SimpleNamespace(value="BEGINNER"),
        image_url="images/plan1.jpg",
        tags=["meditation"],
    )
    plan_2 = SimpleNamespace(
        id=plan_id_2,
        title="Advanced Dharma",
        description="Advanced teachings",
        language=SimpleNamespace(value="BO"),
        difficulty_level=SimpleNamespace(value="ADVANCED"),
        image_url="images/plan2.jpg",
        tags=["dharma", "philosophy"],
    )
    plan_3 = SimpleNamespace(
        id=plan_id_3,
        title="Beginner's Guide",
        description="Introduction",
        language="EN",  # exercise string branch
        difficulty_level="BEGINNER",  # exercise string branch
        image_url=None,
        tags=["basics"],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_enrolled_plans_with_details",
        return_value=(
            [
                (progress_1, plan_1, 21),
                (progress_2, plan_2, 90),
                (progress_3, plan_3, 7),
            ],
            3,
        ),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get",
        return_value="bucket",
    ), patch(
        "pecha_api.plans.users.plan_users_service.generate_presigned_access_url",
        return_value="https://signed.example.com/img.jpg",
    ):
        result = await get_user_enrolled_plans(
            token="token123", status_filter=None, skip=0, limit=20
        )

        assert len(result.plans) == 3
        assert result.skip == 0
        assert result.limit == 20
        assert result.total == 3

        assert result.plans[0].title == "Meditation Plan"
        assert result.plans[0].language == "EN"
        assert result.plans[0].total_days == 21

        assert result.plans[1].title == "Advanced Dharma"
        assert result.plans[1].language == "BO"
        assert result.plans[1].difficulty_level == "ADVANCED"
        assert result.plans[1].total_days == 90

        assert result.plans[2].title == "Beginner's Guide"
        assert result.plans[2].image_url == ""  # no image generates empty string
        assert result.plans[2].total_days == 7


def test_complete_all_subtasks_completions_creates_missing_only():
    from pecha_api.plans.users.plan_users_service import complete_all_subtasks_completions

    user_id = uuid.uuid4()
    task_id = uuid.uuid4()

    sub_a, sub_b, sub_c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_sub_tasks_by_task_id",
        return_value=[SimpleNamespace(id=sub_a), SimpleNamespace(id=sub_b), SimpleNamespace(id=sub_c)],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_uncompleted_user_sub_task_ids",
        return_value=[sub_b],
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserSubTaskCompletion",
        side_effect=lambda user_id, sub_task_id: SimpleNamespace(user_id=user_id, sub_task_id=sub_task_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_user_sub_task_completions_bulk",
    ) as mock_bulk:
        complete_all_subtasks_completions(db=db_mock, user_id=user_id, task_id=task_id)

        assert mock_bulk.call_count == 1
        created_list = mock_bulk.call_args.kwargs["user_sub_task_completions"]
        assert len(created_list) == 1
        assert created_list[0].user_id == user_id
        assert created_list[0].sub_task_id == sub_b


def test_complete_all_subtasks_completions_no_new_items_calls_bulk_with_empty():
    from pecha_api.plans.users.plan_users_service import complete_all_subtasks_completions

    user_id = uuid.uuid4()
    task_id = uuid.uuid4()

    sub_a, sub_b = uuid.uuid4(), uuid.uuid4()

    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_sub_tasks_by_task_id",
        return_value=[SimpleNamespace(id=sub_a), SimpleNamespace(id=sub_b)],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_uncompleted_user_sub_task_ids",
        return_value=[],
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserSubTaskCompletion",
        side_effect=lambda user_id, sub_task_id: SimpleNamespace(user_id=user_id, sub_task_id=sub_task_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_user_sub_task_completions_bulk",
    ) as mock_bulk:
        complete_all_subtasks_completions(db=db_mock, user_id=user_id, task_id=task_id)

        created_list = mock_bulk.call_args.kwargs["user_sub_task_completions"]
        assert created_list == []


def test_check_day_completion_marks_day_complete_when_all_done():
    from pecha_api.plans.users.plan_users_service import check_day_completion

    user_id = uuid.uuid4()
    day_id = uuid.uuid4()

    t1, t2 = uuid.uuid4(), uuid.uuid4()

    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_tasks_by_plan_item_id",
        return_value=[SimpleNamespace(id=t1), SimpleNamespace(id=t2)],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_uncompleted_user_task_ids",
        return_value=[],
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserDayCompletion",
        side_effect=lambda user_id, day_id: SimpleNamespace(user_id=user_id, day_id=day_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_user_day_completion",
    ) as mock_save:
        check_day_completion(db=db_mock, user_id=user_id, day_id=day_id)

        assert mock_save.call_count == 1
        udc = mock_save.call_args.kwargs["user_day_completion"]
        assert udc.user_id == user_id
        assert udc.day_id == day_id


def test_check_day_completion_does_nothing_when_remaining_tasks():
    from pecha_api.plans.users.plan_users_service import check_day_completion

    user_id = uuid.uuid4()
    day_id = uuid.uuid4()

    t1, t2 = uuid.uuid4(), uuid.uuid4()

    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_tasks_by_plan_item_id",
        return_value=[SimpleNamespace(id=t1), SimpleNamespace(id=t2)],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_uncompleted_user_task_ids",
        return_value=[t2],
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_user_day_completion",
    ) as mock_save:
        check_day_completion(db=db_mock, user_id=user_id, day_id=day_id)

        mock_save.assert_not_called()


def test_delete_task_service_success():
    user_id = uuid.uuid4()
    task_id = uuid.uuid4()
    day_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    sub_a, sub_b = uuid.uuid4(), uuid.uuid4()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=SimpleNamespace(id=task_id, plan_item_id=day_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.delete_user_task_completion",
    ) as mock_delete_task, patch(
        "pecha_api.plans.users.plan_users_service.delete_user_day_completion",
    ) as mock_delete_day, patch(
        "pecha_api.plans.users.plan_users_service.get_sub_tasks_by_task_id",
        return_value=[SimpleNamespace(id=sub_a), SimpleNamespace(id=sub_b)],
    ) as mock_get_subtasks, patch(
        "pecha_api.plans.users.plan_users_service.delete_user_subtask_completion",
    ) as mock_delete_subtasks:
        result = delete_task_service(token="tok", task_id=task_id)

        assert result is None
        mock_delete_task.assert_called_once()
        assert mock_delete_task.call_args.kwargs["db"] is db_mock
        assert mock_delete_task.call_args.kwargs["user_id"] == user_id
        assert mock_delete_task.call_args.kwargs["task_id"] == task_id

        mock_delete_day.assert_called_once()
        assert mock_delete_day.call_args.kwargs["db"] is db_mock
        assert mock_delete_day.call_args.kwargs["user_id"] == user_id
        assert mock_delete_day.call_args.kwargs["day_id"] == day_id

        mock_get_subtasks.assert_called_once_with(db=db_mock, task_id=task_id)
        mock_delete_subtasks.assert_called_once()
        assert mock_delete_subtasks.call_args.kwargs["db"] is db_mock
        assert mock_delete_subtasks.call_args.kwargs["user_id"] == user_id
        assert set(mock_delete_subtasks.call_args.kwargs["sub_task_ids"]) == {sub_a, sub_b}


def test_delete_task_service_task_not_found_raises_404():
    user_id = uuid.uuid4()
    task_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_task_service(token="tok", task_id=task_id)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_enrolled_plans_invalid_token():
    from pecha_api.plans.users.plan_users_service import get_user_enrolled_plans
    
    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        side_effect=HTTPException(status_code=401, detail={"error": "Unauthorized", "message": "Invalid token"}),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_enrolled_plans(
                token="invalid_token",
                status_filter=None,
                skip=0,
                limit=20
            )
        
        assert exc_info.value.status_code == 401


def test_delete_task_service_task_not_found_raises_404():
    user_id = uuid.uuid4()
    task_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_task_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_task_service(token="tok", task_id=task_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == TASK_NOT_FOUND


@pytest.mark.asyncio
async def test_get_user_plan_progress_plan_not_found():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    mock_progress = [
        {
            "id": str(uuid.uuid4()),
            "user_id": str(user_id),
            "plan_id": str(plan_id),
            "started_at": "2024-01-15T10:00:00Z",
            "streak_count": 1,
            "longest_streak": 1,
            "status": "active",
            "is_completed": False,
            "completed_at": None,
            "created_at": "2024-01-15T10:00:00Z",
        }
    ]

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.MOCK_USER_PROGRESS",
        new=mock_progress, create=True,
    ), patch(
        "pecha_api.plans.users.plan_users_service.load_plans_from_json",
        return_value=SimpleNamespace(plans=[]),  # plan missing
    ):
        from pecha_api.plans.users.plan_users_service import get_user_plan_progress

        with pytest.raises(HTTPException) as exc_info:
            await get_user_plan_progress(token="tok", plan_id=plan_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.PLAN_NOT_FOUND


def test_get_user_plan_day_details_service_success():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    task1_id = uuid.uuid4()
    task2_id = uuid.uuid4()
    sub1_id = uuid.uuid4()
    sub2_id = uuid.uuid4()

    plan_item = SimpleNamespace(
        id=day_id,
        day_number=3,
        tasks=[
            SimpleNamespace(
                id=task1_id,
                title="Task 1",
                estimated_time=10,
                display_order=1,
                sub_tasks=[
                    SimpleNamespace(id=sub1_id, content_type=ContentType.TEXT, content="A", duration=None, display_order=1, source_text_id=None, pecha_segment_id=None, segment_id=None),
                ],
            ),
            SimpleNamespace(
                id=task2_id,
                title="Task 2",
                estimated_time=5,
                display_order=2,
                sub_tasks=[
                    SimpleNamespace(id=sub2_id, content_type=ContentType.AUDIO, content="B", duration=None, display_order=1, source_text_id=None, pecha_segment_id=None, segment_id=None),
                ],
            ),
        ],
    )

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_day_with_tasks_and_subtasks",
        return_value=plan_item,
    ), patch(
        "pecha_api.plans.users.plan_users_service.is_day_completed",
        return_value=True,
    ) as mock_day_completed, patch(
        "pecha_api.plans.users.plan_users_service.get_user_task_completions_by_user_id_and_task_ids",
        return_value=[SimpleNamespace(task_id=task1_id)],
    ) as mock_task_completions, patch(
        "pecha_api.plans.users.plan_users_service.get_user_subtask_completions_by_user_id_and_sub_task_ids",
        return_value=[SimpleNamespace(sub_task_id=sub1_id)],
    ) as mock_subtask_completions:
        result = get_user_plan_day_details_service(token="tok", plan_id=plan_id, day_number=3)

        # Top-level day details
        assert result.id == day_id
        assert result.day_number == 3
        assert result.is_completed is True

        # Tasks mapping and completion flags
        assert len(result.tasks) == 2
        assert result.tasks[0].id == task1_id
        assert result.tasks[0].title == "Task 1"
        assert result.tasks[0].display_order == 1
        assert result.tasks[0].is_completed is True
        assert result.tasks[1].is_completed is False

        # Sub-tasks mapping and completion flags
        assert len(result.tasks[0].sub_tasks) == 1
        assert result.tasks[0].sub_tasks[0].id == sub1_id
        assert result.tasks[0].sub_tasks[0].is_completed is True

        assert len(result.tasks[1].sub_tasks) == 1
        assert result.tasks[1].sub_tasks[0].id == sub2_id
        assert result.tasks[1].sub_tasks[0].is_completed is False

        # Verify helper invocations
        mock_day_completed.assert_called_once_with(db=db_mock, user_id=user_id, day_id=day_id)
        mock_task_completions.assert_called_once()
        assert mock_task_completions.call_args.kwargs["db"] is db_mock
        assert mock_task_completions.call_args.kwargs["user_id"] == user_id
        assert set(mock_task_completions.call_args.kwargs["task_ids"]) == {task1_id, task2_id}
        mock_subtask_completions.assert_called_once()
        assert mock_subtask_completions.call_args.kwargs["db"] is db_mock
        assert mock_subtask_completions.call_args.kwargs["user_id"] == user_id
        assert set(mock_subtask_completions.call_args.kwargs["sub_task_ids"]) == {sub1_id, sub2_id}


def test_is_completion_helpers_boolean_gateways():
    from pecha_api.plans.users.plan_users_service import is_day_completed

    user_id = uuid.uuid4()
    day_id = uuid.uuid4()

    db_mock = MagicMock()

    # True cases
    with patch(
        "pecha_api.plans.users.plan_users_service.get_user_day_completion_by_user_id_and_day_id",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        assert is_day_completed(db=db_mock, user_id=user_id, day_id=day_id) is True

    # False cases
    with patch(
        "pecha_api.plans.users.plan_users_service.get_user_day_completion_by_user_id_and_day_id",
        return_value=None,
    ):
        assert is_day_completed(db=db_mock, user_id=user_id, day_id=day_id) is False


def test_check_all_subtasks_completed_true():
    from pecha_api.plans.users.plan_users_service import _check_all_subtasks_completed

    user_id = uuid.uuid4()
    task_id = uuid.uuid4()
    sub_a, sub_b = uuid.uuid4(), uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_sub_tasks_by_task_id",
        return_value=[SimpleNamespace(id=sub_a), SimpleNamespace(id=sub_b)],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_uncompleted_user_sub_task_ids",
        return_value=[],
    ):
        assert _check_all_subtasks_completed(user_id=user_id, task_id=task_id) is True


def test_check_all_subtasks_completed_false():
    from pecha_api.plans.users.plan_users_service import _check_all_subtasks_completed

    user_id = uuid.uuid4()
    task_id = uuid.uuid4()
    sub_a, sub_b = uuid.uuid4(), uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_sub_tasks_by_task_id",
        return_value=[SimpleNamespace(id=sub_a), SimpleNamespace(id=sub_b)],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_uncompleted_user_sub_task_ids",
        return_value=[sub_b],
    ):
        assert _check_all_subtasks_completed(user_id=user_id, task_id=task_id) is False


def test_get_user_plan_day_details_service_image_subtask_presigned():
    from pecha_api.plans.users.plan_users_service import get_user_plan_day_details_service
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()
    task_id = uuid.uuid4()
    sub_image_id = uuid.uuid4()

    plan_item = SimpleNamespace(
        id=day_id,
        day_number=1,
        tasks=[
            SimpleNamespace(
                id=task_id,
                title="Task with image subtask",
                estimated_time=5,
                display_order=1,
                sub_tasks=[
                    SimpleNamespace(
                        id=sub_image_id,
                        content_type=ContentType.IMAGE,
                        content="images/subtask/image.png",
                        duration=None,
                        display_order=1,
                        source_text_id=None,
                        pecha_segment_id=None,
                        segment_id=None,
                    )
                ],
            )
        ],
    )

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_day_with_tasks_and_subtasks",
        return_value=plan_item,
    ), patch(
        "pecha_api.plans.users.plan_users_service.is_day_completed",
        return_value=False,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_task_completions_by_user_id_and_task_ids",
        return_value=[],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_subtask_completions_by_user_id_and_sub_task_ids",
        return_value=[],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get",
        return_value="bucket",
    ), patch(
        "pecha_api.plans.users.plan_users_service.generate_presigned_access_url",
        return_value="https://signed.example.com/subtask-image.png",
    ):
        result = get_user_plan_day_details_service(token="tok", plan_id=plan_id, day_number=1)

        assert len(result.tasks) == 1
        assert len(result.tasks[0].sub_tasks) == 1
        sub = result.tasks[0].sub_tasks[0]
        assert sub.id == sub_image_id
        assert sub.content == "https://signed.example.com/subtask-image.png"


def test_unenroll_user_from_plan_success():
    """Test successful unenrollment from a plan"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ) as mock_validate, patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.delete_user_plan_progress",
        return_value=None,
    ) as mock_delete:
        result = unenroll_user_from_plan(token="token123", plan_id=plan_id)

        assert result is None
        mock_validate.assert_called_once_with(token="token123")
        mock_delete.assert_called_once_with(db=db_mock, user_id=user_id, plan_id=plan_id)


def test_unenroll_user_from_plan_deletes_all_completion_records():
    """Test that unenrollment calls delete_user_plan_progress which handles cascade deletion"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ) as mock_validate, patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.delete_user_plan_progress",
        return_value=None,
    ) as mock_delete:
        result = unenroll_user_from_plan(token="token123", plan_id=plan_id)

        assert result is None
        mock_validate.assert_called_once_with(token="token123")
        mock_delete.assert_called_once_with(db=db_mock, user_id=user_id, plan_id=plan_id)


def test_unenroll_user_from_plan_not_enrolled():
    """Test unenrollment when user is not enrolled in the plan"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.delete_user_plan_progress",
        side_effect=HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": f"User is not enrolled in plan with ID {plan_id}"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            unenroll_user_from_plan(token="token123", plan_id=plan_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == "NOT_FOUND"
        assert "not enrolled" in exc_info.value.detail["message"]


def test_unenroll_user_from_plan_invalid_token():
    """Test unenrollment with invalid authentication token"""
    plan_id = uuid.uuid4()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": "Invalid authentication token"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            unenroll_user_from_plan(token="invalid_token", plan_id=plan_id)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error"] == "Unauthorized"


def test_unenroll_user_from_plan_database_error():
    """Test unenrollment when database integrity error occurs"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.delete_user_plan_progress",
        side_effect=HTTPException(
            status_code=400,
            detail={"error": "BAD_REQUEST", "message": "Database integrity error"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            unenroll_user_from_plan(token="token123", plan_id=plan_id)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"] == "BAD_REQUEST"
        assert "integrity error" in exc_info.value.detail["message"]


def test_unenroll_user_from_plan_validates_user_first():
    """Test that user validation happens before database operations"""
    plan_id = uuid.uuid4()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "Unauthorized", "message": "Token expired"}
        ),
    ) as mock_validate, patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
    ) as mock_session, patch(
        "pecha_api.plans.users.plan_users_service.delete_user_plan_progress",
    ) as mock_delete:
        with pytest.raises(HTTPException) as exc_info:
            unenroll_user_from_plan(token="expired_token", plan_id=plan_id)

        mock_validate.assert_called_once_with(token="expired_token")
        
        mock_session.assert_not_called()
        mock_delete.assert_not_called()

        assert exc_info.value.status_code == 401

def test_delete_user_plan_progress_repository_deletes_all_completion_records():
    """Test that delete_user_plan_progress performs all necessary deletions"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    db_mock = MagicMock()
    
    mock_plan_progress = MagicMock()
    mock_plan_progress.user_id = user_id
    mock_plan_progress.plan_id = plan_id
    
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.first.return_value = mock_plan_progress
    mock_query.delete.return_value = 1  # Return count of deleted records
    
    db_mock.query.return_value = mock_query
    
    delete_user_plan_progress(db=db_mock, user_id=user_id, plan_id=plan_id)
    
    assert db_mock.query.call_count >= 4
    
    assert mock_query.delete.call_count >= 3  # At least 3 deletions for task, subtask, day completions
    
    db_mock.delete.assert_called_once_with(mock_plan_progress)
    
    db_mock.commit.assert_called_once()


def test_delete_user_plan_progress_repository_not_enrolled_raises_404():
    """Test that attempting to delete non-existent enrollment raises 404"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    db_mock = MagicMock()
    
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    db_mock.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc_info:
        delete_user_plan_progress(db=db_mock, user_id=user_id, plan_id=plan_id)
    
    assert exc_info.value.status_code == 404
    assert "not enrolled" in str(exc_info.value.detail).lower()
    
    db_mock.delete.assert_not_called()
    db_mock.commit.assert_not_called()


def test_delete_user_plan_progress_repository_integrity_error_rolls_back():
    """Test that database integrity errors trigger rollback"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    db_mock = MagicMock()
    
    mock_plan_progress = MagicMock()
    mock_plan_progress.user_id = user_id
    mock_plan_progress.plan_id = plan_id
    
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_plan_progress
    db_mock.query.return_value = mock_query
    
    db_mock.commit.side_effect = IntegrityError("mock error", None, None)
    
    with pytest.raises(HTTPException) as exc_info:
        delete_user_plan_progress(db=db_mock, user_id=user_id, plan_id=plan_id)
    
    assert exc_info.value.status_code == 400
    assert "integrity error" in str(exc_info.value.detail).lower()
    
    db_mock.rollback.assert_called_once()


def test_delete_user_plan_progress_repository_deletes_in_correct_order():
    """Test that deletions happen in correct order: completions first, then progress"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    db_mock = MagicMock()
    
    mock_plan_progress = MagicMock()
    
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_plan_progress
    
    call_order = []
    
    def track_query(model):
        call_order.append(('query', model.__name__ if hasattr(model, '__name__') else str(model)))
        mock_filter = MagicMock()
        mock_filter.delete.return_value = 1
        result = MagicMock()
        result.filter.return_value = mock_filter
        return result
    
    def track_delete(obj):
        call_order.append(('delete', 'plan_progress'))
    
    def track_commit():
        call_order.append(('commit', None))
    
    db_mock.query.side_effect = track_query
    db_mock.delete.side_effect = track_delete
    db_mock.commit.side_effect = track_commit
    
    delete_user_plan_progress(db=db_mock, user_id=user_id, plan_id=plan_id)
    
    assert ('delete', 'plan_progress') in call_order
    assert ('commit', None) in call_order
    
    delete_index = call_order.index(('delete', 'plan_progress'))
    commit_index = call_order.index(('commit', None))
    assert delete_index < commit_index


def test_delete_user_plan_progress_repository_with_no_completion_records():
    """Test deletion when user has no completion records (edge case)"""
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    db_mock = MagicMock()
    
    mock_plan_progress = MagicMock()
    mock_plan_progress.user_id = user_id
    mock_plan_progress.plan_id = plan_id
    
    mock_progress_query = MagicMock()
    mock_progress_query.filter.return_value.first.return_value = mock_plan_progress
    
    mock_completion_query = MagicMock()
    mock_completion_filter = MagicMock()
    mock_completion_filter.delete.return_value = 0  # No records deleted
    mock_completion_query.filter.return_value = mock_completion_filter
    
    query_call_count = [0]
    
    def query_side_effect(model):
        query_call_count[0] += 1
        if query_call_count[0] == 1:
            return mock_progress_query
        else:
            return mock_completion_query
    
    db_mock.query.side_effect = query_side_effect
    
    delete_user_plan_progress(db=db_mock, user_id=user_id, plan_id=plan_id)
    
    db_mock.delete.assert_called_once_with(mock_plan_progress)
    db_mock.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_plan_days_completion_status_service_success():
    """Test successful retrieval of plan days completion status"""
    from pecha_api.plans.users.plan_users_service import get_user_plan_days_completion_status_service
    
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    day1_id = uuid.uuid4()
    day2_id = uuid.uuid4()
    day3_id = uuid.uuid4()
    
    mock_user = SimpleNamespace(id=user_id)
    
    mock_days = [
        SimpleNamespace(id=day1_id, day_number=1),
        SimpleNamespace(id=day2_id, day_number=2),
        SimpleNamespace(id=day3_id, day_number=3),
    ]
    
    db_mock, session_cm = _mock_session_with_db()
    
    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ) as mock_validate, patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_days_by_plan_id",
        return_value=mock_days,
    ) as mock_get_days, patch(
        "pecha_api.plans.users.plan_users_service.get_completed_day_ids_by_user_id_and_day_ids",
        return_value={day1_id},
    ) as mock_get_completed_day_ids:
        result = await get_user_plan_days_completion_status_service(
            token="token123", plan_id=plan_id
        )
        
        mock_validate.assert_called_once_with(token="token123")
        mock_get_days.assert_called_once_with(db=db_mock, plan_id=plan_id)
        mock_get_completed_day_ids.assert_called_once_with(
            db=db_mock,
            user_id=user_id,
            day_ids=[day1_id, day2_id, day3_id]
        )
        
        assert len(result.days) == 3
        assert result.days[0].day_number == 1
        assert result.days[0].is_completed is True
        assert result.days[1].day_number == 2
        assert result.days[1].is_completed is False
        assert result.days[2].day_number == 3
        assert result.days[2].is_completed is False


@pytest.mark.asyncio
async def test_get_user_plan_days_completion_status_service_all_completed():
    """Test when all days are completed"""
    from pecha_api.plans.users.plan_users_service import get_user_plan_days_completion_status_service
    
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    day1_id = uuid.uuid4()
    day2_id = uuid.uuid4()
    day3_id = uuid.uuid4()
    
    mock_days = [
        SimpleNamespace(id=day1_id, day_number=1),
        SimpleNamespace(id=day2_id, day_number=2),
        SimpleNamespace(id=day3_id, day_number=3),
    ]
    
    db_mock, session_cm = _mock_session_with_db()
    
    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_days_by_plan_id",
        return_value=mock_days,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_completed_day_ids_by_user_id_and_day_ids",
        return_value={day1_id, day2_id, day3_id},
    ):
        result = await get_user_plan_days_completion_status_service(
            token="token123", plan_id=plan_id
        )
        
        assert len(result.days) == 3
        assert all(day.is_completed is True for day in result.days)
