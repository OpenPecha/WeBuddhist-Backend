import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi import HTTPException
from pecha_api.plans.notifications.day_notification_response_models import (
    CreateNotificationRequest,
    UpdateNotificationRequest,
    NotificationDTO,
)
from pecha_api.plans.notifications.day_notification_service import (
    create_day_notification,
    get_day_notification,
    update_day_notification,
    delete_day_notification,
    _generate_notification_image_url,
    _notification_to_dto,
)
from pecha_api.plans.notifications.day_notification_models import ImageTypeEnum
from pecha_api.plans.response_message import (
    BAD_REQUEST,
    NOTIFICATION_ALREADY_EXISTS,
    NOTIFICATION_NOT_FOUND,
    PLAN_DAY_NOT_FOUND,
    PLAN_NOT_FOUND,
)


# ==================== CREATE NOTIFICATION TESTS ====================


def test_create_day_notification_success():
    """Test successful notification creation with valid authentication and all fields."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    author_email = "author@example.com"
    
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
        image_type="PLAN",
        image_url="images/notifications/test.jpg",
    )
    
    mock_author = SimpleNamespace(
        id=uuid.uuid4(),
        email=author_email,
    )
    
    mock_plan_item = SimpleNamespace(
        id=day_id,
        plan_id=plan_id,
    )
    
    mock_plan = SimpleNamespace(
        id=plan_id,
        group_id=uuid.uuid4(),
        status="DRAFT",
    )
    
    mock_created_notification = SimpleNamespace(
        id=notification_id,
        day_id=day_id,
        title=request.title,
        body=request.body,
        image_type=ImageTypeEnum.PLAN,
        image_url=request.image_url,
        created_at=datetime.now(),
        updated_at=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ) as mock_validate, patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ) as mock_get_item, patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ) as mock_get_plan, patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ) as mock_require, patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=None,
    ) as mock_get_existing, patch(
        "pecha_api.plans.notifications.day_notification_service.create_notification",
        return_value=mock_created_notification,
    ) as mock_create, patch(
        "pecha_api.plans.notifications.day_notification_service.generate_presigned_access_url",
        return_value="https://s3.amazonaws.com/presigned-url",
    ) as mock_presign, patch(
        "pecha_api.plans.notifications.day_notification_service.get",
        return_value="test-bucket",
    ):
        result = create_day_notification(
            token="valid_token_123",
            day_id=day_id,
            request=request,
        )
        
        assert mock_validate.call_count == 1
        assert mock_get_item.call_count == 1
        assert mock_get_plan.call_count == 1
        assert mock_require.call_count == 1
        assert mock_get_existing.call_count == 1
        assert mock_create.call_count == 1
        
        assert isinstance(result, NotificationDTO)
        assert result.id == notification_id
        assert result.day_id == day_id
        assert result.title == request.title
        assert result.body == request.body
        assert result.image_type == "PLAN"


def test_create_day_notification_invalid_token():
    """Test notification creation fails with invalid authentication token."""
    day_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
    )
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid token"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            create_day_notification(
                token="invalid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 401


def test_create_day_notification_day_not_found():
    """Test notification creation fails when plan day doesn't exist."""
    day_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            create_day_notification(
                token="valid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == PLAN_DAY_NOT_FOUND


def test_create_day_notification_plan_not_found():
    """Test notification creation fails when plan doesn't exist."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            create_day_notification(
                token="valid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == PLAN_NOT_FOUND


def test_create_day_notification_already_exists():
    """Test notification creation fails when notification already exists for the day."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_existing_notification = SimpleNamespace(id=uuid.uuid4(), day_id=day_id)
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=mock_existing_notification,
    ):
        with pytest.raises(HTTPException) as exc_info:
            create_day_notification(
                token="valid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == NOTIFICATION_ALREADY_EXISTS


def test_create_day_notification_invalid_image_type():
    """Test notification creation fails with invalid image_type enum value."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
        image_type="INVALID_TYPE",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            create_day_notification(
                token="valid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid image_type" in exc_info.value.detail["message"]


def test_create_day_notification_with_custom_image():
    """Test notification creation with custom image type and URL."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
        image_type="CUSTOM",
        image_url="images/notifications/custom.jpg",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_created_notification = SimpleNamespace(
        id=notification_id,
        day_id=day_id,
        title=request.title,
        body=request.body,
        image_type=ImageTypeEnum.CUSTOM,
        image_url=request.image_url,
        created_at=datetime.now(),
        updated_at=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=None,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.create_notification",
        return_value=mock_created_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.generate_presigned_access_url",
        return_value="https://s3.amazonaws.com/custom-presigned-url",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get",
        return_value="test-bucket",
    ):
        result = create_day_notification(
            token="valid_token",
            day_id=day_id,
            request=request,
        )
        
        assert result.image_type == "CUSTOM"
        assert result.image_url == "https://s3.amazonaws.com/custom-presigned-url"


# ==================== GET NOTIFICATION TESTS ====================


def test_get_day_notification_success():
    """Test successful notification retrieval with presigned URL generation."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_notification = SimpleNamespace(
        id=notification_id,
        day_id=day_id,
        title="Daily Reminder",
        body="Complete your meditation practice",
        image_type=ImageTypeEnum.PLAN,
        image_url="images/notifications/test.jpg",
        created_at=datetime.now(),
        updated_at=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=mock_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.generate_presigned_access_url",
        return_value="https://s3.amazonaws.com/presigned-url",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get",
        return_value="test-bucket",
    ):
        result = get_day_notification(
            token="valid_token",
            day_id=day_id,
        )
        
        assert isinstance(result, NotificationDTO)
        assert result.id == notification_id
        assert result.day_id == day_id
        assert result.title == "Daily Reminder"
        assert result.image_url == "https://s3.amazonaws.com/presigned-url"


def test_get_day_notification_invalid_token():
    """Test notification retrieval fails with invalid authentication token."""
    day_id = uuid.uuid4()
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid token"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_day_notification(
                token="invalid_token",
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 401


def test_get_day_notification_not_found():
    """Test notification retrieval fails when notification doesn't exist."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_day_notification(
                token="valid_token",
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == NOTIFICATION_NOT_FOUND


def test_get_day_notification_presigned_url_error():
    """Test notification retrieval handles S3 presigned URL generation errors gracefully."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_notification = SimpleNamespace(
        id=notification_id,
        day_id=day_id,
        title="Daily Reminder",
        body="Complete your meditation practice",
        image_type=ImageTypeEnum.PLAN,
        image_url="images/notifications/test.jpg",
        created_at=datetime.now(),
        updated_at=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=mock_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.generate_presigned_access_url",
        side_effect=Exception("S3 error"),
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get",
        return_value="test-bucket",
    ):
        result = get_day_notification(
            token="valid_token",
            day_id=day_id,
        )
        
        assert result.image_url is None


# ==================== UPDATE NOTIFICATION TESTS ====================


def test_update_day_notification_success():
    """Test successful notification update with partial fields."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    request = UpdateNotificationRequest(
        title="Updated Reminder",
        body="Updated meditation practice",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_existing_notification = SimpleNamespace(
        id=notification_id,
        day_id=day_id,
        title="Old Title",
        body="Old Body",
    )
    mock_updated_notification = SimpleNamespace(
        id=notification_id,
        day_id=day_id,
        title=request.title,
        body=request.body,
        image_type=ImageTypeEnum.PLAN,
        image_url="images/notifications/test.jpg",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=mock_existing_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.update_notification",
        return_value=mock_updated_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.generate_presigned_access_url",
        return_value="https://s3.amazonaws.com/presigned-url",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get",
        return_value="test-bucket",
    ):
        result = update_day_notification(
            token="valid_token",
            day_id=day_id,
            request=request,
        )
        
        assert isinstance(result, NotificationDTO)
        assert result.title == request.title
        assert result.body == request.body


def test_update_day_notification_invalid_token():
    """Test notification update fails with invalid authentication token."""
    day_id = uuid.uuid4()
    request = UpdateNotificationRequest(title="Updated Reminder")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid token"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            update_day_notification(
                token="invalid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 401


def test_update_day_notification_not_found():
    """Test notification update fails when notification doesn't exist."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    request = UpdateNotificationRequest(title="Updated Reminder")
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            update_day_notification(
                token="valid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == NOTIFICATION_NOT_FOUND


def test_update_day_notification_invalid_image_type():
    """Test notification update fails with invalid image_type enum value."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    request = UpdateNotificationRequest(
        title="Updated Reminder",
        image_type="INVALID_TYPE",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_existing_notification = SimpleNamespace(id=uuid.uuid4(), day_id=day_id)
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=mock_existing_notification,
    ):
        with pytest.raises(HTTPException) as exc_info:
            update_day_notification(
                token="valid_token",
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid image_type" in exc_info.value.detail["message"]


def test_update_day_notification_all_fields():
    """Test notification update with all fields including image_type and image_url."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    request = UpdateNotificationRequest(
        title="Updated Reminder",
        body="Updated meditation practice",
        image_type="CUSTOM",
        image_url="images/notifications/updated.jpg",
    )
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_existing_notification = SimpleNamespace(id=notification_id, day_id=day_id)
    mock_updated_notification = SimpleNamespace(
        id=notification_id,
        day_id=day_id,
        title=request.title,
        body=request.body,
        image_type=ImageTypeEnum.CUSTOM,
        image_url=request.image_url,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=mock_existing_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.update_notification",
        return_value=mock_updated_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.generate_presigned_access_url",
        return_value="https://s3.amazonaws.com/updated-presigned-url",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get",
        return_value="test-bucket",
    ):
        result = update_day_notification(
            token="valid_token",
            day_id=day_id,
            request=request,
        )
        
        assert result.image_type == "CUSTOM"
        assert result.image_url == "https://s3.amazonaws.com/updated-presigned-url"


# ==================== DELETE NOTIFICATION TESTS ====================


def test_delete_day_notification_success():
    """Test successful notification deletion."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    mock_existing_notification = SimpleNamespace(id=uuid.uuid4(), day_id=day_id)
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=mock_existing_notification,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.delete_notification",
    ) as mock_delete:
        result = delete_day_notification(
            token="valid_token",
            day_id=day_id,
        )
        
        assert mock_delete.call_count == 1
        assert result is None


def test_delete_day_notification_invalid_token():
    """Test notification deletion fails with invalid authentication token."""
    day_id = uuid.uuid4()
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid token"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_day_notification(
                token="invalid_token",
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 401


def test_delete_day_notification_not_found():
    """Test notification deletion fails when notification doesn't exist."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="DRAFT")
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_notification_by_day_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_day_notification(
                token="valid_token",
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == NOTIFICATION_NOT_FOUND


def test_delete_day_notification_unauthorized():
    """Test notification deletion fails when user is not authorized."""
    day_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    mock_author = SimpleNamespace(id=uuid.uuid4(), email="author@example.com")
    mock_plan_item = SimpleNamespace(id=day_id, plan_id=plan_id)
    mock_plan = SimpleNamespace(id=plan_id, group_id=uuid.uuid4(), status="PUBLISHED")
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.notifications.day_notification_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_item_by_id",
        return_value=mock_plan_item,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.get_plan_by_id",
        return_value=mock_plan,
    ), patch(
        "pecha_api.plans.notifications.day_notification_service.require_can_edit_content",
        side_effect=HTTPException(
            status_code=403,
            detail={"error": "FORBIDDEN", "message": "You are not authorized to delete this notification"}
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_day_notification(
                token="valid_token",
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 403
