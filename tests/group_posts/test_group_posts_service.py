import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

from pecha_api.group_posts.enums import GroupPostMediaType, GroupPostStatus
from pecha_api.group_posts.response_models import GroupPostDTO, GroupPostsResponse
from pecha_api.group_posts.service import (
    _generate_presigned_url,
    _isoformat,
    get_group_post_detail_service,
    list_group_posts_service,
    list_public_group_posts_service,
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


class TestGeneratePresignedUrl:
    """A media URL that cannot be signed must degrade to null rather than
    failing the whole feed."""

    def test_returns_none_without_a_key(self):
        assert _generate_presigned_url(None) is None
        assert _generate_presigned_url("") is None

    @patch('pecha_api.group_posts.service.get')
    @patch('pecha_api.group_posts.service.generate_presigned_access_url')
    def test_signs_the_key_with_the_configured_bucket(self, mock_generate, mock_get):
        mock_get.return_value = "media-bucket"
        mock_generate.return_value = "https://presigned/a.webp"

        assert _generate_presigned_url("groups/g/posts/a.webp") == "https://presigned/a.webp"
        mock_generate.assert_called_once_with(
            bucket_name="media-bucket",
            s3_key="groups/g/posts/a.webp",
        )

    @patch('pecha_api.group_posts.service.get')
    @patch('pecha_api.group_posts.service.generate_presigned_access_url')
    def test_returns_none_when_signing_fails(self, mock_generate, mock_get):
        mock_get.return_value = "media-bucket"
        mock_generate.side_effect = RuntimeError("s3 unavailable")

        assert _generate_presigned_url("groups/g/posts/a.webp") is None


class TestIsoformat:

    def test_returns_none_for_none(self):
        assert _isoformat(None) is None

    def test_formats_datetimes(self):
        value = datetime(2026, 7, 27, 12, 30, tzinfo=tz.utc)

        assert _isoformat(value) == value.isoformat()

    def test_falls_back_to_str_for_other_values(self):
        assert _isoformat(42) == "42"


class TestListGroupPostsService:
    """Test cases for the public feed."""

    @patch('pecha_api.group_posts.comment_repository.get_comment_counts_by_post_ids')
    @patch('pecha_api.group_posts.like_repository.get_like_counts_by_post_ids')
    @patch('pecha_api.plans.authors.plan_authors_repository.get_authors_by_emails')
    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_groups_by_ids', return_value=[])
    @patch('pecha_api.group_posts.service.get_group_posts')
    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_success_only_published(
        self,
        mock_session,
        mock_get_group,
        mock_get_posts,
        _mock_groups,
        mock_presign,
        mock_get_authors,
        mock_like_counts,
        mock_comment_counts,
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

        author = MagicMock()
        author.email = "author@example.com"
        author.first_name = "Tenzin"
        author.last_name = "Gyatsu"
        author.image_url = "authors/tenzin.webp"
        mock_get_authors.return_value = [author]
        mock_like_counts.return_value = {post.id: 3}
        mock_comment_counts.return_value = {post.id: 5}

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
        assert dto.creator_name == "Tenzin Gyatsu"
        assert dto.creator_image_url == "https://presigned/authors/tenzin.webp"
        assert dto.like_count == 3
        assert dto.comment_count == 5

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

    @patch('pecha_api.group_posts.service.get_posts_for_group_ids')
    @patch('pecha_api.group_posts.service.resolve_public_group_scope')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_public_posts_defaults_to_followed_groups(
        self,
        mock_session,
        mock_resolve_scope,
        mock_get_posts,
    ):
        followed_group_id = uuid4()
        user_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_resolve_scope.return_value = (
            [followed_group_id],
            {followed_group_id},
        )
        mock_get_posts.return_value = ([], 0)

        result = list_public_group_posts_service(
            user_id=user_id,
        )

        assert result.posts == []
        assert result.total == 0
        assert mock_resolve_scope.call_args.kwargs[
            "should_include_unfollowed"
        ] is False
        assert mock_get_posts.call_args.kwargs["group_ids"] == [
            followed_group_id
        ]

    @patch('pecha_api.group_posts.service.get_posts_for_group_ids')
    @patch('pecha_api.group_posts.service.resolve_public_group_scope')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_public_posts_can_include_unfollowed_groups(
        self,
        mock_session,
        mock_resolve_scope,
        mock_get_posts,
    ):
        public_group_ids = [uuid4(), uuid4()]
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_resolve_scope.return_value = (public_group_ids, set())
        mock_get_posts.return_value = ([], 0)

        result = list_public_group_posts_service(
            user_id=uuid4(),
            should_include_unfollowed=True,
        )

        assert result.posts == []
        assert mock_resolve_scope.call_args.kwargs[
            "should_include_unfollowed"
        ] is True
        assert mock_get_posts.call_args.kwargs["group_ids"] == public_group_ids

    @patch('pecha_api.group_posts.comment_repository.get_comment_counts_by_post_ids')
    @patch('pecha_api.group_posts.like_repository.get_like_counts_by_post_ids')
    @patch('pecha_api.plans.authors.plan_authors_repository.get_authors_by_emails')
    @patch('pecha_api.group_posts.service.get_group_posts')
    @patch('pecha_api.group_posts.service.get_group_by_id')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_list_empty(
        self,
        mock_session,
        mock_get_group,
        mock_get_posts,
        mock_get_authors,
        mock_like_counts,
        mock_comment_counts,
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_posts.return_value = ([], 0)

        result = list_group_posts_service(group_id=group_id)

        assert result.posts == []
        assert result.total == 0
        mock_get_authors.assert_not_called()
        mock_like_counts.assert_not_called()
        mock_comment_counts.assert_not_called()


class TestGetGroupPostDetailService:
    """Test cases for the public post detail."""

    @patch('pecha_api.group_posts.comment_repository.get_comment_counts_by_post_ids')
    @patch('pecha_api.group_posts.like_repository.get_like_counts_by_post_ids')
    @patch('pecha_api.plans.authors.plan_authors_repository.get_authors_by_emails')
    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_groups_by_ids', return_value=[])
    @patch('pecha_api.group_posts.service.get_post_by_id_only')
    @patch('pecha_api.group_posts.service._validate_group_is_public')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_detail_success(
        self,
        mock_session,
        mock_validate_group,
        mock_get_post,
        _mock_groups,
        mock_presign,
        mock_get_authors,
        mock_like_counts,
        mock_comment_counts,
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_presign.return_value = None
        mock_get_authors.return_value = []
        mock_like_counts.return_value = {}
        mock_comment_counts.return_value = {}

        post = MockGroupPost(group_id=group_id)
        mock_get_post.return_value = post

        result = get_group_post_detail_service(post_id=post.id)

        assert isinstance(result, GroupPostDTO)
        assert result.id == post.id
        assert result.group_id == group_id
        assert result.like_count == 0
        assert result.comment_count == 0
        assert result.liked_by_me is False
        mock_validate_group.assert_called_once()

    @patch('pecha_api.group_posts.service.get_post_by_id_only')
    @patch('pecha_api.group_posts.service.SessionLocal')
    def test_detail_only_queries_published(self, mock_session, mock_get_post):
        """HIDDEN and soft-deleted posts must be invisible publicly: the lookup
        is constrained to PUBLISHED and a miss returns 404."""
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_post.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_group_post_detail_service(post_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        _, kwargs = mock_get_post.call_args
        assert kwargs["status"] == GroupPostStatus.PUBLISHED
