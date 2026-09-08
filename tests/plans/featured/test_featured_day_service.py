import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, Mock
from fastapi import HTTPException
from starlette import status
from datetime import date

from pecha_api.plans.featured.featured_day_service import get_featured_day_service
from pecha_api.plans.featured.featured_day_response_model import PlanDayDTO, TaskDTO, SubTaskDTO
from pecha_api.plans.plans_enums import ContentType


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=None)
    return session


@pytest.fixture
def sample_subtask():
    subtask = MagicMock()
    subtask.id = uuid4()
    subtask.content_type = ContentType.TEXT
    subtask.content = "Practice deep breathing"
    subtask.duration = "12:00"
    subtask.display_order = 1
    return subtask


@pytest.fixture
def sample_task(sample_subtask):
    task = MagicMock()
    task.id = uuid4()
    task.title = "Morning Meditation"
    task.estimated_time = 30
    task.display_order = 1
    task.sub_tasks = [sample_subtask]
    return task


@pytest.fixture
def sample_plan_item(sample_task):
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 15
    plan_item.tasks = [sample_task]
    return plan_item


@pytest.mark.asyncio
async def test_get_featured_day_service_success(sample_plan_item, mock_db_session):
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892 
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[sample_plan_item]) as mock_repo, \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert isinstance(result, PlanDayDTO)
        assert result.id == sample_plan_item.id
        assert result.day_number == 15
        assert len(result.tasks) == 1
        
        task = result.tasks[0]
        assert isinstance(task, TaskDTO)
        assert task.id == sample_plan_item.tasks[0].id
        assert task.title == "Morning Meditation"
        assert task.estimated_time == 30
        assert task.display_order == 1
        assert len(task.subtasks) == 1
        
        subtask = task.subtasks[0]
        assert isinstance(subtask, SubTaskDTO)
        assert subtask.id == sample_plan_item.tasks[0].sub_tasks[0].id
        assert subtask.content_type == ContentType.TEXT
        assert subtask.content == "Practice deep breathing"
        assert subtask.duration == "12:00"
        assert subtask.display_order == 1
        
        mock_repo.assert_called_once_with(mock_db_session.__enter__.return_value, language="EN")
        mock_datetime.now.assert_called_once()


@pytest.mark.asyncio
async def test_get_featured_day_service_multiple_tasks():
    subtask1 = MagicMock()
    subtask1.id = uuid4()
    subtask1.content_type = ContentType.TEXT
    subtask1.content = "Read introduction"
    subtask1.duration = None
    subtask1.display_order = 1
    
    subtask2 = MagicMock()
    subtask2.id = uuid4()
    subtask2.content_type = ContentType.VIDEO
    subtask2.content = "https://video.url/meditation"
    subtask2.duration = None
    subtask2.display_order = 2
    
    task1 = MagicMock()
    task1.id = uuid4()
    task1.title = "Morning Practice"
    task1.estimated_time = 20
    task1.display_order = 1
    task1.sub_tasks = [subtask1, subtask2]
    
    task2 = MagicMock()
    task2.id = uuid4()
    task2.title = "Evening Reflection"
    task2.estimated_time = 15
    task2.display_order = 2
    task2.sub_tasks = []
    
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 7
    plan_item.tasks = [task1, task2]
    
    mock_db_session = MagicMock()
    mock_db_session.__enter__ = Mock(return_value=mock_db_session)
    mock_db_session.__exit__ = Mock(return_value=None)
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]) as mock_repo, \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert result.day_number == 7
        assert len(result.tasks) == 2
        
        assert result.tasks[0].title == "Morning Practice"
        assert len(result.tasks[0].subtasks) == 2
        assert result.tasks[0].subtasks[0].content_type == ContentType.TEXT
        assert result.tasks[0].subtasks[1].content_type == ContentType.VIDEO
        
        assert result.tasks[1].title == "Evening Reflection"
        assert len(result.tasks[1].subtasks) == 0
        
        mock_repo.assert_called_once_with(mock_db_session.__enter__.return_value, language="EN")


@pytest.mark.asyncio
async def test_get_featured_day_service_no_featured_plans(mock_db_session):
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[]) as mock_repo:
        
        with pytest.raises(HTTPException) as exc_info:
            await get_featured_day_service(language="EN")
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "No featured plans with days found"
        
        mock_repo.assert_called_once_with(mock_db_session.__enter__.return_value, language="EN")


