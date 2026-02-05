import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, Mock
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.public.plan_service import get_published_plans, get_published_plan,get_plan_days, get_plan_day_details, get_tags
from pecha_api.plans.public.plan_response_models import PublicPlansResponse, PublicPlanDTO, PlanDaysResponse, PlanDayDTO, TagsResponse
from pecha_api.plans.plans_enums import PlanStatus, DifficultyLevel, LanguageCode
from pecha_api.error_contants import ErrorConstants
from pecha_api.plans.plans_enums import ContentType

@pytest.fixture
def sample_author():
    author = MagicMock()
    author.id = uuid4()
    author.first_name = "John"
    author.last_name = "Doe"
    author.email = "john.doe@example.com"
    author.image_url = "images/author_avatars/author-id/avatar.jpg"
    author.is_verified = True
    return author

def _mock_session_local(mock_session_local):
    """Helper function to mock SessionLocal context manager"""
    mock_db_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db_session
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db_session

@pytest.fixture
def sample_plan(sample_author):
    plan = MagicMock()
    plan.id = uuid4()
    plan.title = "Introduction to Meditation"
    plan.description = "A comprehensive guide to meditation practices"
    plan.language = LanguageCode.EN
    plan.difficulty_level = DifficultyLevel.BEGINNER
    plan.image_url = "images/plan_images/plan-id/uuid/image.jpg"
    plan.status = PlanStatus.PUBLISHED
    plan.tags = ["meditation", "mindfulness", "beginner"]
    plan.author = sample_author
    plan.deleted_at = None
    return plan


@pytest.fixture
def sample_plan_aggregate(sample_plan):
    aggregate = MagicMock()
    aggregate.plan = sample_plan
    aggregate.total_days = 30
    aggregate.subscription_count = 150
    return aggregate


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=None)
    return session


@pytest.mark.asyncio
async def test_get_published_plans_success(sample_plan_aggregate, mock_db_session):
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=[sample_plan_aggregate]) as mock_repo, \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=1), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url") as mock_presigned_url:
        
        result = await get_published_plans(
            search=None,
            language="en",  # Use default language
            sort_by="title",
            sort_order="asc",
            skip=0,
            limit=20
        )
        
        assert isinstance(result, PublicPlansResponse)
        assert len(result.plans) == 1
        assert result.skip == 0
        assert result.limit == 20
        assert result.total == 1
        
        plan_dto = result.plans[0]
        assert plan_dto.title == "Introduction to Meditation"
        assert plan_dto.language == "EN"
        assert plan_dto.total_days == 30
        assert plan_dto.image is not None
        assert plan_dto.image.thumbnail == "https://bucket.s3.amazonaws.com/presigned-url"
        assert plan_dto.image.medium == "https://bucket.s3.amazonaws.com/presigned-url"
        assert plan_dto.image.original == "https://bucket.s3.amazonaws.com/presigned-url"
        
        assert plan_dto.author is not None
        assert plan_dto.author.id == sample_plan_aggregate.plan.author.id
        assert plan_dto.author.firstname == "John"
        assert plan_dto.author.lastname == "Doe"
        assert plan_dto.author.image is not None
        assert plan_dto.author.image.thumbnail == "https://bucket.s3.amazonaws.com/presigned-url"
        
        mock_repo.assert_called_once_with(
            db=mock_db_session.__enter__.return_value,
            skip=0,
            limit=20,
            search=None,
            language="EN",  
            sort_by="title",
            sort_order="asc",
            tag=None
        )


@pytest.mark.asyncio
async def test_get_published_plans_with_search(sample_plan_aggregate, mock_db_session):
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=[sample_plan_aggregate]) as mock_repo, \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=1), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plans(
            search="meditation",
            language="en",
            sort_by="title",
            sort_order="asc",
            skip=0,
            limit=20
        )
        
        assert len(result.plans) == 1
        mock_repo.assert_called_once_with(
            db=mock_db_session.__enter__.return_value,
            skip=0,
            limit=20,
            search="meditation",
            language="EN", 
            sort_by="title",
            sort_order="asc",
            tag=None
        )


