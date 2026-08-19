"""Tests for group post comment like service."""
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.group_posts.comment_like_service import (
    like_comment_service,
    unlike_comment_service,
    list_comment_likers_service,
)


class MockPost:
    def __init__(self, id, group_id):
        self.id = id
        self.group_id = group_id


class MockComment:
    def __init__(self, id, post_id):
        self.id = id
        self.post_id = post_id


class MockUser:
    def __init__(self, id=None, email="user@example.com"):
        self.id = id or uuid4()
        self.email = email


class MockCommentLike:
    def __init__(self, comment_id, user_id, created_at=None):
        self.comment_id = comment_id
        self.user_id = user_id
        self.created_at = created_at or "2024-01-01T00:00:00"
        self.user = MockUser(id=user_id)


class TestLikeCommentService:

    @patch('pecha_api.group_posts.comment_like_service.count_comment_likes')
    @patch('pecha_api.group_posts.comment_like_service.create_like')
    @patch('pecha_api.group_posts.comment_like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.comment_like_service._get_and_validate_comment')
    @patch('pecha_api.group_posts.comment_like_service.SessionLocal')
    def test_like_comment_creates_new_like(
        self,
        mock_session,
        mock_get_comment,
        mock_validate_group,
        mock_create_like,
        mock_count_likes,
    ):
        """Test liking a comment creates a new like and returns is_new=True."""
        comment_id = uuid4()
        post_id = uuid4()
        group_id = uuid4()
        user_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_comment = MockComment(comment_id, post_id)
        mock_post = MockPost(post_id, group_id)
        mock_get_comment.return_value = (mock_comment, mock_post, group_id)

        mock_like = MockCommentLike(comment_id, user_id)
        mock_create_like.return_value = (mock_like, True)  # is_new=True
        mock_count_likes.return_value = 1

        result = like_comment_service(
            comment_id=comment_id,
            user_id=user_id,
        )

        assert result.comment_id == comment_id
        assert result.user_id == user_id
        assert result.liked is True
        assert result.like_count == 1
        assert result.is_new is True
        mock_validate_group.assert_called_once_with(mock_db, group_id)

    @patch('pecha_api.group_posts.comment_like_service.count_comment_likes')
    @patch('pecha_api.group_posts.comment_like_service.create_like')
    @patch('pecha_api.group_posts.comment_like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.comment_like_service._get_and_validate_comment')
    @patch('pecha_api.group_posts.comment_like_service.SessionLocal')
    def test_like_comment_already_liked(
        self,
        mock_session,
        mock_get_comment,
        mock_validate_group,
        mock_create_like,
        mock_count_likes,
    ):
        """Test liking an already-liked comment returns is_new=False."""
        comment_id = uuid4()
        post_id = uuid4()
        group_id = uuid4()
        user_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_comment = MockComment(comment_id, post_id)
        mock_post = MockPost(post_id, group_id)
        mock_get_comment.return_value = (mock_comment, mock_post, group_id)

        mock_like = MockCommentLike(comment_id, user_id)
        mock_create_like.return_value = (mock_like, False)  # is_new=False (already existed)
        mock_count_likes.return_value = 3

        result = like_comment_service(
            comment_id=comment_id,
            user_id=user_id,
        )

        assert result.comment_id == comment_id
        assert result.user_id == user_id
        assert result.liked is True
        assert result.like_count == 3
        assert result.is_new is False

    @patch('pecha_api.group_posts.comment_like_service._get_and_validate_comment')
    @patch('pecha_api.group_posts.comment_like_service.SessionLocal')
    def test_like_comment_not_found(self, mock_session, mock_get_comment):
        """Test liking a non-existent comment raises 404."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_comment.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT_FOUND"
        )

        with pytest.raises(HTTPException) as exc_info:
            like_comment_service(
                comment_id=uuid4(),
                user_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestUnlikeCommentService:

    @patch('pecha_api.group_posts.comment_like_service.delete_like')
    @patch('pecha_api.group_posts.comment_like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.comment_like_service._get_and_validate_comment')
    @patch('pecha_api.group_posts.comment_like_service.SessionLocal')
    def test_unlike_comment_success(
        self,
        mock_session,
        mock_get_comment,
        mock_validate_group,
        mock_delete_like,
    ):
        """Test unliking a comment succeeds."""
        comment_id = uuid4()
        post_id = uuid4()
        group_id = uuid4()
        user_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_comment = MockComment(comment_id, post_id)
        mock_post = MockPost(post_id, group_id)
        mock_get_comment.return_value = (mock_comment, mock_post, group_id)

        unlike_comment_service(
            comment_id=comment_id,
            user_id=user_id,
        )

        mock_delete_like.assert_called_once_with(db=mock_db, comment_id=comment_id, user_id=user_id)


class TestListCommentLikersService:

    @patch('pecha_api.group_posts.comment_like_service.get_comment_likers')
    @patch('pecha_api.group_posts.comment_like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.comment_like_service._get_and_validate_comment')
    @patch('pecha_api.group_posts.comment_like_service.SessionLocal')
    def test_list_comment_likers_success(
        self,
        mock_session,
        mock_get_comment,
        mock_validate_group,
        mock_get_likers,
    ):
        """Test listing comment likers returns correct response."""
        comment_id = uuid4()
        post_id = uuid4()
        group_id = uuid4()
        
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_comment = MockComment(comment_id, post_id)
        mock_post = MockPost(post_id, group_id)
        mock_get_comment.return_value = (mock_comment, mock_post, group_id)
        
        likes = [
            MockCommentLike(comment_id, uuid4()),
            MockCommentLike(comment_id, uuid4()),
            MockCommentLike(comment_id, uuid4()),
        ]
        mock_get_likers.return_value = (likes, 3)

        result = list_comment_likers_service(
            comment_id=comment_id,
            skip=0,
            limit=20,
        )

        assert len(result.likes) == 3
        assert result.total == 3
        assert result.skip == 0
        assert result.limit == 20
        mock_get_likers.assert_called_once_with(db=mock_db, comment_id=comment_id, skip=0, limit=20)