@pytest.mark.asyncio
async def test_get_featured_day_service_empty_tasks(mock_db_session):
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 1
    plan_item.tasks = []
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]), \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert result.day_number == 1
        assert result.tasks == []


@pytest.mark.asyncio
async def test_get_featured_day_service_task_sorting():
    task1 = MagicMock()
    task1.id = uuid4()
    task1.title = "Task 3"
    task1.estimated_time = 10
    task1.display_order = 3
    task1.sub_tasks = []
    
    task2 = MagicMock()
    task2.id = uuid4()
    task2.title = "Task 1"
    task2.estimated_time = 20
    task2.display_order = 1
    task2.sub_tasks = []
    
    task3 = MagicMock()
    task3.id = uuid4()
    task3.title = "Task 2"
    task3.estimated_time = 15
    task3.display_order = 2
    task3.sub_tasks = []
    
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 10
    plan_item.tasks = [task1, task2, task3]
    
    mock_db_session = MagicMock()
    mock_db_session.__enter__ = Mock(return_value=mock_db_session)
    mock_db_session.__exit__ = Mock(return_value=None)
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]), \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert len(result.tasks) == 3
        assert result.tasks[0].title == "Task 1"
        assert result.tasks[0].display_order == 1
        assert result.tasks[1].title == "Task 2"
        assert result.tasks[1].display_order == 2
        assert result.tasks[2].title == "Task 3"
        assert result.tasks[2].display_order == 3


@pytest.mark.asyncio
async def test_get_featured_day_service_subtask_sorting():
    subtask1 = MagicMock()
    subtask1.id = uuid4()
    subtask1.content_type = ContentType.TEXT
    subtask1.content = "Subtask 3"
    subtask1.duration = None
    subtask1.display_order = 3
    
    subtask2 = MagicMock()
    subtask2.id = uuid4()
    subtask2.content_type = ContentType.TEXT
    subtask2.content = "Subtask 1"
    subtask2.duration = None
    subtask2.display_order = 1
    
    subtask3 = MagicMock()
    subtask3.id = uuid4()
    subtask3.content_type = ContentType.TEXT
    subtask3.content = "Subtask 2"
    subtask3.duration = None
    subtask3.display_order = 2
    
    task = MagicMock()
    task.id = uuid4()
    task.title = "Practice"
    task.estimated_time = 30
    task.display_order = 1
    task.sub_tasks = [subtask1, subtask2, subtask3]
    
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 5
    plan_item.tasks = [task]
    
    mock_db_session = MagicMock()
    mock_db_session.__enter__ = Mock(return_value=mock_db_session)
    mock_db_session.__exit__ = Mock(return_value=None)
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]), \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert len(result.tasks[0].subtasks) == 3
        assert result.tasks[0].subtasks[0].content == "Subtask 1"
        assert result.tasks[0].subtasks[0].display_order == 1
        assert result.tasks[0].subtasks[1].content == "Subtask 2"
        assert result.tasks[0].subtasks[1].display_order == 2
        assert result.tasks[0].subtasks[2].content == "Subtask 3"
        assert result.tasks[0].subtasks[2].display_order == 3


@pytest.mark.asyncio
async def test_get_featured_day_service_date_based_selection_from_multiple():

    plan_item1 = MagicMock()
    plan_item1.id = uuid4()
    plan_item1.day_number = 1
    plan_item1.tasks = []
    
    plan_item2 = MagicMock()
    plan_item2.id = uuid4()
    plan_item2.day_number = 2
    plan_item2.tasks = []
    
    plan_item3 = MagicMock()
    plan_item3.id = uuid4()
    plan_item3.day_number = 3
    plan_item3.tasks = []
    
    featured_days = [plan_item1, plan_item2, plan_item3]
    
    mock_db_session = MagicMock()
    mock_db_session.__enter__ = Mock(return_value=mock_db_session)
    mock_db_session.__exit__ = Mock(return_value=None)
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=featured_days):
        
        result1 = await get_featured_day_service(language="EN")
        result2 = await get_featured_day_service(language="EN")
        
        assert result1.id == result2.id
        assert result1.day_number == result2.day_number
        
        assert result1.day_number in [1, 2, 3]
        
        assert isinstance(result1, PlanDayDTO)


