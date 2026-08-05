"""Tests for group post like service."""
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.group_posts.like_service import (
    like_post_service,
    unlike_post_service,
    list_post_likers_service,
)


class MockGroup:
    def __init__(self, id, is_public=True):
        self.id = id
        self.is_public = is_public


class MockPost:
    def __init__(self, id, group_id):
        self.id = id
        self.group_id = group_id


class MockUser:
    def __init__(self, id=None, email="user@example.com"):
        self.id = id or uuid4()
        self.email = email


class MockLike:
    def __init__(self, post_id, user_id, created_at=None):
        self.post_id = post_id
        self.user_id = user_id
        self.created_at = created_at or "2024-01-01T00:00:00"
        self.user = MockUser(id=user_id)


class TestLikePostService:

    @patch('pecha_api.group_posts.like_service.count_post_likes')
    @patch('pecha_api.group_posts.like_service.create_like')
    @patch('pecha_api.group_posts.like_service.resolve_user_id')
    @patch('pecha_api.group_posts.like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.like_service._get_and_validate_post')
    @patch('pecha_api.group_posts.like_service.SessionLocal')
    def test_like_post_creates_new_like(
        self,
        mock_session,
        mock_get_post,
        mock_validate_group,
        mock_resolve_user,
        mock_create_like,
        mock_count_likes,
    ):
        """Test liking a post creates a new like and returns is_new=True."""
        post_id = uuid4()
        group_id = uuid4()
        user_id = uuid4()
        
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_post.return_value = (MockPost(post_id, group_id), group_id)
        mock_resolve_user.return_value = user_id
        
        mock_like = MockLike(post_id, user_id)
        mock_create_like.return_value = (mock_like, True)  # is_new=True
        mock_count_likes.return_value = 1

        result = like_post_service(
            post_id=post_id,
            author_email="user@example.com",
        )

        assert result.post_id == post_id
        assert result.user_id == user_id
        assert result.liked is True
        assert result.like_count == 1
        assert result.is_new is True
        mock_validate_group.assert_called_once_with(mock_db, group_id)

    @patch('pecha_api.group_posts.like_service.count_post_likes')
    @patch('pecha_api.group_posts.like_service.create_like')
    @patch('pecha_api.group_posts.like_service.resolve_user_id')
    @patch('pecha_api.group_posts.like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.like_service._get_and_validate_post')
    @patch('pecha_api.group_posts.like_service.SessionLocal')
    def test_like_post_already_liked(
        self,
        mock_session,
        mock_get_post,
        mock_validate_group,
        mock_resolve_user,
        mock_create_like,
        mock_count_likes,
    ):
        """Test liking an already-liked post returns is_new=False."""
        post_id = uuid4()
        group_id = uuid4()
        user_id = uuid4()
        
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_post.return_value = (MockPost(post_id, group_id), group_id)
        mock_resolve_user.return_value = user_id
        
        mock_like = MockLike(post_id, user_id)
        mock_create_like.return_value = (mock_like, False)  # is_new=False (already existed)
        mock_count_likes.return_value = 5

        result = like_post_service(
            post_id=post_id,
            author_email="user@example.com",
        )

        assert result.post_id == post_id
        assert result.user_id == user_id
        assert result.liked is True
        assert result.like_count == 5
        assert result.is_new is False

    @patch('pecha_api.group_posts.like_service._get_and_validate_post')
    @patch('pecha_api.group_posts.like_service.SessionLocal')
    def test_like_post_not_found(self, mock_session, mock_get_post):
        """Test liking a non-existent post raises 404."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_post.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT_FOUND"
        )

        with pytest.raises(HTTPException) as exc_info:
            like_post_service(
                post_id=uuid4(),
                author_email="user@example.com",
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestUnlikePostService:

    @patch('pecha_api.group_posts.like_service.delete_like')
    @patch('pecha_api.group_posts.like_service.resolve_user_id')
    @patch('pecha_api.group_posts.like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.like_service._get_and_validate_post')
    @patch('pecha_api.group_posts.like_service.SessionLocal')
    def test_unlike_post_success(
        self,
        mock_session,
        mock_get_post,
        mock_validate_group,
        mock_resolve_user,
        mock_delete_like,
    ):
        """Test unliking a post succeeds."""
        post_id = uuid4()
        group_id = uuid4()
        user_id = uuid4()
        
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_post.return_value = (MockPost(post_id, group_id), group_id)
        mock_resolve_user.return_value = user_id

        unlike_post_service(
            post_id=post_id,
            author_email="user@example.com",
        )

        mock_delete_like.assert_called_once_with(db=mock_db, post_id=post_id, user_id=user_id)


class TestListPostLikersService:

    @patch('pecha_api.group_posts.like_service.get_post_likers')
    @patch('pecha_api.group_posts.like_service.validate_group_is_public')
    @patch('pecha_api.group_posts.like_service._get_and_validate_post')
    @patch('pecha_api.group_posts.like_service.SessionLocal')
    def test_list_post_likers_success(
        self,
        mock_session,
        mock_get_post,
        mock_validate_group,
        mock_get_likers,
    ):
        """Test listing post likers returns correct response."""
        post_id = uuid4()
        group_id = uuid4()
        
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_post.return_value = (MockPost(post_id, group_id), group_id)
        
        likes = [
            MockLike(post_id, uuid4()),
            MockLike(post_id, uuid4()),
        ]
        mock_get_likers.return_value = (likes, 2)

        result = list_post_likers_service(
            post_id=post_id,
            skip=0,
            limit=20,
        )

        assert len(result.likes) == 2
        assert result.total == 2
        assert result.skip == 0
        assert result.limit == 20
        mock_get_likers.assert_called_once_with(db=mock_db, post_id=post_id, skip=0, limit=20)
