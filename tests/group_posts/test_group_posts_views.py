from unittest.mock import patch
from uuid import uuid4
from datetime import datetime, timezone as tz

from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.group_posts.response_models import (
    GroupPostDTO,
    GroupPostLinkDTO,
    GroupPostMediaDTO,
    GroupPostsResponse,
)

client = TestClient(api)


def _post_dto(group_id=None, caption="Hello", post_status="PUBLISHED") -> GroupPostDTO:
    now = datetime.now(tz.utc).isoformat()
    return GroupPostDTO(
        id=uuid4(),
        group_id=group_id or uuid4(),
        caption=caption,
        status=post_status,
        published_at=now,
        media=[
            GroupPostMediaDTO(
                id=uuid4(),
                media_type="IMAGE",
                url="https://presigned.example/a.webp",
                width=1080,
                height=1350,
                display_order=1,
            )
        ],
        links=[
            GroupPostLinkDTO(
                id=uuid4(),
                type="EXTERNAL",
                url="https://example.com",
                label="Full guide",
                display_order=1,
            )
        ],
        created_at=now,
        updated_at=now,
    )


class TestPublicGroupPostsViews:

    @patch('pecha_api.group_posts.views.list_group_posts_service')
    def test_list_group_posts(self, mock_service):
        group_id = uuid4()
        dto = _post_dto(group_id=group_id)
        mock_service.return_value = GroupPostsResponse(posts=[dto], skip=0, limit=10, total=1)

        response = client.get(f"/author/groups/{group_id}/posts?skip=0&limit=10")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["total"] == 1
        assert body["posts"][0]["caption"] == "Hello"
        assert body["posts"][0]["media"][0]["url"] == "https://presigned.example/a.webp"
        mock_service.assert_called_once_with(group_id=group_id, skip=0, limit=10)

    @patch('pecha_api.group_posts.views.list_group_posts_service')
    def test_list_group_posts_invalid_limit(self, mock_service):
        response = client.get(f"/author/groups/{uuid4()}/posts?limit=0")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.assert_not_called()

    @patch('pecha_api.group_posts.views.get_group_post_detail_service')
    def test_get_group_post_detail(self, mock_service):
        group_id = uuid4()
        dto = _post_dto(group_id=group_id)
        mock_service.return_value = dto

        response = client.get(f"/author/groups/{group_id}/posts/{dto.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == str(dto.id)
        mock_service.assert_called_once_with(group_id=group_id, post_id=dto.id)

    @patch('pecha_api.group_posts.views.get_group_post_detail_service')
    def test_get_group_post_detail_not_found(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
        )

        response = client.get(f"/author/groups/{uuid4()}/posts/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
