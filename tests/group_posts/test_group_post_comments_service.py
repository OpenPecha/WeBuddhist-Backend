import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

from pecha_api.group_posts.comment_response_models import (
    GroupPostCommentDTO,
    GroupPostCommentsResponse,
)
from pecha_api.group_posts.comment_service import (
    build_comment_dto,
    create_post_comment_service,
    delete_post_comment_service,
    list_post_comments_service,
)


class MockUser:
    def __init__(self, user_id=None, email="user@example.com"):
        self.id = user_id or uuid4()
        self.email = email


class MockComment:
    def __init__(self, user=None, user_id=None, post_id=None, text="Great post!"):
        self.id = uuid4()
        self.post_id = post_id or uuid4()
        self.user_id = user_id or uuid4()
        self.user = user or MockUser(user_id=self.user_id)
        self.text = text
        self.created_at = datetime.now(tz.utc)
        self.updated_at = datetime.now(tz.utc)
        self.deleted_at = None


class MockGroup:
    def __init__(self, id=None, is_public=True):
        self.id = id or uuid4()
        self.is_public = is_public


class MockPost:
    def __init__(self, id=None, group_id=None):
        self.id = id or uuid4()
        self.group_id = group_id or uuid4()
        self.deleted_at = None


class TestListPostCommentsService:

    @patch('pecha_api.group_posts.comment_service.get_post_comments')
    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_list_comments_success(
        self, mock_session, mock_get_group, mock_get_post, mock_get_comments
    ):
        group_id = uuid4()
        post_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_post.return_value = MockPost(id=post_id, group_id=group_id)

        user = MockUser(email="commenter@example.com")
        comment = MockComment(user=user, post_id=post_id)
        mock_get_comments.return_value = ([comment], 1)

        result = list_post_comments_service(
            group_id=group_id,
            post_id=post_id,
            skip=0,
            limit=20,
        )

        assert isinstance(result, GroupPostCommentsResponse)
        assert result.total == 1
        assert result.comments[0].user_email == "commenter@example.com"

    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_list_comments_private_group_returns_404(self, mock_session, mock_get_group):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(is_public=False)

        with pytest.raises(HTTPException) as exc_info:
            list_post_comments_service(
                group_id=uuid4(),
                post_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_posts.comment_service.get_post_comments')
    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_list_comments_empty(
        self, mock_session, mock_get_group, mock_get_post, mock_get_comments
    ):
        group_id = uuid4()
        post_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_post.return_value = MockPost(id=post_id, group_id=group_id)
        mock_get_comments.return_value = ([], 0)

        result = list_post_comments_service(
            group_id=group_id,
            post_id=post_id,
        )

        assert result.comments == []
        assert result.total == 0

    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_list_comments_post_not_found_returns_404(
        self, mock_session, mock_get_group, mock_get_post
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup()
        mock_get_post.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            list_post_comments_service(group_id=uuid4(), post_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestBuildCommentDTO:

    def test_uses_a_placeholder_email_when_the_user_row_is_missing(self):
        comment = MockComment()
        comment.user = None

        dto = build_comment_dto(comment)

        assert dto.user_email == "unknown@example.com"

    def test_leaves_updated_at_null_when_never_edited(self):
        comment = MockComment()
        comment.updated_at = None

        dto = build_comment_dto(comment)

        assert dto.updated_at is None
        assert dto.created_at == comment.created_at.isoformat()


class TestCreatePostCommentService:

    @patch('pecha_api.group_posts.comment_service.create_comment')
    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_create_comment_success(
        self, mock_session, mock_get_group, mock_get_post, mock_create
    ):
        group_id = uuid4()
        post_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_post.return_value = MockPost(id=post_id, group_id=group_id)

        user = MockUser(email="commenter@example.com")
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_create.return_value = MockComment(
            user=user, user_id=user.id, post_id=post_id, text="Hello"
        )

        result = create_post_comment_service(
            group_id=group_id,
            post_id=post_id,
            author_email="commenter@example.com",
            text="Hello",
        )

        assert result.text == "Hello"
        assert result.user_id == user.id
        assert result.user_email == "commenter@example.com"

        persisted = mock_create.call_args.kwargs["comment"]
        assert persisted.post_id == post_id
        assert persisted.user_id == user.id
        assert persisted.text == "Hello"

    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_create_comment_user_not_found(
        self, mock_session, mock_get_group, mock_get_post
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup()
        mock_get_post.return_value = MockPost()

        # Mock the db.query().filter().first() chain to return None
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            create_post_comment_service(
                group_id=uuid4(),
                post_id=uuid4(),
                author_email="test@example.com",
                text="Hello",
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeletePostCommentService:

    @patch('pecha_api.group_posts.comment_service.soft_delete_comment')
    @patch('pecha_api.group_posts.comment_service.get_comment_by_id')
    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_delete_own_comment_success(
        self, mock_session, mock_get_group, mock_get_post,
        mock_get_comment, mock_soft_delete
    ):
        group_id = uuid4()
        post_id = uuid4()
        comment_id = uuid4()
        user_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_post.return_value = MockPost(id=post_id, group_id=group_id)
        comment = MockComment(user_id=user_id, post_id=post_id)
        comment.id = comment_id
        mock_get_comment.return_value = comment

        delete_post_comment_service(
            group_id=group_id,
            post_id=post_id,
            comment_id=comment_id,
            user_id=user_id,
        )

        mock_soft_delete.assert_called_once_with(db=mock_db, comment=comment)

    @patch('pecha_api.group_posts.comment_service.get_comment_by_id')
    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_delete_comment_permission_denied(
        self, mock_session, mock_get_group, mock_get_post, mock_get_comment
    ):
        group_id = uuid4()
        post_id = uuid4()
        comment_id = uuid4()
        user_id = uuid4()
        other_user_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_post.return_value = MockPost(id=post_id, group_id=group_id)
        comment = MockComment(user_id=other_user_id, post_id=post_id)
        comment.id = comment_id
        mock_get_comment.return_value = comment

        with pytest.raises(HTTPException) as exc_info:
            delete_post_comment_service(
                group_id=group_id,
                post_id=post_id,
                comment_id=comment_id,
                user_id=user_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_posts.comment_service.get_comment_by_id')
    @patch('pecha_api.group_posts.comment_service.get_post_by_id')
    @patch('pecha_api.group_posts.comment_service.get_group_by_id')
    @patch('pecha_api.group_posts.comment_service.SessionLocal')
    def test_delete_comment_not_found(
        self, mock_session, mock_get_group, mock_get_post, mock_get_comment
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup()
        mock_get_post.return_value = MockPost()
        mock_get_comment.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_post_comment_service(
                group_id=uuid4(),
                post_id=uuid4(),
                comment_id=uuid4(),
                user_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