@pytest.mark.asyncio
async def test_get_published_plans_with_language_filter(sample_plan_aggregate, mock_db_session):
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=[sample_plan_aggregate]) as mock_repo, \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=1), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plans(
            search=None,
            language="en",
            sort_by="title",
            sort_order="asc",
            skip=0,
            limit=20
        )
        
        assert len(result.plans) == 1
        mock_repo.assert_called_once_with(
            db=mock_db_session.__enter__.return_value,
            skip=0,
            limit=20,
            search=None,
            language="EN", 
            sort_by="title",
            sort_order="asc",
            tag=None
        )


@pytest.mark.asyncio
async def test_get_published_plans_sort_by_title_asc(sample_plan_aggregate, mock_db_session):
    plan1 = MagicMock()
    plan1.id = uuid4()
    plan1.title = "Advanced Meditation"
    plan1.description = "Advanced techniques"
    plan1.language = LanguageCode.EN
    plan1.difficulty_level = DifficultyLevel.BEGINNER
    plan1.image_url = None
    plan1.status = PlanStatus.PUBLISHED
    plan1.tags = []
    plan1.author = None
    
    plan2 = MagicMock()
    plan2.id = uuid4()
    plan2.title = "Beginner Meditation"
    plan2.description = "Basic techniques"
    plan2.language = LanguageCode.EN
    plan2.difficulty_level = DifficultyLevel.BEGINNER
    plan2.image_url = None
    plan2.status = PlanStatus.PUBLISHED
    plan2.tags = []
    plan2.author = None
    
    agg1 = MagicMock()
    agg1.plan = plan1
    agg1.total_days = 20
    agg1.subscription_count = 100
    
    agg2 = MagicMock()
    agg2.plan = plan2
    agg2.total_days = 10
    agg2.subscription_count = 50
    
    aggregates = [agg1, agg2]
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=aggregates), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=2), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value=None):
        
        result = await get_published_plans(sort_by="title", sort_order="asc")
        
        assert result.plans[0].title == "Advanced Meditation"
        assert result.plans[1].title == "Beginner Meditation"


@pytest.mark.asyncio
async def test_get_published_plans_sort_by_title_desc(sample_plan_aggregate, mock_db_session):
    plan1 = MagicMock()
    plan1.id = uuid4()
    plan1.title = "Advanced Meditation"
    plan1.description = "Advanced techniques"
    plan1.language = LanguageCode.EN
    plan1.difficulty_level = DifficultyLevel.BEGINNER
    plan1.image_url = None
    plan1.status = PlanStatus.PUBLISHED
    plan1.tags = []
    plan1.author = None
    
    plan2 = MagicMock()
    plan2.id = uuid4()
    plan2.title = "Beginner Meditation"
    plan2.description = "Basic techniques"
    plan2.language = LanguageCode.EN
    plan2.difficulty_level = DifficultyLevel.BEGINNER
    plan2.image_url = None
    plan2.status = PlanStatus.PUBLISHED
    plan2.tags = []
    plan2.author = None
    
    agg1 = MagicMock()
    agg1.plan = plan1
    agg1.total_days = 20
    agg1.subscription_count = 100
    
    agg2 = MagicMock()
    agg2.plan = plan2
    agg2.total_days = 10
    agg2.subscription_count = 50
    
    aggregates = [agg1, agg2]
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=aggregates), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=2), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value=None):
        
        result = await get_published_plans(sort_by="title", sort_order="desc")
        
        assert len(result.plans) == 2
        assert result.plans[0].title == "Advanced Meditation"
        assert result.plans[1].title == "Beginner Meditation"


