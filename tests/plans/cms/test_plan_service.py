import uuid
import pytest
from unittest.mock import patch, MagicMock, ANY
from fastapi import HTTPException
from datetime import datetime, timezone

import pecha_api.plans.cms.cms_plans_service as plans_service
from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus, ContentType
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.plans_response_models import (
    CreatePlanRequest, UpdatePlanRequest, PlanStatusUpdate,
    PlanDTO,PlanWithAggregates, PlansRepositoryResponse, AuthorDTO
)
from pecha_api.plans.cms.cms_plans_service import (
    create_new_plan, get_filtered_plans, get_details_plan,
    update_plan_details, update_selected_plan_status, delete_selected_plan, get_plan_day_details,
    DUMMY_PLANS, DUMMY_DAYS
)


def _mock_session_local(mock_session_local):
    mock_db_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db_session
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db_session


def test_create_new_plan_success():
    request = CreatePlanRequest(
        title="Mindfulness Basics",
        description="A simple plan to get started with mindfulness.",
        difficulty_level=DifficultyLevel.BEGINNER,
        total_days=7,
        language="en",
        image_url="https://example.com/image.jpg",
        tags=["mindfulness", "beginner"],
    )

    saved_plan = MagicMock()
    saved_plan.id = uuid.uuid4()
    saved_plan.title = request.title
    saved_plan.description = request.description
    saved_plan.difficulty_level = request.difficulty_level
    saved_plan.image_url = request.image_url
    saved_plan.tags = request.tags
    saved_plan.language = request.language
    saved_plan.status = PlanStatus.DRAFT

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.save_plan") as mock_save_plan, \
        patch("pecha_api.plans.cms.cms_plans_service.save_plan_items") as mock_save_plan_items, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_progress") as mock_get_plan_progress, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        db_session = _mock_session_local(mock_session_local)
        mock_save_plan.return_value = saved_plan
        # save_plan_items returns the list of saved items; return a list sized to total_days
        mock_save_plan_items.return_value = [MagicMock() for _ in range(request.total_days)]
        mock_get_plan_progress.return_value = []

        author = MagicMock()
        author.id = uuid.uuid4()
        author.email = "author@example.com"
        author.is_admin = False
        mock_validate_author.return_value = author

        response = create_new_plan(token="dummy", create_plan_request=request)

        mock_validate_author.assert_called_once_with(token="dummy")
        mock_get_plan_progress.assert_called_once_with(db=db_session, plan_id=saved_plan.id)

        # verify repository interactions - plan
        mock_save_plan.assert_called_once_with(db=db_session, plan=ANY)
        called_kwargs = mock_save_plan.call_args.kwargs
        created_plan_model = called_kwargs["plan"]
        assert created_plan_model.title == request.title
        assert created_plan_model.description == request.description
        assert created_plan_model.image_url == request.image_url
        assert created_plan_model.author_id is not None and str(created_plan_model.author_id) != ""

        # verify repository interactions - plan items (bulk)
        mock_save_plan_items.assert_called_once_with(db=db_session, plan_items=ANY)
        called_item_kwargs = mock_save_plan_items.call_args.kwargs
        created_plan_items = called_item_kwargs["plan_items"]
        assert isinstance(created_plan_items, list)
        assert len(created_plan_items) == request.total_days
        # verify each generated PlanItem model
        expected_days = list(range(1, request.total_days + 1))
        actual_days = [item.day_number for item in created_plan_items]
        assert actual_days == expected_days
        assert all(item.plan_id == saved_plan.id for item in created_plan_items)
        assert all(item.created_by == author.email for item in created_plan_items)

        # verify response mapping
        assert response is not None
        assert response.id == saved_plan.id
        assert response.title == request.title
        assert response.description == request.description
        assert response.image_url == request.image_url
        assert response.total_days == request.total_days
        assert response.status == PlanStatus.DRAFT
        assert response.subscription_count == 0



