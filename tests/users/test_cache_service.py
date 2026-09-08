from pecha_api.utils import Utils
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from uuid import uuid4
import pytest
from pecha_api.cache.cache_repository import (
    get_cache_data,
    set_cache
)
from pecha_api.users.user_response_models import (
    UserInfoResponse
)

from pecha_api.users.user_cache_service import (
    get_user_info_cache,
    set_user_info_cache,
    update_user_info_cache,
    update_user_avatar_cache
)

from pecha_api.cache.cache_enums import CacheType

@pytest.mark.asyncio
async def test_get_user_info_cache_empty_cache():
    with patch("pecha_api.users.user_cache_service.get_cache_data", new_callable=AsyncMock, return_value=None):
    
        response = await get_user_info_cache(token="token", cache_type=CacheType.USER_INFO)

        assert response is None

@pytest.mark.asyncio
async def test_get_user_info_cache_success():
    mock_cache_data = UserInfoResponse(
        id=uuid4(),
        username="username_1",
        email="email_1",
        firstname="firstname_1",
        lastname="lastname_1",
        avatar_url="avatar_url_1",
        educations=["education_1"],
        followers=1,
        following=1,
        social_profiles=[]
    )
    with patch("pecha_api.users.user_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_data):

        response = await get_user_info_cache(token="token", cache_type=CacheType.USER_INFO)

        assert response is not None
        assert isinstance(response, UserInfoResponse)
        assert response.email == mock_cache_data.email

@pytest.mark.asyncio
async def test_set_user_info_cache_success():
    mock_cache_data = UserInfoResponse(
        id=uuid4(),
        username="username_1",
        email="email_1",
        firstname="firstname_1",
        lastname="lastname_1",
        avatar_url="avatar_url_1",
        educations=["education_1"],
        followers=1,
        following=1,
        social_profiles=[]
    )
    with patch("pecha_api.users.user_cache_service.Utils.generate_hash_key", return_value="hashed_key"), \
         patch("pecha_api.users.user_cache_service.config.get_int", return_value=123) as mock_get_int, \
         patch("pecha_api.users.user_cache_service.set_cache", new_callable=AsyncMock) as mock_set:

        await set_user_info_cache(token="token", data=mock_cache_data, cache_type=CacheType.USER_INFO)

        mock_get_int.assert_called_once_with("CACHE_TEXT_TIMEOUT")
        mock_set.assert_awaited_once_with(hash_key="hashed_key", value=mock_cache_data, cache_time_out=123)


@pytest.mark.asyncio
async def test_update_user_info_cache_updates_existing():
    mock_cache_data = UserInfoResponse(
        id=uuid4(),
        username="username_1",
        email="email_1",
        firstname="firstname_1",
        lastname="lastname_1",
        avatar_url="avatar_url_1",
        educations=["education_1"],
        followers=1,
        following=1,
        social_profiles=[]
    )

    with patch("pecha_api.users.user_cache_service.Utils.generate_hash_key", return_value="hashed_key"), \
         patch("pecha_api.users.user_cache_service.config.get_int", return_value=123), \
         patch("pecha_api.users.user_cache_service.update_cache", new_callable=AsyncMock, return_value=True) as mock_update, \
         patch("pecha_api.users.user_cache_service.set_cache", new_callable=AsyncMock) as mock_set:

        result = await update_user_info_cache(token="token", data=mock_cache_data, cache_type=CacheType.USER_INFO)

        assert result is True
        mock_update.assert_awaited_once_with(hash_key="hashed_key", value=mock_cache_data, cache_time_out=123)
        assert mock_set.await_count == 0


@pytest.mark.asyncio
async def test_update_user_info_cache_deletes_when_update_fails():
    mock_cache_data = UserInfoResponse(
        id=uuid4(),
        username="username_1",
        email="email_1",
        firstname="firstname_1",
        lastname="lastname_1",
        avatar_url="avatar_url_1",
        educations=["education_1"],
        followers=1,
        following=1,
        social_profiles=[]
    )

    with patch("pecha_api.users.user_cache_service.Utils.generate_hash_key", return_value="hashed_key"), \
         patch("pecha_api.users.user_cache_service.config.get_int", return_value=123), \
         patch("pecha_api.users.user_cache_service.update_cache", new_callable=AsyncMock, return_value=False) as mock_update, \
         patch("pecha_api.users.user_cache_service.delete_cache", new_callable=AsyncMock, return_value=True) as mock_delete:

        result = await update_user_info_cache(token="token", data=mock_cache_data, cache_type=CacheType.USER_INFO)

        assert result is True
        mock_update.assert_awaited_once_with(hash_key="hashed_key", value=mock_cache_data, cache_time_out=123)
        mock_delete.assert_awaited_once_with(hash_key="hashed_key")


@pytest.mark.asyncio
async def test_get_user_info_cache_converts_dict_to_model():
    mock_cache_dict = {
        "id": str(uuid4()),
        "username": "username_1",
        "email": "email_1",
        "firstname": "firstname_1",
        "lastname": "lastname_1",
        "avatar_url": "avatar_url_1",
        "educations": ["education_1"],
        "followers": 1,
        "following": 1,
        "social_profiles": []
    }

    with patch("pecha_api.users.user_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_dict):

        response = await get_user_info_cache(token="token", cache_type=CacheType.USER_INFO)

        assert isinstance(response, UserInfoResponse)
        assert response.email == mock_cache_dict["email"]


@pytest.mark.asyncio
async def test_update_user_avatar_cache_updates_existing():
    mock_cache_data = UserInfoResponse(
        id=uuid4(),
        username="username_1",
        email="email_1",
        firstname="firstname_1",
        lastname="lastname_1",
        avatar_url="avatar_url_1",
        educations=["education_1"],
        followers=1,
        following=1,
        social_profiles=[]
    )

    with patch("pecha_api.users.user_cache_service.Utils.generate_hash_key", return_value="hashed_key"), \
         patch("pecha_api.users.user_cache_service.config.get_int", return_value=123), \
         patch("pecha_api.users.user_cache_service.update_cache", new_callable=AsyncMock, return_value=True) as mock_update, \
         patch("pecha_api.users.user_cache_service.delete_cache", new_callable=AsyncMock) as mock_delete:

        result = await update_user_avatar_cache(token="token", data=mock_cache_data, cache_type=CacheType.USER_INFO)

        assert result is True
        mock_update.assert_awaited_once_with(hash_key="hashed_key", value=mock_cache_data, cache_time_out=123)
        assert mock_delete.await_count == 0


@pytest.mark.asyncio
async def test_update_user_avatar_cache_deletes_when_update_fails():
    mock_cache_data = UserInfoResponse(
        id=uuid4(),
        username="username_1",
        email="email_1",
        firstname="firstname_1",
        lastname="lastname_1",
        avatar_url="avatar_url_1",
        educations=["education_1"],
        followers=1,
        following=1,
        social_profiles=[]
    )

    with patch("pecha_api.users.user_cache_service.Utils.generate_hash_key", return_value="hashed_key"), \
         patch("pecha_api.users.user_cache_service.config.get_int", return_value=123), \
         patch("pecha_api.users.user_cache_service.update_cache", new_callable=AsyncMock, return_value=False) as mock_update, \
         patch("pecha_api.users.user_cache_service.delete_cache", new_callable=AsyncMock, return_value=True) as mock_delete:

        result = await update_user_avatar_cache(token="token", data=mock_cache_data, cache_type=CacheType.USER_INFO)

        assert result is True
        mock_update.assert_awaited_once_with(hash_key="hashed_key", value=mock_cache_data, cache_time_out=123)
        mock_delete.assert_awaited_once_with(hash_key="hashed_key")
