import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from pecha_api.texts.groups.groups_cache_service import (
    get_group_by_id_cache,
    set_group_by_id_cache
)
from pecha_api.texts.groups.groups_response_models import GroupDTO
from pecha_api.cache.cache_enums import CacheType

@pytest.mark.asyncio
async def test_get_group_by_id_cache_success():
    mock_group = {
        "id": "group_id",
        "type": "group_type"
    }

    with patch("pecha_api.texts.groups.groups_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_group):

        response = await get_group_by_id_cache(group_id="group_id", cache_type=CacheType.GROUP_DETAIL)

        assert response is not None
        assert isinstance(response, GroupDTO)
        assert response.id == "group_id"

@pytest.mark.asyncio
async def test_set_group_by_id_cache_success():

    with patch("pecha_api.texts.groups.groups_cache_service.set_cache", new_callable=AsyncMock, return_value=None):

        await set_group_by_id_cache(group_id="group_id", cache_type=CacheType.GROUP_DETAIL, data=GroupDTO(id="group_id", type="group_type"))
    