@pytest.mark.asyncio
async def test_get_filtered_plans_success():
    plan1 = Plan(
        id=uuid.uuid4(),
        title="Plan One",
        description="Description One",
        image_url="https://example.com/one.jpg",
        status=PlanStatus.PUBLISHED,
        author_id=uuid.uuid4(),
        created_by="tester@example.com",
    )

    plan2 = Plan(
        id=uuid.uuid4(),
        title="Plan Two",
        description="Description Two",
        language="en",
        image_url="https://example.com/two.jpg",
        status=PlanStatus.DRAFT,
        author_id=uuid.uuid4(),
        created_by="tester@example.com",
    )

    # Repository now returns PlansRepositoryResponse with PlanWithAggregates items
    repo_response = PlansRepositoryResponse(
        plan_info=[
            PlanWithAggregates(plan=plan1, total_days=5, subscription_count=2),
            PlanWithAggregates(plan=plan2, total_days=0, subscription_count=0),
        ],
        total=2,
    )

    # attach minimal author relation attributes used by service when mapping AuthorDTO
    plan1.author = MagicMock()
    plan1.author.first_name = "A"
    plan1.author.last_name = "Author"
    plan1.author.image_url = "authors/a.jpg"
    plan2.author = MagicMock()
    plan2.author.first_name = "B"
    plan2.author.last_name = "Author"
    plan2.author.image_url = "authors/b.jpg"

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plans_by_author_id") as mock_get_plans_by_author_id, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
        patch("pecha_api.plans.cms.cms_plans_service.generate_presigned_access_url") as mock_presign, \
        patch("pecha_api.plans.cms.cms_plans_service.get") as mock_get_config:
        db_session = _mock_session_local(mock_session_local)
        mock_get_plans_by_author_id.return_value = repo_response
        # author.id is used in service to pass author_id to repository
        mock_author = MagicMock(id=uuid.uuid4(), is_admin=False)
        mock_validate_author.return_value = mock_author
        # Return the original key so assertions comparing to plan.image_url still pass
        mock_presign.side_effect = lambda bucket_name, s3_key: s3_key
        mock_get_config.return_value = "dummy-bucket"

        resp = await get_filtered_plans(
            token="dummy-token",
            search="plan",
            sort_by="created_at",
            sort_order="desc",
            skip=5,
            limit=10,
        )

        mock_validate_author.assert_called_once_with(token="dummy-token")

        # verify repository interaction
        mock_get_plans_by_author_id.assert_called_once()
        called_kwargs = mock_get_plans_by_author_id.call_args.kwargs
        assert called_kwargs == {
            "db": db_session,
            "author_id": mock_author.id,
            "is_admin": False,
            "search": "plan",
            "sort_by": "created_at",
            "sort_order": "desc",
            "skip": 5,
            "limit": 10,
        }

        # verify response mapping
        assert resp is not None
        assert resp.skip == 5
        assert resp.limit == 10
        assert resp.total == 2
        assert len(resp.plans) == 2

        p1 = resp.plans[0]
        assert p1.id == plan1.id
        assert p1.title == plan1.title
        assert p1.description == plan1.description
        assert p1.image_url == plan1.image_url
        assert p1.total_days == 5
        assert p1.status == PlanStatus.PUBLISHED
        assert p1.subscription_count == 2
        # language fallback to default when missing on plan
        assert p1.language == "EN"
        # author DTO mapping
        assert p1.author == AuthorDTO(
            id=plan1.author_id,
            firstname="A",
            lastname="Author",
            image_url=plan1.author.image_url,
        )

        p2 = resp.plans[1]
        assert p2.id == plan2.id
        assert p2.status == PlanStatus.DRAFT
        # language preserved when provided on plan
        assert p2.language == "en"
        assert p2.author == AuthorDTO(
            id=plan2.author_id,
            firstname="B",
            lastname="Author",
            image_url=plan2.author.image_url,
        )


