import uuid
import pytest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException, FastAPI
from starlette import status

from pecha_api.routines.routines_response_models import (
    RoutineWithTimeBlocksResponse,
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