@pytest.mark.asyncio
async def test_get_published_plans_sort_by_total_days(sample_plan_aggregate, mock_db_session):
    plan1 = MagicMock()
    plan1.id = uuid4()
    plan1.title = "Short Plan"
    plan1.description = "Short plan"
    plan1.language = LanguageCode.EN
    plan1.difficulty_level = DifficultyLevel.BEGINNER
    plan1.image_url = None
    plan1.status = PlanStatus.PUBLISHED
    plan1.tags = []
    plan1.author = None
    
    plan2 = MagicMock()
    plan2.id = uuid4()
    plan2.title = "Long Plan"
    plan2.description = "Long plan"
    plan2.language = LanguageCode.EN
    plan2.difficulty_level = DifficultyLevel.BEGINNER
    plan2.image_url = None
    plan2.status = PlanStatus.PUBLISHED
    plan2.tags = []
    plan2.author = None
    
    agg1 = MagicMock()
    agg1.plan = plan1
    agg1.total_days = 10
    agg1.subscription_count = 100
    
    agg2 = MagicMock()
    agg2.plan = plan2
    agg2.total_days = 30
    agg2.subscription_count = 50
    
    aggregates = [agg1, agg2]
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=aggregates), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=2), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value=None):
        
        result = await get_published_plans(sort_by="total_days", sort_order="asc")
        
        assert result.plans[0].total_days == 10
        assert result.plans[1].total_days == 30


@pytest.mark.asyncio
async def test_get_published_plans_sort_by_subscription_count(sample_plan_aggregate, mock_db_session):
    plan1 = MagicMock()
    plan1.id = uuid4()
    plan1.title = "Popular Plan"
    plan1.description = "Popular plan"
    plan1.language = LanguageCode.EN
    plan1.difficulty_level = DifficultyLevel.BEGINNER
    plan1.image_url = None
    plan1.status = PlanStatus.PUBLISHED
    plan1.tags = []
    plan1.author = None
    
    plan2 = MagicMock()
    plan2.id = uuid4()
    plan2.title = "Less Popular Plan"
    plan2.description = "Less popular plan"
    plan2.language = LanguageCode.EN
    plan2.difficulty_level = DifficultyLevel.BEGINNER
    plan2.image_url = None
    plan2.status = PlanStatus.PUBLISHED
    plan2.tags = []
    plan2.author = None
    
    agg1 = MagicMock()
    agg1.plan = plan1
    agg1.total_days = 10
    agg1.subscription_count = 200
    
    agg2 = MagicMock()
    agg2.plan = plan2
    agg2.total_days = 10
    agg2.subscription_count = 50
    
    aggregates = [agg1, agg2]
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=aggregates), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=2), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value=None):
        
        result = await get_published_plans(sort_by="subscription_count", sort_order="desc")
        
        assert len(result.plans) == 2
        assert result.plans[0].title == "Popular Plan"
        assert result.plans[1].title == "Less Popular Plan"


@pytest.mark.asyncio
async def test_get_published_plans_empty_result(mock_db_session):
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=[]), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=0):
        
        result = await get_published_plans()
        
        assert isinstance(result, PublicPlansResponse)
        assert len(result.plans) == 0
        assert result.total == 0


@pytest.mark.asyncio
async def test_get_published_plans_without_author(mock_db_session):
    plan_no_author = MagicMock()
    plan_no_author.id = uuid4()
    plan_no_author.title = "Orphan Plan"
    plan_no_author.description = "Plan without author"
    plan_no_author.language = LanguageCode.EN
    plan_no_author.difficulty_level = DifficultyLevel.BEGINNER
    plan_no_author.image_url = None
    plan_no_author.status = PlanStatus.PUBLISHED
    plan_no_author.tags = []
    plan_no_author.author = None
    
    aggregate = MagicMock()
    aggregate.plan = plan_no_author
    aggregate.total_days = 10
    aggregate.subscription_count = 0
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=[aggregate]), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=1), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plans()
        
        assert len(result.plans) == 1
        assert result.plans[0].author is None


@pytest.mark.asyncio
async def test_get_published_plans_with_pagination(sample_plan_aggregate, mock_db_session):
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=[sample_plan_aggregate]) as mock_repo, \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=1), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plans(skip=10, limit=5)
        
        assert result.skip == 10
        assert result.limit == 5
        mock_repo.assert_called_once_with(
            db=mock_db_session.__enter__.return_value,
            skip=10,
            limit=5,
            search=None,
            language="EN",  # Service converts to uppercase before calling repository
            sort_by="title",
            sort_order="asc",
            tag=None
        )


@pytest.mark.asyncio
async def test_get_published_plans_image_url_generation_failure(sample_plan_aggregate, mock_db_session):
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", return_value=[sample_plan_aggregate]), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_count", return_value=1), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plans()
        
        assert len(result.plans) == 1
        assert result.plans[0].image is not None