@pytest.mark.asyncio
async def test_get_details_plan_success():
    plan = Plan(
        id=uuid.uuid4(),
        title="Test Plan",
        description="Test Description",
        image_url="https://example.com/image.jpg",
        status=PlanStatus.PUBLISHED,
        author_id=uuid.uuid4(),
        created_by="tester@example.com",
    )
    # Ensure required fields used by service/DTO are present
    plan.difficulty_level = "BEGINNER"
    plan.tags = ["mindfulness"]

    item1 = PlanItem(id=uuid.uuid4(), plan_id=plan.id, day_number=1, created_by="tester@example.com")
    item2 = PlanItem(id=uuid.uuid4(), plan_id=plan.id, day_number=2, created_by="tester@example.com")

    task1 = PlanTask(
        id=uuid.uuid4(),
        plan_item_id=item1.id,
        title="Morning Practice",
        display_order=1,
        estimated_time=10,
        created_by="tester@example.com",
    )
    task2 = PlanTask(
        id=uuid.uuid4(),
        plan_item_id=item2.id,
        title="Listen Audio",
        display_order=1,
        estimated_time=20,
        created_by="tester@example.com",
    )

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan_by_id, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_plan_items_by_plan_id, \
        patch("pecha_api.plans.cms.cms_plans_service.get_tasks_by_item_ids") as mock_get_tasks_by_item_ids, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
        patch("pecha_api.plans.cms.cms_plans_service.generate_presigned_access_url") as mock_presign, \
        patch("pecha_api.plans.cms.cms_plans_service.get") as mock_get_config:
        db_session = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = MagicMock(is_admin=False)
        mock_get_plan_by_id.return_value = plan
        mock_get_plan_items_by_plan_id.return_value = [item1, item2]
        mock_get_tasks_by_item_ids.return_value = [task1, task2]
        mock_presign.side_effect = lambda bucket_name, s3_key: s3_key
        mock_get_config.return_value = "dummy-bucket"

        response = await get_details_plan(token="dummy-token", plan_id=plan.id)

        mock_validate_author.assert_called_once_with(token="dummy-token")
        mock_get_plan_by_id.assert_called_once_with(db=db_session, plan_id=plan.id)
        mock_get_plan_items_by_plan_id.assert_called_once_with(db=db_session, plan_id=plan.id)
        mock_get_tasks_by_item_ids.assert_called_once_with(db=db_session, plan_item_ids=[item1.id, item2.id])

        assert response is not None
        assert response.id == plan.id
        assert response.title == plan.title
        assert response.description == plan.description
        assert response.total_days == 2
        assert len(response.days) == 2
        # Image URL should be the same as input since we stub presign to echo key
        assert response.image_url == plan.image_url

        day1 = next(d for d in response.days if d.id == item1.id)
        assert day1.day_number == 1
        assert len(day1.tasks) == 1
        assert day1.tasks[0].id == task1.id
        assert day1.tasks[0].title == task1.title
        assert day1.tasks[0].estimated_time == task1.estimated_time

        day2 = next(d for d in response.days if d.id == item2.id)
        assert day2.day_number == 2
        assert len(day2.tasks) == 1
        assert day2.tasks[0].id == task2.id
        assert day2.tasks[0].estimated_time == task2.estimated_time

@pytest.mark.asyncio
async def test_get_plan_day_details_success():
    plan_id = uuid.uuid4()
    day_number = 3

    subtask1 = MagicMock()
    subtask1.id = uuid.uuid4()
    subtask1.content_type = ContentType.TEXT
    subtask1.content = "Practice for 10 minutes"
    subtask1.display_order = 1

    subtask2 = MagicMock()
    subtask2.id = uuid.uuid4()
    subtask2.content_type = ContentType.AUDIO
    subtask2.content = "https://example.com/audio.mp3"
    subtask2.display_order = 2

    task = MagicMock()
    task.id = uuid.uuid4()
    task.title = "Guided Meditation"
    task.estimated_time = 15
    task.display_order = 1
    task.sub_tasks = [subtask1, subtask2]

    plan_item = MagicMock()
    plan_item.id = uuid.uuid4()
    plan_item.day_number = day_number
    plan_item.tasks = [task]

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_day_with_tasks_and_subtasks") as mock_get_day, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        _ = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = MagicMock()
        mock_get_day.return_value = plan_item

        resp = await get_plan_day_details(token="tkn", plan_id=plan_id, day_number=day_number)

        mock_validate_author.assert_called_once_with(token="tkn")
        mock_get_day.assert_called_once()

        assert resp.id == plan_item.id
        assert resp.day_number == day_number
        assert len(resp.tasks) == 1

        t = resp.tasks[0]
        assert t.id == task.id
        assert t.title == task.title
        assert t.estimated_time == task.estimated_time
        assert t.display_order == task.display_order
        assert len(t.subtasks) == 2
        assert t.subtasks[0].id == subtask1.id
        assert t.subtasks[0].content_type == ContentType.TEXT
        assert t.subtasks[0].content == subtask1.content
        assert t.subtasks[0].display_order == 1
        assert t.subtasks[1].id == subtask2.id
        assert t.subtasks[1].content_type == ContentType.AUDIO
        assert t.subtasks[1].content == subtask2.content
        assert t.subtasks[1].display_order == 2

