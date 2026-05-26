from unittest.mock import AsyncMock, patch
import pytest

from fastapi.testclient import TestClient
from pecha_api.app import api


from pecha_api.texts.groups.groups_response_models import (
    GroupDTO,
    CreateGroupRequest
)
from pecha_api.texts.groups.groups_enums import GroupType

client = TestClient(api)

@pytest.mark.asyncio
async def test_get_group_by_id_success():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    group_details = GroupDTO(
        id = group_id,
        type = "version"
    )
    with patch("pecha_api.texts.groups.groups_views.get_group_details", new_callable=AsyncMock) as mock_group_details:
        mock_group_details.return_value = group_details
        response = client.get(f"/groups/{group_id}")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_group_success():
    create_group_request = {
        "type": GroupType.TEXT.value
    }
    with patch("pecha_api.texts.groups.groups_views.create_new_group", new_callable=AsyncMock) as mock_create_group:
        mock_create_group.return_value = GroupDTO(
            id="4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163",
            type="version"
        )
        response = client.post("/groups", json=create_group_request, headers={"Authorization": "Bearer testtoken"})
        assert response.status_code == 201

