import uuid
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from pecha_api.plans.notifications.day_notification_response_models import (
    CreateNotificationRequest,
    UpdateNotificationRequest,
    NotificationDTO,
)
from pecha_api.plans.notifications.day_notification_views import (
    create_notification,
    get_notification,
    update_notification,
    delete_notification,
)


class _Creds:
    def __init__(self, token: str):
        self.credentials = token


# ==================== CREATE NOTIFICATION TESTS ====================


@pytest.mark.asyncio
async def test_create_notification_success():
    """Test successful notification creation with valid authentication."""
    day_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
        image_type="PLAN",
        image_url="images/notifications/test.jpg",
    )
    
    expected = NotificationDTO(
        id=notification_id,
        day_id=day_id,
        title=request.title,
        body=request.body,
        image_type="PLAN",
        image_url="https://s3.amazonaws.com/presigned-url",
        created_at="2024-01-01T00:00:00Z",
        updated_at=None,
    )
    
    creds = _Creds(token="valid_token_123")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.create_day_notification",
        return_value=expected,
    ) as mock_create:
        resp = await create_notification(
            authentication_credential=creds,
            day_id=day_id,
            request=request,
        )
        
        assert mock_create.call_count == 1
        assert mock_create.call_args.kwargs == {
            "token": "valid_token_123",
            "day_id": day_id,
            "request": request,
        }
        assert resp == expected


