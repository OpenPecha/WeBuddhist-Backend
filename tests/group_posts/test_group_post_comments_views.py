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


def _comment_dto(
    post_id=None,
    user_email="user@example.com",
    parent_comment_id=None,
) -> GroupPostCommentDTO:
    now = datetime.now(tz.utc).isoformat()
    return GroupPostCommentDTO(
        id=uuid4(),
        post_id=post_id or uuid4(),
        parent_comment_id=parent_comment_id,
        user={
            "first_name": "First",
            "last_name": "Last",
            "email": user_email,
            "avatar_url": "https://example.com/avatar.jpg",
        },
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
            f"/groups/author/posts/{post_id}/comments?skip=0&limit=20"
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["total"] == 1
        assert body["comments"][0]["text"] == "Great post!"
        assert body["comments"][0]["user"] == {
            "first_name": "First",
            "last_name": "Last",
            "email": "user@example.com",
            "avatar_url": "https://example.com/avatar.jpg",
        }
        assert "user_id" not in body["comments"][0]

    @patch('pecha_api.group_posts.comment_views.list_post_comments_service')
    def test_list_comments_empty(self, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        mock_service.return_value = GroupPostCommentsResponse(
            comments=[], skip=0, limit=20, total=0
        )

        response = client.get(f"/groups/author/posts/{post_id}/comments")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 0


class TestCreatePostCommentView:

    @patch('pecha_api.group_posts.comment_views.create_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_user_details')
    def test_create_comment(self, mock_validate, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        user = MagicMock()
        user.id = uuid4()
        mock_validate.return_value = user
        mock_service.return_value = _comment_dto(post_id=post_id)

        response = client.post(
            f"/groups/author/posts/{post_id}/comments",
            headers=AUTH_HEADERS,
            json={"text": "Great post!"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["text"] == "Great post!"
        mock_validate.assert_called_once_with(token="test-token")
        mock_service.assert_called_once_with(
            post_id=post_id,
            user_id=user.id,
            text="Great post!",
            parent_comment_id=None,
        )

    @patch('pecha_api.group_posts.comment_views.create_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_user_details')
    def test_create_reply_to_comment(self, mock_validate, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        parent_comment_id = uuid4()
        user = MagicMock(id=uuid4())
        mock_validate.return_value = user
        mock_service.return_value = _comment_dto(
            post_id=post_id,
            parent_comment_id=parent_comment_id,
        )

        response = client.post(
            f"/groups/author/posts/{post_id}/comments",
            headers=AUTH_HEADERS,
            json={
                "text": "Nested reply",
                "parent_comment_id": str(parent_comment_id),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["parent_comment_id"] == str(parent_comment_id)
        mock_service.assert_called_once_with(
            post_id=post_id,
            user_id=user.id,
            text="Nested reply",
            parent_comment_id=parent_comment_id,
        )

    def test_create_comment_requires_auth(self):
        client = get_client()

        response = client.post(
            f"/groups/author/posts/{uuid4()}/comments",
            json={"text": "Great post!"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_posts.comment_views.create_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_user_details')
    def test_create_comment_rejects_blank_text(self, mock_validate, mock_service):
        client = get_client()

        response = client.post(
            f"/groups/author/posts/{uuid4()}/comments",
            headers=AUTH_HEADERS,
            json={"text": "   "},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.assert_not_called()

    @patch('pecha_api.group_posts.comment_views.create_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_user_details')
    def test_create_comment_propagates_service_error(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock(id=uuid4())
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
        )

        response = client.post(
            f"/groups/author/posts/{uuid4()}/comments",
            headers=AUTH_HEADERS,
            json={"text": "Great post!"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeletePostCommentView:

    @patch('pecha_api.group_posts.comment_views.delete_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_user_details')
    def test_delete_comment(self, mock_validate, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        comment_id = uuid4()
        user_id = uuid4()
        user = MagicMock()
        user.id = user_id
        mock_validate.return_value = user
        mock_service.return_value = None

        response = client.delete(
            f"/groups/author/comments/{comment_id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_service.assert_called_once_with(
            comment_id=comment_id,
            user_id=user_id,
        )

    def test_delete_comment_requires_auth(self):
        client = get_client()

        response = client.delete(
            f"/groups/author/comments/{uuid4()}"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_posts.comment_views.delete_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_user_details')
    def test_delete_comment_of_another_user_is_forbidden(
        self,
        mock_validate,
        mock_service,
    ):
        client = get_client()
        mock_validate.return_value = MagicMock(id=uuid4())
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

        response = client.delete(
            f"/groups/author/comments/{uuid4()}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

