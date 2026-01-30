import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.plans.public.plan_response_models import PublicPlansResponse, PublicPlanDTO, AuthorDTO, PlanDayBasic, PlanDayDTO, TaskDTO, SubTaskDTO,PlanDaysResponse, TagsResponse
from pecha_api.plans.plans_enums import PlanStatus, DifficultyLevel,ContentType
from pecha_api.error_contants import ErrorConstants
from pecha_api.plans.public.plan_views import get_plan_days_list, get_plan_day_content


client = TestClient(api)

class _Creds:
    def __init__(self, token: str):
        self.credentials = token

@pytest.fixture
def sample_author_dto():
    """Sample author DTO for testing."""
    return AuthorDTO(
        id=uuid4(),
        firstname="John",
        lastname="Doe",
        image=None
    )


@pytest.fixture
def sample_plan_dto(sample_author_dto):
    """Sample plan DTO for testing - matches actual PublicPlanDTO model structure."""
    return PublicPlanDTO(
        id=uuid4(),
        title="Introduction to Meditation",
        description="A comprehensive guide to meditation practices",
        language="en",
        difficulty_level=DifficultyLevel.BEGINNER,
        image=None,
        total_days=30,
        tags=["meditation", "mindfulness", "beginner"],
        author=sample_author_dto
    )


@pytest.fixture
def sample_plans_response(sample_plan_dto):
    """Sample plans response for testing."""
    return PublicPlansResponse(
        plans=[sample_plan_dto],
        skip=0,
        limit=20,
        total=1
    )

@pytest.mark.asyncio
async def test_get_plans_success(sample_plans_response):
    """Test successful retrieval of published plans with default language='en'."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response) as mock_service:
        response = client.get("/api/v1/plans")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "plans" in data
        assert "skip" in data
        assert "limit" in data
        assert "total" in data
        assert len(data["plans"]) == 1
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert data["total"] == 1
        
        plan = data["plans"][0]
        assert "id" in plan
        assert plan["title"] == "Introduction to Meditation"
        assert plan["language"] == "en"
        assert plan["total_days"] == 30
        
        assert "author" in plan
        assert plan["author"] is not None
        assert "id" in plan["author"]
        assert plan["author"]["firstname"] == "John"
        assert plan["author"]["lastname"] == "Doe"
        assert "image" in plan["author"]
        
        mock_service.assert_called_once_with(
            search=None,
            language="en",
            sort_by="title",
            sort_order="asc",
            skip=0,
            limit=20
        )


@pytest.mark.asyncio
async def test_get_plans_with_search_filter(sample_plans_response):
    """Test retrieval of plans with search filter and default language='en'."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response) as mock_service:
        response = client.get("/api/v1/plans?search=meditation")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["plans"]) == 1
        
        mock_service.assert_called_once_with(
            search="meditation",
            language="en",
            sort_by="title",
            sort_order="asc",
            skip=0,
            limit=20
        )


@pytest.mark.asyncio
async def test_get_plans_with_language_filter(sample_plans_response):
    """Test retrieval of plans with language filter."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response) as mock_service:
        response = client.get("/api/v1/plans?language=en")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["plans"]) == 1
        
        mock_service.assert_called_once_with(
            search=None,
            language="en",
            sort_by="title",
            sort_order="asc",
            skip=0,
            limit=20
        )


@pytest.mark.asyncio
async def test_get_plans_with_sorting(sample_plans_response):
    """Test retrieval of plans with custom sorting and default language='en'."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response) as mock_service:
        response = client.get("/api/v1/plans?sort_by=subscription_count&sort_order=desc")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["plans"]) == 1
        
        mock_service.assert_called_once_with(
            search=None,
            language="en",
            sort_by="subscription_count",
            sort_order="desc",
            skip=0,
            limit=20
        )


