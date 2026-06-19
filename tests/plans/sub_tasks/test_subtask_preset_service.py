import uuid
import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from pecha_api.plans.tasks.sub_tasks.subtask_preset_response_models import (
    PresetRequest,
    PresetResponse,
)
from pecha_api.plans.tasks.sub_tasks.subtask_preset_service import (
    create_or_update_preset_service,
    get_preset_service,
    delete_preset_service,
    _map_to_response,
)


@pytest.mark.asyncio
async def test_create_or_update_preset_service_creates_new_preset():
    """Test creating a new preset when none exists"""
    subtask_id = uuid.uuid4()
    version_id = uuid.uuid4()
    token = "valid_token_123"
    
    request = PresetRequest(
        version_id=str(version_id),
        language="bo"
    )
    
    author = SimpleNamespace(email="author@example.com", id=uuid.uuid4())
    subtask = SimpleNamespace(id=subtask_id)
    
    created_preset = SimpleNamespace(
        id=uuid.uuid4(),
        subtask_id=subtask_id,
        version_id=version_id,
        language="bo",
        created_at=datetime.now(timezone.utc),
        created_by="author@example.com",
        updated_at=None,
        updated_by=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.validate_and_extract_author_details",
        return_value=author,
    ) as mock_validate, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SessionLocal",
        return_value=session_cm,
    ) as mock_session, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_sub_task_by_subtask_id",
        return_value=subtask,
    ) as mock_get_subtask, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_preset_by_subtask_id",
        return_value=None,
    ) as mock_get_preset, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SubTaskPreset",
        return_value=created_preset,
    ) as mock_preset_model, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.create_preset",
        return_value=created_preset,
    ) as mock_create:
        
        resp = await create_or_update_preset_service(
            token=token,
            subtask_id=subtask_id,
            preset_request=request,
        )
        
        assert mock_validate.call_count == 1
        assert mock_validate.call_args.kwargs == {"token": token}
        
        assert mock_get_subtask.call_count == 1
        assert mock_get_subtask.call_args.kwargs == {"db": db_mock, "id": subtask_id}
        
        assert mock_get_preset.call_count == 1
        assert mock_get_preset.call_args.kwargs == {"db": db_mock, "subtask_id": subtask_id}
        
        assert mock_create.call_count == 1
        
        assert resp.subtask_id == str(subtask_id)
        assert resp.version_id == str(version_id)
        assert resp.language == "bo"
        assert resp.created_by == "author@example.com"


@pytest.mark.asyncio
async def test_create_or_update_preset_service_updates_existing_preset():
    """Test updating an existing preset"""
    subtask_id = uuid.uuid4()
    old_version_id = uuid.uuid4()
    new_version_id = uuid.uuid4()
    token = "valid_token_123"
    
    request = PresetRequest(
        version_id=str(new_version_id),
        language="en"
    )
    
    author = SimpleNamespace(email="author@example.com", id=uuid.uuid4())
    subtask = SimpleNamespace(id=subtask_id)
    
    existing_preset = SimpleNamespace(
        id=uuid.uuid4(),
        subtask_id=subtask_id,
        version_id=old_version_id,
        language="bo",
        created_at=datetime.now(timezone.utc),
        created_by="original@example.com",
        updated_at=None,
        updated_by=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_sub_task_by_subtask_id",
        return_value=subtask,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_preset_by_subtask_id",
        return_value=existing_preset,
    ) as mock_get_preset, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.update_preset",
        return_value=existing_preset,
    ) as mock_update, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.Utils.get_utc_date_time",
        return_value=datetime.now(timezone.utc),
    ):
        
        resp = await create_or_update_preset_service(
            token=token,
            subtask_id=subtask_id,
            preset_request=request,
        )
        
        assert mock_get_preset.call_count == 1
        assert mock_update.call_count == 1
        
        assert existing_preset.version_id == new_version_id
        assert existing_preset.language == "en"
        assert existing_preset.updated_by == "author@example.com"


