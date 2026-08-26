from unittest.mock import patch
from uuid import uuid4
from datetime import datetime, timezone as tz

from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.response_models import (
    GroupPostDTO,
    GroupPostsResponse,
)

client = TestClient(api)

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _post_dto(group_id=None, caption="Hello", post_status="PUBLISHED") -> GroupPostDTO:
    now = datetime.now(tz.utc).isoformat()
    return GroupPostDTO(
        id=uuid4(),
        group_id=group_id or uuid4(),
        caption=caption,
        status=post_status,
        published_at=now,
        media=[],
        links=[],
        created_at=now,
        updated_at=now,
    )


class TestCmsGroupPostsViews:

    @patch('pecha_api.group_posts.cms_views.cms_list_group_posts_service')
    def test_list_passes_status_filter(self, mock_service):
        group_id = uuid4()
        mock_service.return_value = GroupPostsResponse(posts=[], skip=0, limit=20, total=0)

        response = client.get(
            f"/cms/author/groups/{group_id}/posts?status=HIDDEN",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            token="test-token",
            group_id=group_id,
            skip=0,
            limit=20,
            status_filter=GroupPostStatus.HIDDEN,
        )

    def test_list_requires_auth(self):
        response = client.get(f"/cms/author/groups/{uuid4()}/posts")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_posts.cms_views.cms_get_group_post_detail_service')
    def test_get_group_post_detail(self, mock_service):
        group_id = uuid4()
        dto = _post_dto(group_id=group_id, post_status="HIDDEN")
        mock_service.return_value = dto

        response = client.get(
            f"/cms/author/groups/{group_id}/posts/{dto.id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "HIDDEN"
        mock_service.assert_called_once_with(
            token="test-token",
            group_id=group_id,
            post_id=dto.id,
        )

    def test_get_group_post_detail_requires_auth(self):
        response = client.get(f"/cms/author/groups/{uuid4()}/posts/{uuid4()}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_posts.cms_views.cms_create_group_post_service')
    def test_create_group_post(self, mock_service):
        group_id = uuid4()
        mock_service.return_value = _post_dto(group_id=group_id)

        response = client.post(
            f"/cms/author/groups/{group_id}/posts",
            headers=AUTH_HEADERS,
            json={
                "caption": "Hello",
                "media": [
                    {
                        "media_type": "IMAGE",
                        "media_key": "groups/g/posts/a.webp",
                        "display_order": 1,
                    }
                ],
                "links": [
                    {
                        "type": "EXTERNAL",
                        "url": "https://example.com",
                        "label": "Full guide",
                        "display_order": 1,
                    }
                ],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        kwargs = mock_service.call_args.kwargs
        assert kwargs["token"] == "test-token"
        assert kwargs["group_id"] == group_id
        assert kwargs["request"].media[0].media_key == "groups/g/posts/a.webp"
        assert kwargs["request"].links[0].url == "https://example.com"

    @patch('pecha_api.group_posts.cms_views.cms_create_group_post_service')
    def test_create_group_post_rejects_bad_link_url(self, mock_service):
        response = client.post(
            f"/cms/author/groups/{uuid4()}/posts",
            headers=AUTH_HEADERS,
            json={
                "caption": "Hello",
                "links": [{"type": "EXTERNAL", "url": "javascript:alert(1)"}],
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.assert_not_called()

    @patch('pecha_api.group_posts.cms_views.cms_update_group_post_service')
    def test_update_group_post(self, mock_service):
        group_id = uuid4()
        dto = _post_dto(group_id=group_id, post_status="HIDDEN")
        mock_service.return_value = dto

        response = client.patch(
            f"/cms/author/groups/{group_id}/posts/{dto.id}",
            headers=AUTH_HEADERS,
            json={"status": "HIDDEN"},
        )

        assert response.status_code == status.HTTP_200_OK
        kwargs = mock_service.call_args.kwargs
        assert kwargs["request"].status == GroupPostStatus.HIDDEN

    @patch('pecha_api.group_posts.cms_views.cms_replace_group_post_media_service')
    def test_replace_media(self, mock_service):
        group_id = uuid4()
        dto = _post_dto(group_id=group_id)
        mock_service.return_value = dto

        response = client.put(
            f"/cms/author/groups/{group_id}/posts/{dto.id}/media",
            headers=AUTH_HEADERS,
            json={
                "media": [
                    {
                        "media_type": "AUDIO",
                        "media_key": "groups/g/posts/chant.mp3",
                        "duration_ms": 60000,
                        "display_order": 1,
                    }
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK
        kwargs = mock_service.call_args.kwargs
        assert kwargs["request"].media[0].duration_ms == 60000

    @patch('pecha_api.group_posts.cms_views.cms_replace_group_post_links_service')
    def test_replace_links(self, mock_service):
        group_id = uuid4()
        dto = _post_dto(group_id=group_id)
        mock_service.return_value = dto

        response = client.put(
            f"/cms/author/groups/{group_id}/posts/{dto.id}/links",
            headers=AUTH_HEADERS,
            json={"links": [{"type": "YOUTUBE", "url": "https://youtube.com/watch?v=x"}]},
        )

        assert response.status_code == status.HTTP_200_OK
        kwargs = mock_service.call_args.kwargs
        assert kwargs["request"].links[0].type == "YOUTUBE"

    @patch('pecha_api.group_posts.cms_views.cms_delete_group_post_service')
    def test_delete_group_post(self, mock_service):
        group_id = uuid4()
        post_id = uuid4()
        mock_service.return_value = None

        response = client.delete(
            f"/cms/author/groups/{group_id}/posts/{post_id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_service.assert_called_once_with(
            token="test-token",
            group_id=group_id,
            post_id=post_id,
        )
