import uuid
import pytest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException, FastAPI
from starlette import status

from pecha_api.routines.routines_response_models import (
    RoutineWithTimeBlocksResponse,
    RoutineResponse,
    TimeBlockDTO,
    SessionDTO,
)
from pecha_api.routines.routines_enums import SessionType


VALID_TOKEN = "valid_token"


@pytest.fixture
def routines_app():
    from pecha_api.routines import routines_views

    app = FastAPI()
    app.include_router(routines_views.routines_router)
    app.include_router(routines_views.user_routine_router)
    return app


@pytest.fixture
def authenticated_client(routines_app):
    from pecha_api.routines import routines_views

    original_dependency_overrides = routines_app.dependency_overrides.copy()

    def get_token_override():
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=VALID_TOKEN)

    routines_app.dependency_overrides[routines_views.oauth2_scheme] = get_token_override
    client = TestClient(routines_app)

    yield client

    routines_app.dependency_overrides = original_dependency_overrides


@pytest.fixture
def unauthenticated_client(routines_app):
    original_dependency_overrides = routines_app.dependency_overrides.copy()
    client = TestClient(routines_app)
    yield client
    routines_app.dependency_overrides = original_dependency_overrides


def test_create_routine_success(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    mock_response = RoutineWithTimeBlocksResponse(
        id=routine_id,
        time_blocks=[
            TimeBlockDTO(
                id=time_block_id,
                time="12:00",
                time_int=1200,
                notification_enabled=True,
                sessions=[
                    SessionDTO(
                        id=session_id,
                        session_type=SessionType.PLAN,
                        source_id=source_id,
                        title="Daily Routine",
                        language="EN",
                        image_url="https://example.com/image.jpg",
                        display_order=0,
                    )
                ],
            )
        ],
    )

    with patch(
        "pecha_api.routines.routines_views.create_routine_with_time_block",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_create:
        response = authenticated_client.post(
            "/routines",
            json={
                "time": "12:00",
                "time_int": 1200,
                "notification_enabled": True,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(source_id),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["id"] == str(routine_id)
        assert len(body["time_blocks"]) == 1
        assert body["time_blocks"][0]["time"] == "12:00"
        assert body["time_blocks"][0]["time_int"] == 1200
        assert body["time_blocks"][0]["sessions"][0]["title"] == "Daily Routine"
        assert body["time_blocks"][0]["sessions"][0]["language"] == "EN"
        mock_create.assert_called_once()


def test_create_routine_unauthorized(unauthenticated_client):
    response = unauthenticated_client.post(
        "/routines",
        json={
            "time": "12:00",
            "time_int": 1200,
            "sessions": [
                {
                    "session_type": "PLAN",
                    "source_id": str(uuid.uuid4()),
                    "display_order": 0,
                }
            ],
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_routine_conflict(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.create_routine_with_time_block",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.side_effect = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Bad request",
                "message": "Routine already exists for this user",
            },
        )

        response = authenticated_client.post(
            "/routines",
            json={
                "time": "12:00",
                "time_int": 1200,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert (
            response.json()["detail"]["message"]
            == "Routine already exists for this user"
        )


def test_create_routine_empty_sessions(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.create_routine_with_time_block",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.side_effect = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Bad request",
                "message": "At least one session is required",
            },
        )

        response = authenticated_client.post(
            "/routines",
            json={
                "time": "12:00",
                "time_int": 1200,
                "sessions": [],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_routine_invalid_time(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.create_routine_with_time_block",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.side_effect = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Bad request",
                "message": "Time must be in HH:MM 24-hour format (00:00 to 23:59)",
            },
        )

        response = authenticated_client.post(
            "/routines",
            json={
                "time": "25:00",
                "time_int": 2500,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"]["message"]
            == "Time must be in HH:MM 24-hour format (00:00 to 23:59)"
        )


def test_create_routine_duplicate_plan(authenticated_client):
    duplicate_source_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.create_routine_with_time_block",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.side_effect = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Bad request",
                "message": "A plan can only appear once across the entire routine",
            },
        )

        response = authenticated_client.post(
            "/routines",
            json={
                "time": "12:00",
                "time_int": 1200,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(duplicate_source_id),
                        "display_order": 0,
                    },
                    {
                        "session_type": "PLAN",
                        "source_id": str(duplicate_source_id),
                        "display_order": 1,
                    },
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            response.json()["detail"]["message"]
            == "A plan can only appear once across the entire routine"
        )


def test_create_time_block_success(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    mock_response = TimeBlockDTO(
        id=time_block_id,
        time="08:00",
        time_int=800,
        notification_enabled=True,
        sessions=[
            SessionDTO(
                id=session_id,
                session_type=SessionType.PLAN,
                source_id=source_id,
                title="Morning Plan",
                language="EN",
                image_url="https://example.com/morning.jpg",
                display_order=0,
            )
        ],
    )

    with patch(
        "pecha_api.routines.routines_views.add_time_block_to_routine",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_add:
        response = authenticated_client.post(
            f"/routines/{routine_id}/time-blocks",
            json={
                "time": "08:00",
                "time_int": 800,
                "notification_enabled": True,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(source_id),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["id"] == str(time_block_id)
        assert body["time"] == "08:00"
        assert body["time_int"] == 800
        assert len(body["sessions"]) == 1
        assert body["sessions"][0]["title"] == "Morning Plan"
        mock_add.assert_called_once()


def test_create_time_block_routine_not_found(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.add_time_block_to_routine",
        new_callable=AsyncMock,
    ) as mock_add:
        mock_add.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Bad request",
                "message": "Routine not found",
            },
        )

        response = authenticated_client.post(
            f"/routines/{uuid.uuid4()}/time-blocks",
            json={
                "time": "08:00",
                "time_int": 800,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["message"] == "Routine not found"


def test_create_time_block_forbidden(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.add_time_block_to_routine",
        new_callable=AsyncMock,
    ) as mock_add:
        mock_add.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Bad request",
                "message": "Routine does not belong to this user",
            },
        )

        response = authenticated_client.post(
            f"/routines/{uuid.uuid4()}/time-blocks",
            json={
                "time": "08:00",
                "time_int": 800,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_time_block_duplicate_time(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.add_time_block_to_routine",
        new_callable=AsyncMock,
    ) as mock_add:
        mock_add.side_effect = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Bad request",
                "message": "A time block with this time already exists in the routine",
            },
        )

        response = authenticated_client.post(
            f"/routines/{uuid.uuid4()}/time-blocks",
            json={
                "time": "12:00",
                "time_int": 1200,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert (
            response.json()["detail"]["message"]
            == "A time block with this time already exists in the routine"
        )


def test_create_time_block_duplicate_plan(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.add_time_block_to_routine",
        new_callable=AsyncMock,
    ) as mock_add:
        mock_add.side_effect = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Bad request",
                "message": "A plan can only appear once across the entire routine",
            },
        )

        response = authenticated_client.post(
            f"/routines/{uuid.uuid4()}/time-blocks",
            json={
                "time": "08:00",
                "time_int": 800,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_time_block_success(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.delete_time_block",
        return_value=None,
    ) as mock_delete:
        response = authenticated_client.delete(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""
        mock_delete.assert_called_once()


def test_delete_time_block_unauthorized(unauthenticated_client):
    response = unauthenticated_client.delete(
        f"/routines/{uuid.uuid4()}/time-blocks/{uuid.uuid4()}",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_time_block_routine_not_found(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.delete_time_block",
    ) as mock_delete:
        mock_delete.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Bad request",
                "message": "Routine not found",
            },
        )

        response = authenticated_client.delete(
            f"/routines/{uuid.uuid4()}/time-blocks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["message"] == "Routine not found"


def test_delete_time_block_forbidden(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.delete_time_block",
    ) as mock_delete:
        mock_delete.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Bad request",
                "message": "Routine does not belong to this user",
            },
        )

        response = authenticated_client.delete(
            f"/routines/{uuid.uuid4()}/time-blocks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_time_block_time_block_not_found(authenticated_client):
    with patch(
        "pecha_api.routines.routines_views.delete_time_block",
    ) as mock_delete:
        mock_delete.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Bad request",
                "message": "Time block not found",
            },
        )

        response = authenticated_client.delete(
            f"/routines/{uuid.uuid4()}/time-blocks/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["message"] == "Time block not found"


# --- Update Time Block (PUT) Tests ---


def test_update_time_block_success(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    mock_response = TimeBlockDTO(
        id=time_block_id,
        time="14:00",
        time_int=1400,
        notification_enabled=True,
        sessions=[
            SessionDTO(
                id=session_id,
                session_type=SessionType.PLAN,
                source_id=source_id,
                title="Updated Routine",
                language="EN",
                image_url="https://example.com/image.jpg",
                display_order=0,
            )
        ],
    )

    with patch(
        "pecha_api.routines.routines_views.update_time_block_service",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_update:
        response = authenticated_client.put(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            json={
                "time": "14:00",
                "time_int": 1400,
                "notification_enabled": True,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(source_id),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["id"] == str(time_block_id)
        assert body["time"] == "14:00"
        assert body["time_int"] == 1400
        assert body["notification_enabled"] is True
        assert len(body["sessions"]) == 1
        assert body["sessions"][0]["title"] == "Updated Routine"
        mock_update.assert_called_once()


def test_update_time_block_unauthorized(unauthenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    response = unauthenticated_client.put(
        f"/routines/{routine_id}/time-blocks/{time_block_id}",
        json={
            "time": "14:00",
            "time_int": 1400,
            "sessions": [
                {
                    "session_type": "PLAN",
                    "source_id": str(uuid.uuid4()),
                    "display_order": 0,
                }
            ],
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_time_block_routine_not_found(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.update_time_block_service",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Bad request", "message": "Routine not found"},
        )

        response = authenticated_client.put(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            json={
                "time": "14:00",
                "time_int": 1400,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["message"] == "Routine not found"


def test_update_time_block_forbidden(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.update_time_block_service",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Bad request", "message": "Routine does not belong to the authenticated user"},
        )

        response = authenticated_client.put(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            json={
                "time": "14:00",
                "time_int": 1400,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"]["message"] == "Routine does not belong to the authenticated user"


def test_update_time_block_not_found(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.update_time_block_service",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Bad request", "message": "Time block not found"},
        )

        response = authenticated_client.put(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            json={
                "time": "14:00",
                "time_int": 1400,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["message"] == "Time block not found"


def test_update_time_block_time_conflict(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.update_time_block_service",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.side_effect = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Bad request", "message": "Time block with this time already exists"},
        )

        response = authenticated_client.put(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            json={
                "time": "14:00",
                "time_int": 1400,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"]["message"] == "Time block with this time already exists"


def test_update_time_block_duplicate_plan(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.update_time_block_service",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.side_effect = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Bad request", "message": "A plan can only appear once across the entire routine"},
        )

        response = authenticated_client.put(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            json={
                "time": "14:00",
                "time_int": 1400,
                "sessions": [
                    {
                        "session_type": "PLAN",
                        "source_id": str(uuid.uuid4()),
                        "display_order": 0,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"]["message"] == "A plan can only appear once across the entire routine"


def test_update_time_block_empty_sessions(authenticated_client):
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    with patch(
        "pecha_api.routines.routines_views.update_time_block_service",
        new_callable=AsyncMock,
    ) as mock_update:
        mock_update.side_effect = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Bad request", "message": "At least one session is required"},
        )

        response = authenticated_client.put(
            f"/routines/{routine_id}/time-blocks/{time_block_id}",
            json={
                "time": "14:00",
                "time_int": 1400,
                "sessions": [],
            },
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()["detail"]["message"] == "At least one session is required"


# ============================================================================
# GET /users/me/routine Tests
# ============================================================================


def test_get_routine_success(authenticated_client):
    """Test successful retrieval of user routine with time blocks and sessions."""
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    mock_response = RoutineResponse(
        id=routine_id,
        time_blocks=[
            TimeBlockDTO(
                id=time_block_id,
                time="08:00",
                time_int=800,
                notification_enabled=True,
                sessions=[
                    SessionDTO(
                        id=session_id,
                        session_type=SessionType.PLAN,
                        source_id=source_id,
                        title="Morning Meditation",
                        language="EN",
                        image_url="https://example.com/image.jpg",
                        display_order=0,
                    )
                ],
            )
        ],
        skip=0,
        limit=20,
        total=1,
    )

    with patch(
        "pecha_api.routines.routines_views.get_user_routine",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_get:
        response = authenticated_client.get(
            "/users/me/routine",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["id"] == str(routine_id)
        assert body["skip"] == 0
        assert body["limit"] == 20
        assert body["total"] == 1
        assert len(body["time_blocks"]) == 1
        assert body["time_blocks"][0]["time"] == "08:00"
        assert body["time_blocks"][0]["time_int"] == 800
        assert body["time_blocks"][0]["notification_enabled"] is True
        assert body["time_blocks"][0]["sessions"][0]["title"] == "Morning Meditation"
        mock_get.assert_called_once()


def test_get_routine_unauthorized(unauthenticated_client):
    """Test that unauthenticated requests return 403 Forbidden."""
    response = unauthenticated_client.get("/users/me/routine")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_routine_empty_time_blocks(authenticated_client):
    """Test retrieval of routine with no time blocks (new user)."""
    routine_id = uuid.uuid4()

    mock_response = RoutineResponse(
        id=routine_id,
        time_blocks=[],
        skip=0,
        limit=20,
        total=0,
    )

    with patch(
        "pecha_api.routines.routines_views.get_user_routine",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_get:
        response = authenticated_client.get(
            "/users/me/routine",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["id"] == str(routine_id)
        assert body["time_blocks"] == []
        assert body["total"] == 0
        mock_get.assert_called_once()


def test_get_routine_with_pagination(authenticated_client):
    """Test retrieval of routine with custom pagination parameters."""
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    mock_response = RoutineResponse(
        id=routine_id,
        time_blocks=[
            TimeBlockDTO(
                id=time_block_id,
                time="12:00",
                time_int=1200,
                notification_enabled=False,
                sessions=[
                    SessionDTO(
                        id=session_id,
                        session_type=SessionType.RECITATION,
                        source_id=source_id,
                        title="Daily Recitation",
                        language="BO",
                        image_url=None,
                        display_order=0,
                    )
                ],
            )
        ],
        skip=5,
        limit=10,
        total=15,
    )

    with patch(
        "pecha_api.routines.routines_views.get_user_routine",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_get:
        response = authenticated_client.get(
            "/users/me/routine?skip=5&limit=10",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["skip"] == 5
        assert body["limit"] == 10
        assert body["total"] == 15
        mock_get.assert_called_once()


def test_get_routine_with_multiple_time_blocks(authenticated_client):
    """Test retrieval of routine with multiple time blocks sorted by time."""
    routine_id = uuid.uuid4()
    time_block_id_1 = uuid.uuid4()
    time_block_id_2 = uuid.uuid4()
    session_id_1 = uuid.uuid4()
    session_id_2 = uuid.uuid4()
    source_id_1 = uuid.uuid4()
    source_id_2 = uuid.uuid4()

    mock_response = RoutineResponse(
        id=routine_id,
        time_blocks=[
            TimeBlockDTO(
                id=time_block_id_1,
                time="06:00",
                time_int=600,
                notification_enabled=True,
                sessions=[
                    SessionDTO(
                        id=session_id_1,
                        session_type=SessionType.PLAN,
                        source_id=source_id_1,
                        title="Morning Practice",
                        language="EN",
                        image_url="https://example.com/morning.jpg",
                        display_order=0,
                    )
                ],
            ),
            TimeBlockDTO(
                id=time_block_id_2,
                time="20:00",
                time_int=2000,
                notification_enabled=True,
                sessions=[
                    SessionDTO(
                        id=session_id_2,
                        session_type=SessionType.RECITATION,
                        source_id=source_id_2,
                        title="Evening Recitation",
                        language="BO",
                        image_url=None,
                        display_order=0,
                    )
                ],
            ),
        ],
        skip=0,
        limit=20,
        total=2,
    )

    with patch(
        "pecha_api.routines.routines_views.get_user_routine",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_get:
        response = authenticated_client.get(
            "/users/me/routine",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert len(body["time_blocks"]) == 2
        assert body["time_blocks"][0]["time"] == "06:00"
        assert body["time_blocks"][1]["time"] == "20:00"
        assert body["total"] == 2
        mock_get.assert_called_once()


def test_get_routine_invalid_skip_parameter(authenticated_client):
    """Test that negative skip parameter returns 422 Unprocessable Entity."""
    response = authenticated_client.get(
        "/users/me/routine?skip=-1",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_routine_invalid_limit_parameter(authenticated_client):
    """Test that limit parameter exceeding max returns 422 Unprocessable Entity."""
    response = authenticated_client.get(
        "/users/me/routine?limit=101",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_routine_limit_below_minimum(authenticated_client):
    """Test that limit parameter below minimum returns 422 Unprocessable Entity."""
    response = authenticated_client.get(
        "/users/me/routine?limit=0",
        headers={"Authorization": f"Bearer {VALID_TOKEN}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_routine_service_error(authenticated_client):
    """Test that service layer HTTPException is properly propagated."""
    with patch(
        "pecha_api.routines.routines_views.get_user_routine",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.side_effect = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "message": "Database connection failed"},
        )

        response = authenticated_client.get(
            "/users/me/routine",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_get_routine_invalid_token(authenticated_client):
    """Test that invalid authentication token returns 401 Unauthorized."""
    with patch(
        "pecha_api.routines.routines_views.get_user_routine",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "message": "Invalid token"},
        )

        response = authenticated_client.get(
            "/users/me/routine",
            headers={"Authorization": f"Bearer invalid_token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