@pytest.mark.asyncio
async def test_get_plans_with_pagination(sample_plans_response):
    """Test retrieval of plans with pagination parameters and default language='en'."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response) as mock_service:
        response = client.get("/api/v1/plans?skip=10&limit=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        mock_service.assert_called_once_with(
            search=None,
            language="en",
            sort_by="title",
            sort_order="asc",
            skip=10,
            limit=5
        )


@pytest.mark.asyncio
async def test_get_plans_with_all_filters(sample_plans_response):
    """Test retrieval of plans with all filter parameters."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response) as mock_service:
        response = client.get(
            "/api/v1/plans?search=meditation&language=en&sort_by=total_days&sort_order=desc&skip=5&limit=10"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        mock_service.assert_called_once_with(
            search="meditation",
            language="en",
            sort_by="total_days",
            sort_order="desc",
            skip=5,
            limit=10
        )


@pytest.mark.asyncio
async def test_get_plans_empty_result():
    """Test retrieval when no plans are found."""
    empty_response = PublicPlansResponse(plans=[], skip=0, limit=20, total=0)
    
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=empty_response):
        response = client.get("/api/v1/plans")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["plans"]) == 0
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_plans_invalid_sort_by(sample_plans_response):
    """Test retrieval with invalid sort_by parameter - endpoint accepts and uses default."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response):
        response = client.get("/api/v1/plans?sort_by=invalid_field")
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_plans_invalid_sort_order(sample_plans_response):
    """Test retrieval with invalid sort_order parameter - endpoint accepts and uses default."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", return_value=sample_plans_response):
        response = client.get("/api/v1/plans?sort_order=invalid_order")
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_plans_negative_skip():
    """Test retrieval with negative skip parameter."""
    response = client.get("/api/v1/plans?skip=-1")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_plans_invalid_limit():
    """Test retrieval with invalid limit parameter (exceeds max)."""
    response = client.get("/api/v1/plans?limit=100")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_plans_service_error():
    """Test handling of service layer errors."""
    with patch("pecha_api.plans.public.plan_views.get_published_plans", side_effect=HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database connection error"
    )):
        response = client.get("/api/v1/plans")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database connection error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_plan_details_success(sample_plan_dto):
    """Test successful retrieval of plan details."""
    plan_id = sample_plan_dto.id
    
    with patch("pecha_api.plans.public.plan_views.get_published_plan", return_value=sample_plan_dto) as mock_service:
        response = client.get(f"/api/v1/plans/{plan_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == str(plan_id)
        assert data["title"] == "Introduction to Meditation"
        assert data["description"] == "A comprehensive guide to meditation practices"
        assert data["language"] == "en"
        assert data["difficulty_level"] == "BEGINNER"
        assert data["total_days"] == 30
        assert data["tags"] == ["meditation", "mindfulness", "beginner"]
        
        assert "author" in data
        assert data["author"]["firstname"] == "John"
        assert data["author"]["lastname"] == "Doe"
        
        assert "image" in data
        assert "image" in data["author"]
        
        mock_service.assert_called_once_with(plan_id=plan_id)


@pytest.mark.asyncio
async def test_get_plan_details_not_found():
    """Test retrieval of non-existent plan."""
    plan_id = uuid4()
    
    with patch("pecha_api.plans.public.plan_views.get_published_plan", side_effect=HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorConstants.PLAN_NOT_FOUND
    )):
        response = client.get(f"/api/v1/plans/{plan_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert ErrorConstants.PLAN_NOT_FOUND in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_plan_details_invalid_uuid():
    """Test retrieval with invalid UUID format."""
    response = client.get("/api/v1/plans/invalid-uuid")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_plan_details_without_author(sample_plan_dto):
    """Test retrieval of plan without author information."""
    plan_dto_no_author = PublicPlanDTO(
        id=uuid4(),
        title="Test Plan",
        description="Test Description",
        language="en",
        difficulty_level=DifficultyLevel.BEGINNER,
        image=None,
        total_days=10,
        tags=[],
        author=None
    )
    
    with patch("pecha_api.plans.public.plan_views.get_published_plan", return_value=plan_dto_no_author):
        response = client.get(f"/api/v1/plans/{plan_dto_no_author.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["author"] is None


@pytest.mark.asyncio
async def test_get_plan_details_service_error():
    """Test handling of service layer errors."""
    plan_id = uuid4()
    
    with patch("pecha_api.plans.public.plan_views.get_published_plan", side_effect=HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch published plan details"
    )):
        response = client.get(f"/api/v1/plans/{plan_id}")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to fetch published plan details" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_plan_days_list_success():
    """Test successful retrieval of plan days list"""
    creds = _Creds(token="valid_token_123")
    plan_id = uuid4()
    
    expected_days = [
        PlanDayBasic(id=str(uuid4()), day_number=1),
        PlanDayBasic(id=str(uuid4()), day_number=2),
    ]
    expected_response = PlanDaysResponse(days=expected_days)

    with patch(
        "pecha_api.plans.public.plan_views.get_plan_days",
        return_value=expected_response,
        new_callable=AsyncMock,
    ) as mock_service:
        response = await get_plan_days_list(
            authentication_credential=creds,
            plan_id=plan_id
        )

        mock_service.assert_called_once_with(
            token="valid_token_123",
            plan_id=plan_id
        )

        assert response == expected_response
        assert len(response.days) == 2
        assert response.days[0].day_number == 1
        assert response.days[1].day_number == 2


@pytest.mark.asyncio
async def test_get_plan_days_list_empty_days():
    """Test retrieval when plan has no days"""
    creds = _Creds(token="valid_token_456")
    plan_id = uuid4()
    
    expected_response = PlanDaysResponse(days=[])

    with patch(
        "pecha_api.plans.public.plan_views.get_plan_days",
        return_value=expected_response,
        new_callable=AsyncMock,
    ) as mock_service:
        response = await get_plan_days_list(
            authentication_credential=creds,
            plan_id=plan_id
        )

        mock_service.assert_called_once_with(
            token="valid_token_456",
            plan_id=plan_id
        )

        assert response == expected_response
        assert len(response.days) == 0

@pytest.mark.asyncio
async def test_get_plan_day_content_success():
    """Test successful retrieval of plan day content"""
    creds = _Creds(token="valid_token_123")
    plan_id = uuid4()
    day_number = 1
    
    expected_subtask = SubTaskDTO(
        id= uuid4(),
        content_type=ContentType.TEXT,
        content="Test subtask content",
        display_order=1
    )
    
    expected_task = TaskDTO(
        id=uuid4(),
        title="Test Task",
        estimated_time=30,
        display_order=1,
        subtasks=[expected_subtask]
    )
    
    expected_response = PlanDayDTO(
        id=uuid4(),
        day_number=day_number,
        tasks=[expected_task]
    )

    with patch(
        "pecha_api.plans.public.plan_views.get_plan_day_details",
        return_value=expected_response,
        new_callable=AsyncMock,
    ) as mock_service:
        response = await get_plan_day_content(
            authentication_credential=creds,
            plan_id=plan_id,
            day_number=day_number
        )

        mock_service.assert_called_once_with(
            token="valid_token_123",
            plan_id=plan_id,
            day_number=day_number
        )

        assert response == expected_response
        assert response.id == expected_response.id
        assert response.day_number == day_number
        assert len(response.tasks) == 1
        
        task = response.tasks[0]
        assert task.id == expected_task.id
        assert task.title == "Test Task"
        assert task.estimated_time == 30
        assert task.display_order == 1
        assert len(task.subtasks) == 1
        
        subtask = task.subtasks[0]
        assert subtask.id == expected_subtask.id
        assert subtask.content_type == ContentType.TEXT
        assert subtask.content == "Test subtask content"
        assert subtask.display_order == 1


@pytest.mark.asyncio
async def test_get_plan_day_content_no_tasks():
    """Test retrieval of plan day with no tasks"""
    creds = _Creds(token="valid_token_456")
    plan_id = uuid4()
    day_number = 2
    
    expected_response = PlanDayDTO(
        id= uuid4(),
        day_number=day_number,
        tasks=[]
    )

    with patch(
        "pecha_api.plans.public.plan_views.get_plan_day_details",
        return_value=expected_response,
        new_callable=AsyncMock,
    ) as mock_service:
        response = await get_plan_day_content(
            authentication_credential=creds,
            plan_id=plan_id,
            day_number=day_number
        )

        mock_service.assert_called_once_with(
            token="valid_token_456",
            plan_id=plan_id,
            day_number=day_number
        )

        assert response == expected_response
        assert response.id == expected_response.id
        assert response.day_number == day_number
        assert len(response.tasks) == 0

@pytest.mark.asyncio
async def test_get_plan_tags_success():
    """Test successful retrieval of plan tags with default language='en'."""
    mock_tags_response = TagsResponse(tags=["meditation", "sleep", "daily"])

    with patch(
        "pecha_api.plans.public.plan_views.get_tags", return_value=mock_tags_response
    ) as mock_service:
        response = client.get("/api/v1/plans/tags")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tags" in data
        assert isinstance(data["tags"], list)
        assert data["tags"] == ["meditation", "sleep", "daily"]

        mock_service.assert_called_once_with(language="en")


@pytest.mark.asyncio
async def test_get_plan_tags_with_language_param():
    """Test retrieval of plan tags with specific language."""
    mock_tags_response = TagsResponse(tags=["煙供", "教學"])

    with patch(
        "pecha_api.plans.public.plan_views.get_tags", return_value=mock_tags_response
    ) as mock_service:
        response = client.get("/api/v1/plans/tags?language=zh")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tags"] == ["煙供", "教學"]

        mock_service.assert_called_once_with(language="zh")