@pytest.mark.asyncio
async def test_get_plan_day_details_not_found():
    non_existent_plan_id = uuid.uuid4()
    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_day_with_tasks_and_subtasks") as mock_get_day, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        _ = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = MagicMock()
        mock_get_day.side_effect = HTTPException(status_code=404, detail={"error": "Bad request", "message": "Plan day not found"})

        with pytest.raises(HTTPException) as exc_info:
            await get_plan_day_details(token="tkn", plan_id=non_existent_plan_id, day_number=1)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == {"error": "Bad request", "message": "Plan day not found"}
@pytest.mark.asyncio
async def test_get_plan_day_details_no_subtasks():
    plan_id = uuid.uuid4()
    day_number = 2

    task = MagicMock()
    task.id = uuid.uuid4()
    task.title = "Reading Practice"
    task.estimated_time = 5
    task.display_order = 1
    task.sub_tasks = []

    plan_item = MagicMock()
    plan_item.id = uuid.uuid4()
    plan_item.day_number = day_number
    plan_item.tasks = [task]

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_day_with_tasks_and_subtasks") as mock_get_day, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        _ = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = MagicMock()
        mock_get_day.return_value = plan_item

        resp = await get_plan_day_details(token="tkn", plan_id=plan_id, day_number=day_number)

        assert resp.id == plan_item.id
        assert resp.day_number == day_number
        assert len(resp.tasks) == 1
        t = resp.tasks[0]
        assert t.id == task.id
        assert t.title == task.title
        assert t.display_order == task.display_order
        assert t.estimated_time == task.estimated_time
        assert t.subtasks == []
