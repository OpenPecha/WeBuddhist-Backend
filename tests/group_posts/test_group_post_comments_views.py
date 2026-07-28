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


class TestCreatePostCommentView:

    @patch('pecha_api.group_posts.comment_views.create_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_author_details')
    def test_create_comment(self, mock_validate, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        author = MagicMock()
        author.email = "author@example.com"
        mock_validate.return_value = author
        mock_service.return_value = _comment_dto(post_id=post_id)

        response = client.post(
            f"/author/groups/{group_id}/posts/{post_id}/comments",
            headers=AUTH_HEADERS,
            json={"text": "Great post!"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["text"] == "Great post!"
        mock_validate.assert_called_once_with(token="test-token")
        mock_service.assert_called_once_with(
            group_id=group_id,
            post_id=post_id,
            author_email="author@example.com",
            text="Great post!",
        )

    def test_create_comment_requires_auth(self):
        client = get_client()

        response = client.post(
            f"/author/groups/{uuid4()}/posts/{uuid4()}/comments",
            json={"text": "Great post!"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_posts.comment_views.create_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_author_details')
    def test_create_comment_rejects_blank_text(self, mock_validate, mock_service):
        client = get_client()

        response = client.post(
            f"/author/groups/{uuid4()}/posts/{uuid4()}/comments",
            headers=AUTH_HEADERS,
            json={"text": "   "},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.assert_not_called()

    @patch('pecha_api.group_posts.comment_views.create_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_author_details')
    def test_create_comment_propagates_service_error(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock(email="author@example.com")
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
        )

        response = client.post(
            f"/author/groups/{uuid4()}/posts/{uuid4()}/comments",
            headers=AUTH_HEADERS,
            json={"text": "Great post!"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeletePostCommentView:

    @patch('pecha_api.group_posts.comment_views.delete_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_author_details')
    def test_delete_comment(self, mock_validate, mock_service):
        client = get_client()
        group_id = uuid4()
        post_id = uuid4()
        comment_id = uuid4()
        author = MagicMock()
        author.id = uuid4()
        mock_validate.return_value = author
        mock_service.return_value = None

        response = client.delete(
            f"/author/groups/{group_id}/posts/{post_id}/comments/{comment_id}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_service.assert_called_once_with(
            group_id=group_id,
            post_id=post_id,
            comment_id=comment_id,
            user_id=author.id,
        )

    def test_delete_comment_requires_auth(self):
        client = get_client()

        response = client.delete(
            f"/author/groups/{uuid4()}/posts/{uuid4()}/comments/{uuid4()}"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_posts.comment_views.delete_post_comment_service')
    @patch('pecha_api.group_posts.comment_views.validate_and_extract_author_details')
    def test_delete_comment_of_another_user_is_forbidden(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock(id=uuid4())
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

        response = client.delete(
            f"/author/groups/{uuid4()}/posts/{uuid4()}/comments/{uuid4()}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