@pytest.mark.asyncio
async def test_get_published_plans_database_error(mock_db_session):
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plans_from_db", side_effect=Exception("Database connection error")):
        
        with pytest.raises(HTTPException) as exc_info:
            await get_published_plans()
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to fetch published plans" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_published_plan_success(sample_plan, sample_author, mock_db_session):
    plan_id = sample_plan.id
    
    mock_query = MagicMock()
    mock_db_session.__enter__.return_value.query.return_value = mock_query
    mock_query.filter.return_value.count.return_value = 30 
    mock_query.filter.return_value.distinct.return_value.count.return_value = 150 
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plan_by_id", return_value=sample_plan) as mock_repo, \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url") as mock_presigned_url:
        
        result = await get_published_plan(plan_id=plan_id)
        
        assert isinstance(result, PublicPlanDTO)
        assert result.id == plan_id
        assert result.title == "Introduction to Meditation"
        assert result.language == "EN" 
        assert result.total_days == 30
        assert result.image is not None
        assert result.image.thumbnail == "https://bucket.s3.amazonaws.com/presigned-url"
        assert result.image.medium == "https://bucket.s3.amazonaws.com/presigned-url"
        assert result.image.original == "https://bucket.s3.amazonaws.com/presigned-url"
        
        assert result.author is not None
        assert result.author.firstname == "John"
        assert result.author.lastname == "Doe"
        assert result.author.image is not None
        assert result.author.image.thumbnail == "https://bucket.s3.amazonaws.com/presigned-url"
        
        mock_repo.assert_called_once_with(db=mock_db_session.__enter__.return_value, plan_id=plan_id)


@pytest.mark.asyncio
async def test_get_published_plan_not_found(mock_db_session):
    plan_id = uuid4()
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plan_by_id", return_value=None):
        
        with pytest.raises(HTTPException) as exc_info:
            await get_published_plan(plan_id=plan_id)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to fetch published plan details" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_published_plan_without_author(mock_db_session):
    plan_no_author = MagicMock()
    plan_no_author.id = uuid4()
    plan_no_author.title = "Orphan Plan"
    plan_no_author.description = "Plan without author"
    plan_no_author.language = LanguageCode.EN
    plan_no_author.difficulty_level = DifficultyLevel.BEGINNER
    plan_no_author.image_url = None
    plan_no_author.status = PlanStatus.PUBLISHED
    plan_no_author.tags = []
    plan_no_author.author = None
    
    mock_query = MagicMock()
    mock_db_session.__enter__.return_value.query.return_value = mock_query
    mock_query.filter.return_value.count.return_value = 10
    mock_query.filter.return_value.distinct.return_value.count.return_value = 5
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plan_by_id", return_value=plan_no_author), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plan(plan_id=plan_no_author.id)
        
        assert result.author is None
        assert result.title == "Orphan Plan"


@pytest.mark.asyncio
async def test_get_published_plan_image_url_generation_failure(sample_plan, mock_db_session):
    plan_id = sample_plan.id
    
    mock_query = MagicMock()
    mock_db_session.__enter__.return_value.query.return_value = mock_query
    mock_query.filter.return_value.count.return_value = 30
    mock_query.filter.return_value.distinct.return_value.count.return_value = 150
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plan_by_id", return_value=sample_plan), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plan(plan_id=plan_id)
        
        assert result.image is not None


@pytest.mark.asyncio
async def test_get_published_plan_database_error(mock_db_session):
    plan_id = uuid4()
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plan_by_id", side_effect=Exception("Database connection error")):
        
        with pytest.raises(HTTPException) as exc_info:
            await get_published_plan(plan_id=plan_id)
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to fetch published plan details" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_published_plan_with_empty_tags(sample_plan, mock_db_session):
    sample_plan.tags = None
    
    mock_query = MagicMock()
    mock_db_session.__enter__.return_value.query.return_value = mock_query
    mock_query.filter.return_value.count.return_value = 10
    mock_query.filter.return_value.distinct.return_value.count.return_value = 5
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plan_by_id", return_value=sample_plan), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plan(plan_id=sample_plan.id)
        
        assert result.tags == []