@pytest.mark.asyncio
async def test_get_details_plan_not_found():
    non_existent_id = uuid.uuid4()


    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan_by_id, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        _ = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = MagicMock()
        mock_get_plan_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_details_plan(token="dummy-token", plan_id=non_existent_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == {"error": "Bad request", "message": "Plan not found"}


@pytest.mark.asyncio
async def test_update_plan_details_success():
    plan_id = uuid.uuid4()
    author_email = "author@example.com"
    author_id = uuid.uuid4()
    start_date = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.title = "Original Title"
    mock_plan.description = "Original Description"
    mock_plan.difficulty_level = DifficultyLevel.BEGINNER
    mock_plan.image_url = "images/plan_images/original.jpg"
    mock_plan.tags = ["original"]
    mock_plan.language = MagicMock(value="en")
    mock_plan.status = PlanStatus.DRAFT
    mock_plan.start_date = None
    
    existing_items = [MagicMock(spec=PlanItem, day_number=i) for i in range(1, 6)]
    
    update_request = UpdatePlanRequest(
        title="Updated Title",
        description="Updated Description",
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        image_url="images/plan_images/updated.jpg",
        tags=["updated", "test"],
        total_days=5,
        start_date=start_date,
    )
    
    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.update_plan") as mock_update_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_items, \
         patch("pecha_api.plans.cms.cms_plans_service.generate_presigned_access_url") as mock_presigned_url, \
         patch("pecha_api.plans.cms.cms_plans_service.get") as mock_get_config:
        
        db_session = _mock_session_local(mock_session_local)
        db_session.query.return_value.filter.return_value.scalar.return_value = 10  
        
        mock_author = MagicMock()
        mock_author.email = author_email
        mock_author.id = author_id
        mock_author.is_admin = False
        mock_validate_author.return_value = mock_author
        
        mock_get_plan.return_value = mock_plan
        mock_update_plan.return_value = mock_plan
        mock_get_items.return_value = existing_items
        mock_presigned_url.return_value = "https://s3.amazonaws.com/presigned-url"
        mock_get_config.return_value = "test-bucket"
        
        response = await update_plan_details(
            token="test-token",
            plan_id=plan_id,
            update_plan_request=update_request
        )
        
        mock_validate_author.assert_called_once_with(token="test-token")
        mock_get_plan.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_update_plan.assert_called_once_with(db_session, mock_plan)
        
        assert mock_plan.title == update_request.title
        assert mock_plan.description == update_request.description
        assert mock_plan.difficulty_level == update_request.difficulty_level
        assert mock_plan.image_url == update_request.image_url
        assert mock_plan.tags == update_request.tags
        assert mock_plan.updated_by == author_email
        assert mock_plan.start_date == start_date
        
        assert response.id == plan_id
        assert response.title == update_request.title
        assert response.description == update_request.description
        assert response.difficulty_level == update_request.difficulty_level
        assert response.total_days == 5
        assert response.subscription_count == 10
        assert response.image_url == "https://s3.amazonaws.com/presigned-url"
        assert response.start_date == start_date


@pytest.mark.asyncio
async def test_update_plan_details_cannot_update_start_date_for_published_with_subscribers():
    plan_id = uuid.uuid4()
    author_email = "author@example.com"
    author_id = uuid.uuid4()
    start_date = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.title = "Original Title"
    mock_plan.description = "Original Description"
    mock_plan.difficulty_level = DifficultyLevel.BEGINNER
    mock_plan.image_url = "images/plan_images/original.jpg"
    mock_plan.tags = ["original"]
    mock_plan.language = MagicMock(value="en")
    mock_plan.status = PlanStatus.PUBLISHED
    mock_plan.start_date = None

    update_request = UpdatePlanRequest(start_date=start_date)

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan:

        db_session = _mock_session_local(mock_session_local)
        db_session.query.return_value.filter.return_value.scalar.return_value = 1

        mock_author = MagicMock()
        mock_author.email = author_email
        mock_author.id = author_id
        mock_author.is_admin = False
        mock_validate_author.return_value = mock_author

        mock_get_plan.return_value = mock_plan

        with pytest.raises(HTTPException) as exc:
            await update_plan_details(
                token="test-token",
                plan_id=plan_id,
                update_plan_request=update_request,
            )

        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_update_plan_details_partial_update():
    """Test updating only some fields (partial update)"""
    plan_id = uuid.uuid4()
    author_id = uuid.uuid4()
    
    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.title = "Original Title"
    mock_plan.description = "Original Description"
    mock_plan.difficulty_level = DifficultyLevel.BEGINNER
    mock_plan.image_url = "images/original.jpg"
    mock_plan.tags = ["original"]
    mock_plan.language = MagicMock(value="en")
    mock_plan.status = PlanStatus.DRAFT
    mock_plan.start_date = None
    
    existing_items = [MagicMock(spec=PlanItem, day_number=i) for i in range(1, 6)]
    
    update_request = UpdatePlanRequest(
        title="New Title",
        description="New Description"
    )
    
    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.update_plan") as mock_update_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_items:
        
        db_session = _mock_session_local(mock_session_local)
        db_session.query.return_value.filter.return_value.scalar.return_value = 5
        
        mock_author = MagicMock()
        mock_author.email = "author@example.com"
        mock_author.id = author_id
        mock_author.is_admin = False
        mock_validate_author.return_value = mock_author
        
        mock_get_plan.return_value = mock_plan
        mock_update_plan.return_value = mock_plan
        mock_get_items.return_value = existing_items
        
        response = await update_plan_details(
            token="test-token",
            plan_id=plan_id,
            update_plan_request=update_request
        )
        
        assert mock_plan.title == "New Title"
        assert mock_plan.description == "New Description"
        assert mock_plan.difficulty_level == DifficultyLevel.BEGINNER
        assert mock_plan.image_url == "images/original.jpg"
        assert mock_plan.tags == ["original"]

        assert response.total_days == 5


@pytest.mark.asyncio
async def test_update_plan_details_not_found():
    """Test updating non-existent plan returns 404"""
    non_existent_id = uuid.uuid4()
    update_request = UpdatePlanRequest(title="Updated Title")
    
    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan:
        
        _mock_session_local(mock_session_local)
        
        mock_author = MagicMock()
        mock_validate_author.return_value = mock_author
        
        mock_get_plan.return_value = None  
        
        with pytest.raises(HTTPException) as exc_info:
            await update_plan_details(
                token="test-token",
                plan_id=non_existent_id,
                update_plan_request=update_request
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == {"error": "Bad request", "message": "Plan not found"}


@pytest.mark.asyncio
async def test_update_plan_details_with_image_url_generation():
    """Test that image_url is properly generated with presigned URL"""
    plan_id = uuid.uuid4()
    author_id = uuid.uuid4()
    
    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.title = "Test Plan"
    mock_plan.description = "Test Description"
    mock_plan.difficulty_level = DifficultyLevel.BEGINNER
    mock_plan.image_url = "images/plan_images/test.jpg"
    mock_plan.tags = []
    mock_plan.language = MagicMock(value="en")
    mock_plan.status = PlanStatus.DRAFT
    mock_plan.start_date = None
    
    existing_items = [MagicMock(spec=PlanItem, day_number=1)]
    
    update_request = UpdatePlanRequest(title="Test Plan")
    
    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.update_plan") as mock_update_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_items, \
         patch("pecha_api.plans.cms.cms_plans_service.generate_presigned_access_url") as mock_presigned_url, \
         patch("pecha_api.plans.cms.cms_plans_service.get") as mock_get_config:
        
        db_session = _mock_session_local(mock_session_local)
        db_session.query.return_value.filter.return_value.scalar.return_value = 0
        
        mock_author = MagicMock()
        mock_author.id = author_id
        mock_author.is_admin = False
        mock_validate_author.return_value = mock_author
        
        mock_get_plan.return_value = mock_plan
        mock_update_plan.return_value = mock_plan
        mock_get_items.return_value = existing_items
        
        presigned_url = "https://s3.amazonaws.com/bucket/test.jpg?signature=xyz"
        mock_presigned_url.return_value = presigned_url
        mock_get_config.return_value = "test-bucket"
        
        response = await update_plan_details(
            token="test-token",
            plan_id=plan_id,
            update_plan_request=update_request
        )
        
        mock_get_config.assert_called_with("AWS_BUCKET_NAME")
        mock_presigned_url.assert_called_once_with("test-bucket", "images/plan_images/test.jpg")
        assert response.image_url == presigned_url


@pytest.mark.asyncio
async def test_update_plan_details_image_url_generation_failure():
    """Test that original image_url is used when presigned URL generation fails"""
    plan_id = uuid.uuid4()
    author_id = uuid.uuid4()
    
    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.title = "Test Plan"
    mock_plan.description = "Test Description"
    mock_plan.difficulty_level = DifficultyLevel.BEGINNER
    mock_plan.image_url = "images/plan_images/test.jpg"
    mock_plan.tags = []
    mock_plan.language = MagicMock(value="en")
    mock_plan.status = PlanStatus.DRAFT
    mock_plan.start_date = None
    
    existing_items = [MagicMock(spec=PlanItem, day_number=1)]
    
    update_request = UpdatePlanRequest(title="Test Plan")
    
    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.update_plan") as mock_update_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_items, \
         patch("pecha_api.plans.cms.cms_plans_service.generate_presigned_access_url") as mock_presigned_url, \
         patch("pecha_api.plans.cms.cms_plans_service.get") as mock_get_config:
        
        db_session = _mock_session_local(mock_session_local)
        db_session.query.return_value.filter.return_value.scalar.return_value = 0
        
        mock_author = MagicMock()
        mock_author.id = author_id
        mock_author.is_admin = False
        mock_validate_author.return_value = mock_author
        
        mock_get_plan.return_value = mock_plan
        mock_update_plan.return_value = mock_plan
        mock_get_items.return_value = existing_items
        
        mock_presigned_url.side_effect = Exception("S3 error")
        mock_get_config.return_value = "test-bucket"
        
        response = await update_plan_details(
            token="test-token",
            plan_id=plan_id,
            update_plan_request=update_request
        )
        
        assert response.image_url == "images/plan_images/test.jpg"


@pytest.mark.asyncio
async def test_update_plan_details_no_image_url():
    """Test updating plan with no image_url"""
    plan_id = uuid.uuid4()
    author_id = uuid.uuid4()
    
    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.title = "Test Plan"
    mock_plan.description = "Test Description"
    mock_plan.difficulty_level = DifficultyLevel.BEGINNER
    mock_plan.image_url = None
    mock_plan.tags = []
    mock_plan.language = MagicMock(value="en")
    mock_plan.status = PlanStatus.DRAFT
    mock_plan.start_date = None
    
    existing_items = [MagicMock(spec=PlanItem, day_number=1)]
    
    update_request = UpdatePlanRequest(title="Test Plan")
    
    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.update_plan") as mock_update_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_items:
        
        db_session = _mock_session_local(mock_session_local)
        db_session.query.return_value.filter.return_value.scalar.return_value = 0
        
        mock_author = MagicMock()
        mock_author.id = author_id
        mock_author.is_admin = False
        mock_validate_author.return_value = mock_author
        
        mock_get_plan.return_value = mock_plan
        mock_update_plan.return_value = mock_plan
        mock_get_items.return_value = existing_items
        
        response = await update_plan_details(
            token="test-token",
            plan_id=plan_id,
            update_plan_request=update_request
        )
        
        assert response.image_url is None


@pytest.mark.asyncio
async def test_update_selected_plan_status_success_db_backed():
    plan_id = uuid.uuid4()
    author_id = uuid.uuid4()

    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.title = "Title"
    mock_plan.description = "Desc"
    mock_plan.language = "EN"
    mock_plan.difficulty_level = DifficultyLevel.BEGINNER
    mock_plan.image_url = "images/plan.jpg"
    mock_plan.tags = ["t"]
    mock_plan.status = PlanStatus.DRAFT

    items = [MagicMock(spec=PlanItem), MagicMock(spec=PlanItem)]
    user_progress = [MagicMock(), MagicMock(), MagicMock()]

    status_update = PlanStatusUpdate(status=PlanStatus.PUBLISHED)

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_items, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_progress") as mock_get_progress, \
         patch("pecha_api.plans.cms.cms_plans_service.update_plan") as mock_update_plan, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = MagicMock(id=author_id, is_admin=False)
        mock_get_plan_by_id.return_value = mock_plan
        mock_get_items.return_value = items
        mock_get_progress.return_value = user_progress
        mock_update_plan.return_value = mock_plan

        resp = await update_selected_plan_status(
            token="tkn",
            plan_id=plan_id,
            plan_status_update=status_update,
        )

        mock_get_plan_by_id.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_get_items.assert_called_with(db=db_session, plan_id=plan_id)
        mock_update_plan.assert_called_once_with(db=db_session, plan=mock_plan)

        assert resp.id == plan_id
        assert resp.status == PlanStatus.PUBLISHED
        assert resp.total_days == len(items)
        assert resp.subscription_count == len(user_progress)
        assert resp.image_url == mock_plan.image_url


@pytest.mark.asyncio
async def test_update_selected_plan_status_invalid_transition_no_days():
    plan_id = uuid.uuid4()
    author_id = uuid.uuid4()

    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = author_id
    mock_plan.status = PlanStatus.DRAFT

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_items_by_plan_id") as mock_get_items, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        _ = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = MagicMock(id=author_id, is_admin=False)
        mock_get_plan_by_id.return_value = mock_plan
        mock_get_items.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            await update_selected_plan_status(
                token="tkn",
                plan_id=plan_id,
                plan_status_update=PlanStatusUpdate(status=PlanStatus.PUBLISHED),
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == {"error": "Bad request", "message": "Plan must have at least one day with content to be published"}


@pytest.mark.asyncio
async def test_update_selected_plan_status_not_found():
    plan_id = uuid.uuid4()

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        _ = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = MagicMock(id=uuid.uuid4(), is_admin=False)
        mock_get_plan_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await update_selected_plan_status(
                token="tkn",
                plan_id=plan_id,
                plan_status_update=PlanStatusUpdate(status=PlanStatus.PUBLISHED),
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == {"error": "Bad request", "message": "Plan not found"}


@pytest.mark.asyncio
async def test_update_selected_plan_status_author_mismatch():
    plan_id = uuid.uuid4()

    mock_plan = MagicMock(spec=Plan)
    mock_plan.id = plan_id
    mock_plan.author_id = uuid.uuid4()  # different than caller

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        _ = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = MagicMock(id=uuid.uuid4(), is_admin=False)
        mock_get_plan_by_id.return_value = mock_plan

        with pytest.raises(HTTPException) as exc_info:
            await update_selected_plan_status(
                token="tkn",
                plan_id=plan_id,
                plan_status_update=PlanStatusUpdate(status=PlanStatus.PUBLISHED),
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == {"error": "Bad request", "message": "You are not authorized to update this plan"}


@pytest.mark.asyncio
async def test_delete_selected_plan_success():
    plan_id = uuid.uuid4()
    author = MagicMock()
    author.id = uuid.uuid4()
    author.is_admin = False

    plan = MagicMock(spec=Plan)
    plan.id = plan_id
    plan.author_id = author.id

    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \
        patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id") as mock_get_plan_by_id, \
        patch("pecha_api.plans.cms.cms_plans_service._soft_delete_plan_by_id") as mock_soft_delete, \
        patch("pecha_api.plans.cms.cms_plans_service.validate_and_extract_author_details") as mock_validate_author:
        db_session = _mock_session_local(mock_session_local)
        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan

        await delete_selected_plan(token="dummy-token", plan_id=plan_id)

        mock_validate_author.assert_called_once_with(token="dummy-token")
        mock_get_plan_by_id.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_soft_delete.assert_called_once_with(db=db_session, plan_id=plan_id, author=author)