@pytest.mark.asyncio
async def test_get_featured_day_service_with_all_content_types():
    subtask_text = MagicMock()
    subtask_text.id = uuid4()
    subtask_text.content_type = ContentType.TEXT
    subtask_text.content = "Read instructions"
    subtask_text.duration = None
    subtask_text.display_order = 1
    
    subtask_video = MagicMock()
    subtask_video.id = uuid4()
    subtask_video.content_type = ContentType.VIDEO
    subtask_video.content = "https://video.url"
    subtask_video.duration = None
    subtask_video.display_order = 2
    
    subtask_audio = MagicMock()
    subtask_audio.id = uuid4()
    subtask_audio.content_type = ContentType.AUDIO
    subtask_audio.content = "https://audio.url"
    subtask_audio.duration = None
    subtask_audio.display_order = 3
    
    subtask_image = MagicMock()
    subtask_image.id = uuid4()
    subtask_image.content_type = ContentType.IMAGE
    subtask_image.content = "https://image.url"
    subtask_image.duration = None
    subtask_image.display_order = 4
    
    task = MagicMock()
    task.id = uuid4()
    task.title = "Multimedia Practice"
    task.estimated_time = 45
    task.display_order = 1
    task.sub_tasks = [subtask_text, subtask_video, subtask_audio, subtask_image]
    
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 20
    plan_item.tasks = [task]
    
    mock_db_session = MagicMock()
    mock_db_session.__enter__ = Mock(return_value=mock_db_session)
    mock_db_session.__exit__ = Mock(return_value=None)
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]), \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        subtasks = result.tasks[0].subtasks
        assert len(subtasks) == 4
        assert subtasks[0].content_type == ContentType.TEXT
        assert subtasks[1].content_type == ContentType.VIDEO
        assert subtasks[2].content_type == ContentType.AUDIO
        assert subtasks[3].content_type == ContentType.IMAGE


@pytest.mark.asyncio
async def test_get_featured_day_service_with_optional_fields_none():
    subtask = MagicMock()
    subtask.id = uuid4()
    subtask.content_type = ContentType.TEXT
    subtask.content = None
    subtask.duration = None
    subtask.display_order = None
    
    task = MagicMock()
    task.id = uuid4()
    task.title = None
    task.estimated_time = None
    task.display_order = None
    task.sub_tasks = [subtask]
    
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 10
    plan_item.tasks = [task]
    
    mock_db_session = MagicMock()
    mock_db_session.__enter__ = Mock(return_value=mock_db_session)
    mock_db_session.__exit__ = Mock(return_value=None)
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]), \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert result.tasks[0].title is None
        assert result.tasks[0].estimated_time is None
        assert result.tasks[0].display_order is None
        
        assert result.tasks[0].subtasks[0].content is None
        assert result.tasks[0].subtasks[0].display_order is None


@pytest.mark.asyncio
async def test_get_featured_day_service_database_error(mock_db_session):
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", side_effect=Exception("Database connection error")):
        
        with pytest.raises(Exception) as exc_info:
            await get_featured_day_service(language="EN")
        
        assert str(exc_info.value) == "Database connection error"


@pytest.mark.asyncio
async def test_get_featured_day_service_large_day_number(mock_db_session):
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 365
    plan_item.tasks = []
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]), \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert result.day_number == 365


@pytest.mark.asyncio
async def test_get_featured_day_service_many_subtasks():
    subtasks = []
    for i in range(1, 21):
        subtask = MagicMock()
        subtask.id = uuid4()
        subtask.content_type = ContentType.TEXT
        subtask.content = f"Subtask {i}"
        subtask.duration = None
        subtask.display_order = i
        subtasks.append(subtask)
    
    task = MagicMock()
    task.id = uuid4()
    task.title = "Comprehensive Practice"
    task.estimated_time = 120
    task.display_order = 1
    task.sub_tasks = subtasks
    
    plan_item = MagicMock()
    plan_item.id = uuid4()
    plan_item.day_number = 50
    plan_item.tasks = [task]
    
    mock_db_session = MagicMock()
    mock_db_session.__enter__ = Mock(return_value=mock_db_session)
    mock_db_session.__exit__ = Mock(return_value=None)
    
    mock_date = MagicMock()
    mock_date.toordinal.return_value = 738892
    
    with patch("pecha_api.plans.featured.featured_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.plans.featured.featured_day_service.get_all_featured_plan_days", return_value=[plan_item]), \
         patch("pecha_api.plans.featured.featured_day_service.datetime") as mock_datetime:
        
        mock_datetime.now.return_value.date.return_value = mock_date
        
        result = await get_featured_day_service(language="EN")
        
        assert len(result.tasks[0].subtasks) == 20
        for i, subtask in enumerate(result.tasks[0].subtasks, 1):
            assert subtask.content == f"Subtask {i}"
            assert subtask.display_order == i
