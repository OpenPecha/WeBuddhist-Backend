from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz

from fastapi import HTTPException
from starlette import status
from pecha_api.group_posts.comment_response_models import (
    GroupPostCommentDTO,
    GroupPostCommentsResponse,
)

# Lazy import to avoid app initialization issues
def get_client():
    from pecha_api.app import api
    from fastapi.testclient import TestClient
    return TestClient(api)

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _comment_dto(post_id=None, user_id=None, user_email="user@example.com") -> GroupPostCommentDTO:
    now = datetime.now(tz.utc).isoformat()
    return GroupPostCommentDTO(
        id=uuid4(),
        post_id=post_id or uuid4(),
        user_id=user_id or uuid4(),
        user_email=user_email,
        text="Great post!",
        created_at=now,
        updated_at=now,
    )


class TestPublicGroupPostCommentsViews:

    @patch('pecha_api.group_posts.comment_views.list_post_comments_service')
    def test_list_comments(self, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        dto = _comment_dto(post_id=post_id)
        mock_service.return_value = GroupPostCommentsResponse(
            comments=[dto], skip=0, limit=20, total=1
        )

        response = client.get(
            f"/author/groups/{group_id}/posts/{post_id}/comments?skip=0&limit=20"
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["total"] == 1
        assert body["comments"][0]["text"] == "Great post!"

    @patch('pecha_api.group_posts.comment_views.list_post_comments_service')
    def test_list_comments_empty(self, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        mock_service.return_value = GroupPostCommentsResponse(
            comments=[], skip=0, limit=20, total=0
        )

        response = client.get(f"/author/groups/{group_id}/posts/{post_id}/comments")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 0