@pytest.mark.asyncio
async def test_create_notification_invalid_token():
    """Test notification creation fails with invalid authentication token."""
    day_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
    )
    
    creds = _Creds(token="invalid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.create_day_notification",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid authentication token"}
        ),
    ) as mock_create:
        with pytest.raises(HTTPException) as exc_info:
            await create_notification(
                authentication_credential=creds,
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 401
        assert mock_create.call_count == 1


@pytest.mark.asyncio
async def test_create_notification_day_not_found():
    """Test notification creation fails when plan day doesn't exist."""
    day_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
    )
    
    creds = _Creds(token="valid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.create_day_notification",
        side_effect=HTTPException(
            status_code=404,
            detail={"error": "BAD_REQUEST", "message": "Plan day not found"}
        ),
    ) as mock_create:
        with pytest.raises(HTTPException) as exc_info:
            await create_notification(
                authentication_credential=creds,
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail["message"].lower()


@pytest.mark.asyncio
async def test_create_notification_already_exists():
    """Test notification creation fails when notification already exists for the day."""
    day_id = uuid.uuid4()
    request = CreateNotificationRequest(
        title="Daily Reminder",
        body="Complete your meditation practice",
    )
    
    creds = _Creds(token="valid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.create_day_notification",
        side_effect=HTTPException(
            status_code=400,
            detail={"error": "BAD_REQUEST", "message": "Notification already exists for this day"}
        ),
    ) as mock_create:
        with pytest.raises(HTTPException) as exc_info:
            await create_notification(
                authentication_credential=creds,
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail["message"].lower()


# ==================== GET NOTIFICATION TESTS ====================


@pytest.mark.asyncio
async def test_get_notification_success():
    """Test successful notification retrieval with valid authentication."""
    day_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    expected = NotificationDTO(
        id=notification_id,
        day_id=day_id,
        title="Daily Reminder",
        body="Complete your meditation practice",
        image_type="CUSTOM",
        image_url="https://s3.amazonaws.com/presigned-url",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
    )
    
    creds = _Creds(token="valid_token_123")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.get_day_notification",
        return_value=expected,
    ) as mock_get:
        resp = await get_notification(
            authentication_credential=creds,
            day_id=day_id,
        )
        
        assert mock_get.call_count == 1
        assert mock_get.call_args.kwargs == {
            "token": "valid_token_123",
            "day_id": day_id,
        }
        assert resp == expected


@pytest.mark.asyncio
async def test_get_notification_invalid_token():
    """Test notification retrieval fails with invalid authentication token."""
    day_id = uuid.uuid4()
    creds = _Creds(token="invalid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.get_day_notification",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid authentication token"}
        ),
    ) as mock_get:
        with pytest.raises(HTTPException) as exc_info:
            await get_notification(
                authentication_credential=creds,
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 401
        assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_get_notification_not_found():
    """Test notification retrieval fails when notification doesn't exist."""
    day_id = uuid.uuid4()
    creds = _Creds(token="valid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.get_day_notification",
        side_effect=HTTPException(
            status_code=404,
            detail={"error": "BAD_REQUEST", "message": "Notification not found for this day"}
        ),
    ) as mock_get:
        with pytest.raises(HTTPException) as exc_info:
            await get_notification(
                authentication_credential=creds,
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail["message"].lower()


# ==================== UPDATE NOTIFICATION TESTS ====================


@pytest.mark.asyncio
async def test_update_notification_success():
    """Test successful notification update with valid authentication."""
    day_id = uuid.uuid4()
    notification_id = uuid.uuid4()
    
    request = UpdateNotificationRequest(
        title="Updated Reminder",
        body="Updated meditation practice",
        image_type="CUSTOM",
        image_url="images/notifications/updated.jpg",
    )
    
    expected = NotificationDTO(
        id=notification_id,
        day_id=day_id,
        title=request.title,
        body=request.body,
        image_type="CUSTOM",
        image_url="https://s3.amazonaws.com/presigned-url-updated",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-02T00:00:00Z",
    )
    
    creds = _Creds(token="valid_token_123")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.update_day_notification",
        return_value=expected,
    ) as mock_update:
        resp = await update_notification(
            authentication_credential=creds,
            day_id=day_id,
            request=request,
        )
        
        assert mock_update.call_count == 1
        assert mock_update.call_args.kwargs == {
            "token": "valid_token_123",
            "day_id": day_id,
            "request": request,
        }
        assert resp == expected


@pytest.mark.asyncio
async def test_update_notification_invalid_token():
    """Test notification update fails with invalid authentication token."""
    day_id = uuid.uuid4()
    request = UpdateNotificationRequest(
        title="Updated Reminder",
    )
    
    creds = _Creds(token="invalid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.update_day_notification",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid authentication token"}
        ),
    ) as mock_update:
        with pytest.raises(HTTPException) as exc_info:
            await update_notification(
                authentication_credential=creds,
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 401
        assert mock_update.call_count == 1


@pytest.mark.asyncio
async def test_update_notification_not_found():
    """Test notification update fails when notification doesn't exist."""
    day_id = uuid.uuid4()
    request = UpdateNotificationRequest(
        title="Updated Reminder",
    )
    
    creds = _Creds(token="valid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.update_day_notification",
        side_effect=HTTPException(
            status_code=404,
            detail={"error": "BAD_REQUEST", "message": "Notification not found for this day"}
        ),
    ) as mock_update:
        with pytest.raises(HTTPException) as exc_info:
            await update_notification(
                authentication_credential=creds,
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail["message"].lower()


@pytest.mark.asyncio
async def test_update_notification_invalid_image_type():
    """Test notification update fails with invalid image_type enum value."""
    day_id = uuid.uuid4()
    request = UpdateNotificationRequest(
        title="Updated Reminder",
        image_type="INVALID_TYPE",
    )
    
    creds = _Creds(token="valid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.update_day_notification",
        side_effect=HTTPException(
            status_code=400,
            detail={"error": "BAD_REQUEST", "message": "Invalid image_type. Must be 'PLAN' or 'CUSTOM'"}
        ),
    ) as mock_update:
        with pytest.raises(HTTPException) as exc_info:
            await update_notification(
                authentication_credential=creds,
                day_id=day_id,
                request=request,
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid image_type" in exc_info.value.detail["message"]


# ==================== DELETE NOTIFICATION TESTS ====================


@pytest.mark.asyncio
async def test_delete_notification_success():
    """Test successful notification deletion with valid authentication."""
    day_id = uuid.uuid4()
    creds = _Creds(token="valid_token_123")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.delete_day_notification",
        return_value=None,
    ) as mock_delete:
        result = await delete_notification(
            authentication_credential=creds,
            day_id=day_id,
        )
        
        assert mock_delete.call_count == 1
        assert mock_delete.call_args.kwargs == {
            "token": "valid_token_123",
            "day_id": day_id,
        }
        assert result is None


@pytest.mark.asyncio
async def test_delete_notification_invalid_token():
    """Test notification deletion fails with invalid authentication token."""
    day_id = uuid.uuid4()
    creds = _Creds(token="invalid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.delete_day_notification",
        side_effect=HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "Invalid authentication token"}
        ),
    ) as mock_delete:
        with pytest.raises(HTTPException) as exc_info:
            await delete_notification(
                authentication_credential=creds,
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 401
        assert mock_delete.call_count == 1


@pytest.mark.asyncio
async def test_delete_notification_not_found():
    """Test notification deletion fails when notification doesn't exist."""
    day_id = uuid.uuid4()
    creds = _Creds(token="valid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.delete_day_notification",
        side_effect=HTTPException(
            status_code=404,
            detail={"error": "BAD_REQUEST", "message": "Notification not found for this day"}
        ),
    ) as mock_delete:
        with pytest.raises(HTTPException) as exc_info:
            await delete_notification(
                authentication_credential=creds,
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail["message"].lower()


@pytest.mark.asyncio
async def test_delete_notification_unauthorized():
    """Test notification deletion fails when user is not authorized."""
    day_id = uuid.uuid4()
    creds = _Creds(token="valid_token")
    
    with patch(
        "pecha_api.plans.notifications.day_notification_views.delete_day_notification",
        side_effect=HTTPException(
            status_code=403,
            detail={"error": "FORBIDDEN", "message": "You are not authorized to delete this notification"}
        ),
    ) as mock_delete:
        with pytest.raises(HTTPException) as exc_info:
            await delete_notification(
                authentication_credential=creds,
                day_id=day_id,
            )
        
        assert exc_info.value.status_code == 403
        assert "not authorized" in exc_info.value.detail["message"].lower()
