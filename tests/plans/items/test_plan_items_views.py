import uuid
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.items.plan_items_response_models import ItemDTO
from fastapi import FastAPI


VALID_TOKEN = "valid_token"


@pytest.fixture
def items_app():
    """Create a minimal FastAPI app including only the items router."""
    from pecha_api.plans.items import plan_items_views
    app = FastAPI()
    app.include_router(plan_items_views.items_router)
    return app


@pytest.fixture
def authenticated_client(items_app):
    from pecha_api.plans.items import plan_items_views

    original_dependency_overrides = items_app.dependency_overrides.copy()

    def get_token_override():
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=VALID_TOKEN)

    items_app.dependency_overrides[plan_items_views.oauth2_scheme] = get_token_override
    client = TestClient(items_app)

    yield client

    items_app.dependency_overrides = original_dependency_overrides


@pytest.fixture
def unauthenticated_client(items_app):
    original_dependency_overrides = items_app.dependency_overrides.copy()
    client = TestClient(items_app)
    yield client
    items_app.dependency_overrides = original_dependency_overrides


def test_create_day_success(authenticated_client):
    plan_id = uuid.uuid4()
    created = ItemDTO(id=uuid.uuid4(), plan_id=plan_id, day_number=4)

    with patch("pecha_api.plans.items.plan_items_views.create_plan_item", return_value=[created]) as mock_create:
        response = authenticated_client.post(f"/cms/plans/{plan_id}/days", headers={"Authorization": f"Bearer {VALID_TOKEN}"})

        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert len(body) == 1
        assert body[0]["id"] == str(created.id)
        assert body[0]["plan_id"] == str(plan_id)
        assert body[0]["day_number"] == 4
        mock_create.assert_called_once()


def test_create_day_unauthorized(unauthenticated_client):
    plan_id = uuid.uuid4()
    response = unauthenticated_client.post(f"/cms/plans/{plan_id}/days")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_day_service_error(authenticated_client):
    plan_id = uuid.uuid4()
    with patch("pecha_api.plans.items.plan_items_views.create_plan_item") as mock_create:
        mock_create.side_effect = HTTPException(status_code=404, detail={"error": "Bad request", "message": "plan not found"})

        response = authenticated_client.post(f"/cms/plans/{plan_id}/days", headers={"Authorization": f"Bearer {VALID_TOKEN}"})

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == {"error": "Bad request", "message": "plan not found"}


def test_delete_day_success(authenticated_client):
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    with patch("pecha_api.plans.items.plan_items_views.delete_plan_days", return_value=None) as mock_delete:
        response = authenticated_client.request(
            "DELETE",
            f"/cms/plans/{plan_id}/days",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
            json={"day_ids": [str(day_id)]},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""
        mock_delete.assert_called_once()


def test_delete_day_unauthorized(unauthenticated_client):
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()
    response = unauthenticated_client.request(
        "DELETE",
        f"/cms/plans/{plan_id}/days",
        json={"day_ids": [str(day_id)]},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_reorder_days_success(authenticated_client):
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()
    payload = {"days": [{"id": str(day_id), "day_number": 1}]}

    with patch("pecha_api.plans.items.plan_items_views.update_plans_day_number", return_value=None) as mock_reorder:
        response = authenticated_client.put(
            f"/cms/plans/{plan_id}/reorder-days",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
            json=payload,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_reorder.assert_called_once()


def test_reorder_days_unauthorized(unauthenticated_client):
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()
    response = unauthenticated_client.put(
        f"/cms/plans/{plan_id}/reorder-days",
        json={"days": [{"id": str(day_id), "day_number": 1}]},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_day_audio_success(authenticated_client):
    day_id = uuid.uuid4()

    with patch("pecha_api.plans.items.plan_items_views.delete_plan_day_audio", return_value=None) as mock_delete_audio:
        response = authenticated_client.delete(
            f"/cms/plans/days/{day_id}/audio",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_delete_audio.assert_called_once()


def test_delete_day_audio_unauthorized(unauthenticated_client):
    day_id = uuid.uuid4()
    response = unauthenticated_client.delete(f"/cms/plans/days/{day_id}/audio")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_day_not_found(authenticated_client):
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    with patch("pecha_api.plans.items.plan_items_views.delete_plan_days") as mock_delete:
        mock_delete.side_effect = HTTPException(status_code=404, detail={"error": "Not Found", "message": "day not found"})

        response = authenticated_client.request(
            "DELETE",
            f"/cms/plans/{plan_id}/days",
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
            json={"day_ids": [str(day_id)]},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == {"error": "Not Found", "message": "day not found"}