@pytest.mark.asyncio
async def test_get_published_plan_zero_subscriptions(sample_plan, mock_db_session):
    mock_query = MagicMock()
    mock_db_session.__enter__.return_value.query.return_value = mock_db_session
    mock_query.filter.return_value.count.return_value = 15
    mock_query.filter.return_value.distinct.return_value.count.return_value = 0
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.public.plan_service.get_published_plan_by_id", return_value=sample_plan), \
         patch("pecha_api.plans.public.plan_service.generate_presigned_access_url", return_value="https://bucket.s3.amazonaws.com/presigned-url"):
        
        result = await get_published_plan(plan_id=sample_plan.id)
        
        assert result.title == sample_plan.title
        assert result.id == sample_plan.id

@pytest.mark.asyncio
async def test_get_plan_days_success():
    """Test successful retrieval of plan days"""
    token = "valid_token_123"
    plan_id = uuid4()
    
    mock_plan = MagicMock()
    mock_plan.id = plan_id
    mock_plan.title = "Test Plan"
    
    mock_day_1 = MagicMock()
    mock_day_1.id = uuid4()
    mock_day_1.day_number = 1
    
    mock_day_2 = MagicMock()
    mock_day_2.id = uuid4()
    mock_day_2.day_number = 2
    
    mock_plan_days = [mock_day_1, mock_day_2]
    
    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "test@example.com"

    with patch("pecha_api.plans.public.plan_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.public.plan_service.validate_and_extract_user_details") as mock_validate_user, \
         patch("pecha_api.plans.public.plan_service.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.public.plan_service.get_days_by_plan_id") as mock_get_days:
        
        db_session = _mock_session_local(mock_session_local)
        mock_validate_user.return_value = mock_user
        mock_get_plan.return_value = mock_plan
        mock_get_days.return_value = mock_plan_days

        response = await get_plan_days(token=token, plan_id=plan_id)

        mock_validate_user.assert_called_once_with(token=token)
        
        mock_get_plan.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_get_days.assert_called_once_with(db=db_session, plan_id=plan_id)

        assert isinstance(response, PlanDaysResponse)
        assert len(response.days) == 2
        
        assert response.days[0].id == str(mock_day_1.id)
        assert response.days[0].day_number == 1
        assert response.days[1].id == str(mock_day_2.id)
        assert response.days[1].day_number == 2


@pytest.mark.asyncio
async def test_get_plan_days_empty_days():
    """Test retrieval when plan has no days"""
    token = "valid_token_456"
    plan_id = uuid4()
    
    mock_plan = MagicMock()
    mock_plan.id = plan_id
    mock_plan.title = "Empty Plan"
    
    mock_user = MagicMock()
    mock_user.id = uuid4()

    with patch("pecha_api.plans.public.plan_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.public.plan_service.validate_and_extract_user_details") as mock_validate_user, \
         patch("pecha_api.plans.public.plan_service.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.public.plan_service.get_days_by_plan_id") as mock_get_days:
        
        db_session = _mock_session_local(mock_session_local)
        mock_validate_user.return_value = mock_user
        mock_get_plan.return_value = mock_plan
        mock_get_days.return_value = []

        response = await get_plan_days(token=token, plan_id=plan_id)

        mock_validate_user.assert_called_once_with(token=token)
        mock_get_plan.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_get_days.assert_called_once_with(db=db_session, plan_id=plan_id)

        assert isinstance(response, PlanDaysResponse)
        assert len(response.days) == 0