@pytest.mark.asyncio
async def test_create_or_update_preset_service_raises_404_when_subtask_not_found():
    """Test that 404 is raised when subtask doesn't exist"""
    subtask_id = uuid.uuid4()
    version_id = uuid.uuid4()
    token = "valid_token_123"
    
    request = PresetRequest(
        version_id=str(version_id),
        language="bo"
    )
    
    author = SimpleNamespace(email="author@example.com", id=uuid.uuid4())
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_sub_task_by_subtask_id",
        return_value=None,
    ):
        
        with pytest.raises(HTTPException) as exc_info:
            await create_or_update_preset_service(
                token=token,
                subtask_id=subtask_id,
                preset_request=request,
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Subtask not found"


@pytest.mark.asyncio
async def test_get_preset_service_returns_preset():
    """Test getting a preset successfully"""
    subtask_id = uuid.uuid4()
    version_id = uuid.uuid4()
    preset_id = uuid.uuid4()
    
    preset = SimpleNamespace(
        id=preset_id,
        subtask_id=subtask_id,
        version_id=version_id,
        language="zh",
        created_at=datetime.now(timezone.utc),
        created_by="author@example.com",
        updated_at=None,
        updated_by=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_preset_by_subtask_id",
        return_value=preset,
    ) as mock_get_preset:
        
        resp = await get_preset_service(subtask_id=subtask_id)
        
        assert mock_get_preset.call_count == 1
        assert mock_get_preset.call_args.kwargs == {"db": db_mock, "subtask_id": subtask_id}
        
        assert resp.id == str(preset_id)
        assert resp.subtask_id == str(subtask_id)
        assert resp.version_id == str(version_id)
        assert resp.language == "zh"


@pytest.mark.asyncio
async def test_get_preset_service_raises_404_when_not_found():
    """Test that 404 is raised when preset doesn't exist"""
    subtask_id = uuid.uuid4()
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_preset_by_subtask_id",
        return_value=None,
    ):
        
        with pytest.raises(HTTPException) as exc_info:
            await get_preset_service(subtask_id=subtask_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Preset not found for this subtask"


@pytest.mark.asyncio
async def test_delete_preset_service_deletes_preset():
    """Test deleting a preset successfully"""
    subtask_id = uuid.uuid4()
    version_id = uuid.uuid4()
    preset_id = uuid.uuid4()
    token = "valid_token_123"
    
    author = SimpleNamespace(email="author@example.com", id=uuid.uuid4())
    
    preset = SimpleNamespace(
        id=preset_id,
        subtask_id=subtask_id,
        version_id=version_id,
        language="bo",
        created_at=datetime.now(timezone.utc),
        created_by="author@example.com",
        updated_at=None,
        updated_by=None,
    )
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.validate_and_extract_author_details",
        return_value=author,
    ) as mock_validate, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_preset_by_subtask_id",
        return_value=preset,
    ) as mock_get_preset, patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.delete_preset",
    ) as mock_delete:
        
        await delete_preset_service(token=token, subtask_id=subtask_id)
        
        assert mock_validate.call_count == 1
        assert mock_validate.call_args.kwargs == {"token": token}
        
        assert mock_get_preset.call_count == 1
        assert mock_get_preset.call_args.kwargs == {"db": db_mock, "subtask_id": subtask_id}
        
        assert mock_delete.call_count == 1
        assert mock_delete.call_args.kwargs == {"db": db_mock, "preset": preset}


@pytest.mark.asyncio
async def test_delete_preset_service_raises_404_when_not_found():
    """Test that 404 is raised when trying to delete non-existent preset"""
    subtask_id = uuid.uuid4()
    token = "valid_token_123"
    
    author = SimpleNamespace(email="author@example.com", id=uuid.uuid4())
    
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    
    with patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.validate_and_extract_author_details",
        return_value=author,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.sub_tasks.subtask_preset_service.get_preset_by_subtask_id",
        return_value=None,
    ):
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_preset_service(token=token, subtask_id=subtask_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Preset not found for this subtask"


def test_map_to_response_with_all_fields():
    """Test mapping preset model to response with all fields"""
    preset_id = uuid.uuid4()
    subtask_id = uuid.uuid4()
    version_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
    
    preset = SimpleNamespace(
        id=preset_id,
        subtask_id=subtask_id,
        version_id=version_id,
        language="en",
        created_at=created_at,
        created_by="creator@example.com",
        updated_at=updated_at,
        updated_by="updater@example.com",
    )
    
    resp = _map_to_response(preset)
    
    assert resp.id == str(preset_id)
    assert resp.subtask_id == str(subtask_id)
    assert resp.version_id == str(version_id)
    assert resp.language == "en"
    assert resp.created_at == created_at.isoformat()
    assert resp.created_by == "creator@example.com"
    assert resp.updated_at == updated_at.isoformat()
    assert resp.updated_by == "updater@example.com"


def test_map_to_response_without_updated_fields():
    """Test mapping preset model to response without updated fields"""
    preset_id = uuid.uuid4()
    subtask_id = uuid.uuid4()
    version_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    
    preset = SimpleNamespace(
        id=preset_id,
        subtask_id=subtask_id,
        version_id=version_id,
        language="bo",
        created_at=created_at,
        created_by="creator@example.com",
        updated_at=None,
        updated_by=None,
    )
    
    resp = _map_to_response(preset)
    
    assert resp.id == str(preset_id)
    assert resp.subtask_id == str(subtask_id)
    assert resp.version_id == str(version_id)
    assert resp.language == "bo"
    assert resp.created_at == created_at.isoformat()
    assert resp.created_by == "creator@example.com"
    assert resp.updated_at is None
    assert resp.updated_by is None
