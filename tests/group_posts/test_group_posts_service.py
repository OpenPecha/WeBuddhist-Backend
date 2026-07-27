import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

from pecha_api.group_posts.enums import GroupPostMediaType, GroupPostStatus
from pecha_api.group_posts.response_models import GroupPostDTO, GroupPostsResponse
from pecha_api.group_posts.service import (
    get_group_post_detail_service,
    list_group_posts_service,
)


class MockGroup:
    """Mock AuthorGroup model."""
    def __init__(self, id=None, is_public=True):
        self.id = id or uuid4()
        self.is_public = is_public


class MockGroupPostMedia:
    """Mock GroupPostMedia model."""
    def __init__(
        self,
        media_type=GroupPostMediaType.IMAGE,
        media_key="groups/g/posts/a.webp",
        thumbnail_key=None,
        width=None,
        height=None,
        duration_ms=None,
        display_order=1,
    ):
        self.id = uuid4()
        self.media_type = media_type
        self.media_key = media_key
        self.thumbnail_key = thumbnail_key
        self.width = width
        self.height = height
        self.duration_ms = duration_ms
        self.display_order = display_order


class MockGroupPostLink:
    """Mock GroupPostLink model."""
    def __init__(self, type="EXTERNAL", url="https://example.com", label=None, display_order=1):
        self.id = uuid4()
        self.type = type
        self.url = url
        self.label = label
        self.display_order = display_order


class MockGroupPost:
    """Mock GroupPost model."""
    def __init__(
        self,
        group_id=None,
        caption="Evening practice notes",
        status=GroupPostStatus.PUBLISHED,
        media=None,
        links=None,
    ):
        self.id = uuid4()
        self.group_id = group_id or uuid4()
        self.caption = caption
        self.status = status
        self.published_at = datetime.now(tz.utc)
        self.created_at = datetime.now(tz.utc)
        self.updated_at = datetime.now(tz.utc)
        self.deleted_at = None
        self.created_by = "author@example.com"
        self.updated_by = None
        self.deleted_by = None
        self.media = media or []
        self.links = links or []


class TestListGroupPostsService:
    """Test cases for the public feed."""

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_group_posts')
    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_success_only_published(
        self, mock_session, mock_get_group, mock_get_posts, mock_presign
    ):
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.side_effect = lambda key: f"https://presigned/{key}" if key else None

        media = [
            MockGroupPostMedia(display_order=2, media_key="b.webp"),
            MockGroupPostMedia(display_order=1, media_key="a.webp", width=1080, height=1350),
        ]
        links = [MockGroupPostLink(label="Full guide")]
        post = MockGroupPost(group_id=group_id, media=media, links=links)
        mock_get_posts.return_value = ([post], 1)

        result = list_group_posts_service(group_id=group_id, skip=0, limit=20)

        assert isinstance(result, GroupPostsResponse)
        assert result.total == 1
        assert result.skip == 0
        assert result.limit == 20
        dto = result.posts[0]
        assert dto.status == "PUBLISHED"
        assert dto.caption == "Evening practice notes"
        assert [m.display_order for m in dto.media] == [1, 2]
        assert dto.media[0].url == "https://presigned/a.webp"
        assert dto.media[0].width == 1080
        assert dto.links[0].label == "Full guide"

        _, kwargs = mock_get_posts.call_args
        assert kwargs["status"] == GroupPostStatus.PUBLISHED
        assert kwargs["group_id"] == group_id

    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_group_not_found(self, mock_session, mock_get_group):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            list_group_posts_service(group_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_private_group_returns_404(self, mock_session, mock_get_group):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(is_public=False)

        with pytest.raises(HTTPException) as exc_info:
            list_group_posts_service(group_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_posts.service.get_group_posts')
    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_empty(self, mock_session, mock_get_group, mock_get_posts):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_posts.return_value = ([], 0)

        result = list_group_posts_service(group_id=group_id)

        assert result.posts == []
        assert result.total == 0


class TestGetGroupPostDetailService:
    """Test cases for the public post detail."""

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_post_by_id')
    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_detail_success(self, mock_session, mock_get_group, mock_get_post, mock_presign):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None

        post = MockGroupPost(group_id=group_id)
        mock_get_post.return_value = post

        result = get_group_post_detail_service(group_id=group_id, post_id=post.id)

        assert isinstance(result, GroupPostDTO)
        assert result.id == post.id
        assert result.group_id == group_id

    @patch('pecha_api.group_posts.service.get_post_by_id')
    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_detail_only_queries_published(self, mock_session, mock_get_group, mock_get_post):
        """HIDDEN and soft-deleted posts must be invisible publicly: the lookup
        is constrained to PUBLISHED and a miss returns 404."""
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_post.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_group_post_detail_service(group_id=group_id, post_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        _, kwargs = mock_get_post.call_args
        assert kwargs["status"] == GroupPostStatus.PUBLISHED