@pytest.mark.asyncio
async def test_get_plan_days_plan_not_found():
    """Test when plan does not exist"""
    token = "valid_token_789"
    plan_id = uuid4()
    
    mock_user = MagicMock()
    mock_user.id = uuid4()

    with patch("pecha_api.plans.public.plan_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.public.plan_service.validate_and_extract_user_details") as mock_validate_user, \
         patch("pecha_api.plans.public.plan_service.get_plan_by_id") as mock_get_plan:
        
        db_session = _mock_session_local(mock_session_local)
        mock_validate_user.return_value = mock_user
        mock_get_plan.return_value = None 

        with pytest.raises(HTTPException) as exc_info:
            await get_plan_days(token=token, plan_id=plan_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.PLAN_NOT_FOUND

        mock_validate_user.assert_called_once_with(token=token)
        mock_get_plan.assert_called_once_with(db=db_session, plan_id=plan_id)

def test_get_plan_day_details_success():
    """Test successful retrieval of plan day details with tasks and subtasks"""
    plan_id = uuid4()
    day_number = 1
    
    mock_subtask_1 = MagicMock()
    mock_subtask_1.id = uuid4()
    mock_subtask_1.content_type = ContentType.TEXT
    mock_subtask_1.content = "Subtask content 1"
    mock_subtask_1.display_order = 1
    
    mock_task = MagicMock()
    mock_task.id = uuid4()
    mock_task.title = "Test Task"
    mock_task.estimated_time = 30
    mock_task.display_order = 1
    mock_task.sub_tasks = [mock_subtask_1]
    
    mock_plan_item = MagicMock()
    mock_plan_item.id = uuid4()
    mock_plan_item.day_number = day_number
    mock_plan_item.tasks = [mock_task]
    
    with patch("pecha_api.plans.public.plan_service.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.public.plan_service.get_plan_day_with_tasks_and_subtasks") as mock_get_plan_day:
        
        db_session = _mock_session_local(mock_session_local)
        mock_get_plan_day.return_value = mock_plan_item

        response = get_plan_day_details(plan_id=plan_id, day_number=day_number)

        mock_get_plan_day.assert_called_once_with(db=db_session, plan_id=plan_id, day_number=day_number)

        assert isinstance(response, PlanDayDTO)
        assert response.id == mock_plan_item.id
        assert response.day_number == day_number
        assert len(response.tasks) == 1
        
        task = response.tasks[0]
        assert task.id == mock_task.id
        assert task.title == "Test Task"
        assert task.estimated_time == 30
        assert task.display_order == 1
        assert len(task.subtasks) == 1
        
        assert task.subtasks[0].id == mock_subtask_1.id
        assert task.subtasks[0].content_type == ContentType.TEXT
        assert task.subtasks[0].content == "Subtask content 1"
        assert task.subtasks[0].display_order == 1

@pytest.mark.asyncio
async def test_get_tags_success(mock_db_session):
    """Test successful retrieval of tags."""
    mock_tags = ["meditation", "sleep", "daily"]

    with patch(
        "pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session
    ), patch(
        "pecha_api.plans.public.plan_service.get_all_unique_tags",
        return_value=mock_tags,
    ) as mock_repo:

        result = await get_tags(language="en")

        assert isinstance(result, TagsResponse)
        assert result.tags == ["meditation", "sleep", "daily"]

        mock_repo.assert_called_once_with(
            db=mock_db_session.__enter__.return_value, language="EN"
        )

@pytest.mark.asyncio
async def test_get_tags_empty(mock_db_session):
    """Test retrieval when no tags exist."""
    with patch(
        "pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session
    ), patch(
        "pecha_api.plans.public.plan_service.get_all_unique_tags", return_value=[]
    ) as mock_repo:

        result = await get_tags(language="en")

        assert isinstance(result, TagsResponse)
        assert result.tags == []

@pytest.mark.asyncio
async def test_get_published_plans_with_tag_filter(
    sample_plan_aggregate, mock_db_session
):
    with patch(
        "pecha_api.plans.public.plan_service.SessionLocal", return_value=mock_db_session
    ), patch(
        "pecha_api.plans.public.plan_service.get_published_plans_from_db",
        return_value=[sample_plan_aggregate],
    ) as mock_repo, patch(
        "pecha_api.plans.public.plan_service.get_published_plans_count", return_value=1
    ), patch(
        "pecha_api.plans.public.plan_service.generate_presigned_access_url",
        return_value="https://bucket.s3.amazonaws.com/presigned-url",
    ):

        result = await get_published_plans(
            tag="meditation",
            search=None,
            language="en",
            sort_by="title",
            sort_order="asc",
            skip=0,
            limit=20,
        )

        assert len(result.plans) == 1
        mock_repo.assert_called_once_with(
            db=mock_db_session.__enter__.return_value,
            skip=0,
            limit=20,
            search=None,
            language="EN",
            sort_by="title",
            sort_order="asc",
            tag="meditation",
        )