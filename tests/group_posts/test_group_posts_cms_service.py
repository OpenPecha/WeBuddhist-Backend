import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

from pecha_api.group_posts.cms_service import (
    EMPTY_POST_MESSAGE,
    MAX_MEDIA_ITEMS_MESSAGE,
    MAX_MEDIA_ITEMS_PER_POST,
    cms_create_group_post_service,
    cms_delete_group_post_service,
    cms_get_group_post_detail_service,
    cms_list_group_posts_service,
    cms_replace_group_post_links_service,
    cms_replace_group_post_media_service,
    cms_update_group_post_service,
)
from pecha_api.group_posts.enums import GroupPostMediaType, GroupPostStatus
from pecha_api.group_posts.response_models import (
    CreateGroupPostRequest,
    GroupPostDTO,
    GroupPostLinkRequest,
    GroupPostMediaRequest,
    GroupPostsResponse,
    ReplaceGroupPostLinksRequest,
    ReplaceGroupPostMediaRequest,
    UpdateGroupPostRequest,
)


class MockGroup:
    """Mock AuthorGroup model."""
    def __init__(self, id=None):
        self.id = id or uuid4()
        self.is_public = True


class MockAuthor:
    """Mock Author model."""
    def __init__(self, email="author@example.com"):
        self.id = uuid4()
        self.email = email


class MockGroupPost:
    """Mock GroupPost model."""
    def __init__(
        self,
        group_id=None,
        caption="Caption",
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


def _media_request(display_order=1, media_key="groups/g/posts/a.webp"):
    return GroupPostMediaRequest(
        media_type=GroupPostMediaType.IMAGE,
        media_key=media_key,
        display_order=display_order,
    )


def _link_request(display_order=1, url="https://example.com"):
    return GroupPostLinkRequest(type="EXTERNAL", url=url, display_order=display_order)


def _assign_ids(post):
    """Simulate the ids the database would assign on commit."""
    for entry in post.media:
        entry.id = entry.id or uuid4()
    for entry in post.links:
        entry.id = entry.id or uuid4()
    return post


class TestCmsListGroupPostsService:

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_groups_by_ids', return_value=[])
    @patch('pecha_api.group_posts.cms_service.get_group_posts')
    @patch('pecha_api.group_posts.cms_service.require_can_read_group_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_list_passes_status_filter(
        self, mock_session, mock_validate, mock_get_group,
        mock_require_read, mock_get_posts, _mock_groups, mock_presign
    ):
        group_id = uuid4()
        author = MockAuthor()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None
        mock_get_posts.return_value = ([MockGroupPost(group_id=group_id, status=GroupPostStatus.HIDDEN)], 1)

        result = cms_list_group_posts_service(
            token="cms_token",
            group_id=group_id,
            status_filter=GroupPostStatus.HIDDEN,
        )

        assert isinstance(result, GroupPostsResponse)
        assert result.posts[0].status == "HIDDEN"
        mock_require_read.assert_called_once_with(db=mock_db, group_id=group_id, author=author)
        _, kwargs = mock_get_posts.call_args
        assert kwargs["status"] == GroupPostStatus.HIDDEN

    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_list_group_not_found(self, mock_session, mock_validate, mock_get_group):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            cms_list_group_posts_service(token="cms_token", group_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCmsGetGroupPostDetailService:

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_groups_by_ids', return_value=[])
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_read_group_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_detail_includes_hidden_posts(
        self, mock_session, mock_validate, mock_get_group,
        mock_require_read, mock_get_post, _mock_groups, mock_presign
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None
        post = MockGroupPost(group_id=group_id, status=GroupPostStatus.HIDDEN)
        mock_get_post.return_value = post

        result = cms_get_group_post_detail_service(
            token="cms_token", group_id=group_id, post_id=post.id
        )

        assert result.status == "HIDDEN"
        # CMS lookups must not constrain status, so HIDDEN posts stay visible.
        _, kwargs = mock_get_post.call_args
        assert "status" not in kwargs or kwargs["status"] is None

    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_read_group_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_detail_not_found(
        self, mock_session, mock_validate, mock_get_group, mock_require_read, mock_get_post
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup()
        mock_get_post.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            cms_get_group_post_detail_service(
                token="cms_token", group_id=uuid4(), post_id=uuid4()
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCmsCreateGroupPostService:

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.cms_service.create_post')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_create_success_renumbers_media(
        self, mock_session, mock_validate, mock_get_group,
        mock_require_create, mock_create_post, mock_presign
    ):
        group_id = uuid4()
        author = MockAuthor(email="creator@example.com")
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None

        def fake_create(db, post):
            post.id = post.id or uuid4()
            return _assign_ids(post)

        mock_create_post.side_effect = fake_create

        request = CreateGroupPostRequest(
            caption="Hello",
            media=[
                _media_request(display_order=5, media_key="groups/g/posts/second.webp"),
                _media_request(display_order=2, media_key="groups/g/posts/first.webp"),
            ],
            links=[_link_request()],
        )

        result = cms_create_group_post_service(
            token="cms_token", group_id=group_id, request=request
        )

        assert isinstance(result, GroupPostDTO)
        mock_require_create.assert_called_once_with(db=mock_db, group_id=group_id, author=author)

        created_post = mock_create_post.call_args.kwargs["post"]
        assert created_post.created_by == "creator@example.com"
        assert created_post.published_at is not None
        # Requested orders (5, 2) are sorted then renumbered 1..n.
        assert [m.display_order for m in created_post.media] == [1, 2]
        assert created_post.media[0].media_key == "groups/g/posts/first.webp"
        assert created_post.media[1].media_key == "groups/g/posts/second.webp"

    @patch('pecha_api.group_posts.cms_service.create_post')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    def test_create_empty_post_rejected(self, mock_validate, mock_create_post):
        mock_validate.return_value = MockAuthor()

        request = CreateGroupPostRequest(caption="   ", media=[], links=[])

        with pytest.raises(HTTPException) as exc_info:
            cms_create_group_post_service(
                token="cms_token", group_id=uuid4(), request=request
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == EMPTY_POST_MESSAGE
        mock_create_post.assert_not_called()

    @patch('pecha_api.group_posts.cms_service.create_post')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    def test_create_too_many_media_rejected(self, mock_validate, mock_create_post):
        mock_validate.return_value = MockAuthor()

        request = CreateGroupPostRequest(
            media=[
                _media_request(display_order=index + 1, media_key=f"groups/g/posts/{index}.webp")
                for index in range(MAX_MEDIA_ITEMS_PER_POST + 1)
            ],
        )

        with pytest.raises(HTTPException) as exc_info:
            cms_create_group_post_service(
                token="cms_token", group_id=uuid4(), request=request
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == MAX_MEDIA_ITEMS_MESSAGE
        mock_create_post.assert_not_called()

    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_create_permission_denied(
        self, mock_session, mock_validate, mock_get_group, mock_require_create
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup()
        mock_require_create.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="NO_GROUP_MEMBERSHIP"
        )

        with pytest.raises(HTTPException) as exc_info:
            cms_create_group_post_service(
                token="cms_token", group_id=uuid4(),
                request=CreateGroupPostRequest(caption="Hello"),
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestCmsUpdateGroupPostService:

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_groups_by_ids', return_value=[])
    @patch('pecha_api.group_posts.cms_service.update_post')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_change_status')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_update_caption_does_not_require_status_permission(
        self, mock_session, mock_validate, mock_get_group, mock_require_create,
        mock_require_status, mock_get_post, mock_update_post, _mock_groups, mock_presign
    ):
        group_id = uuid4()
        author = MockAuthor()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None
        post = MockGroupPost(group_id=group_id, caption="Old caption")
        mock_get_post.return_value = post
        mock_update_post.side_effect = lambda db, post: post

        result = cms_update_group_post_service(
            token="cms_token",
            group_id=group_id,
            post_id=post.id,
            request=UpdateGroupPostRequest(caption="New caption"),
        )

        assert result.caption == "New caption"
        assert post.updated_by == author.email
        mock_require_status.assert_not_called()

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_groups_by_ids', return_value=[])
    @patch('pecha_api.group_posts.cms_service.update_post')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_change_status')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_update_status_change_requires_status_permission(
        self, mock_session, mock_validate, mock_get_group, mock_require_create,
        mock_require_status, mock_get_post, mock_update_post, _mock_groups, mock_presign
    ):
        group_id = uuid4()
        author = MockAuthor()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None
        post = MockGroupPost(group_id=group_id, status=GroupPostStatus.PUBLISHED)
        mock_get_post.return_value = post
        mock_update_post.side_effect = lambda db, post: post

        result = cms_update_group_post_service(
            token="cms_token",
            group_id=group_id,
            post_id=post.id,
            request=UpdateGroupPostRequest(status=GroupPostStatus.HIDDEN),
        )

        assert result.status == "HIDDEN"
        mock_require_status.assert_called_once_with(db=mock_db, group_id=group_id, author=author)

    @patch('pecha_api.group_posts.cms_service.update_post')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_update_cannot_clear_last_content(
        self, mock_session, mock_validate, mock_get_group,
        mock_require_create, mock_get_post, mock_update_post
    ):
        """Clearing the caption of a caption-only post would leave it empty."""
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        post = MockGroupPost(group_id=group_id, caption="Only content", media=[], links=[])
        mock_get_post.return_value = post

        with pytest.raises(HTTPException) as exc_info:
            cms_update_group_post_service(
                token="cms_token",
                group_id=group_id,
                post_id=post.id,
                request=UpdateGroupPostRequest(caption=""),
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == EMPTY_POST_MESSAGE
        mock_update_post.assert_not_called()

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.service.get_groups_by_ids', return_value=[])
    @patch('pecha_api.group_posts.cms_service.update_post')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_change_status')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_update_overrides_published_at(
        self, mock_session, mock_validate, mock_get_group, mock_require_create,
        mock_require_status, mock_get_post, mock_update_post, _mock_groups, mock_presign
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None
        post = MockGroupPost(group_id=group_id)
        mock_get_post.return_value = post
        mock_update_post.side_effect = lambda db, post: post

        backdated = datetime(2026, 1, 15, 9, 0, tzinfo=tz.utc)
        result = cms_update_group_post_service(
            token="cms_token",
            group_id=group_id,
            post_id=post.id,
            request=UpdateGroupPostRequest(published_at=backdated),
        )

        assert post.published_at == backdated
        assert result.published_at == backdated.isoformat()
        mock_require_status.assert_not_called()

    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_update_post_not_found(
        self, mock_session, mock_validate, mock_get_group, mock_require_create, mock_get_post
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup()
        mock_get_post.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            cms_update_group_post_service(
                token="cms_token",
                group_id=uuid4(),
                post_id=uuid4(),
                request=UpdateGroupPostRequest(caption="New"),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCmsReplaceGroupPostMediaService:

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.cms_service.replace_post_media')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_replace_media_success(
        self, mock_session, mock_validate, mock_get_group, mock_require_create,
        mock_get_post, mock_replace, mock_presign
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None
        post = MockGroupPost(group_id=group_id, caption="Keeps content")
        mock_get_post.return_value = post

        def fake_replace(db, post, media):
            post.media = media
            return _assign_ids(post)

        mock_replace.side_effect = fake_replace

        request = ReplaceGroupPostMediaRequest(
            media=[
                _media_request(display_order=9, media_key="groups/g/posts/z.webp"),
                _media_request(display_order=3, media_key="groups/g/posts/a.webp"),
            ]
        )

        result = cms_replace_group_post_media_service(
            token="cms_token", group_id=group_id, post_id=post.id, request=request
        )

        replaced_media = mock_replace.call_args.kwargs["media"]
        assert [m.display_order for m in replaced_media] == [1, 2]
        assert replaced_media[0].media_key == "groups/g/posts/a.webp"
        assert all(m.post_id == post.id for m in replaced_media)
        assert len(result.media) == 2

    @patch('pecha_api.group_posts.cms_service.replace_post_media')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_replace_media_cannot_empty_media_only_post(
        self, mock_session, mock_validate, mock_get_group, mock_require_create,
        mock_get_post, mock_replace
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        post = MockGroupPost(group_id=group_id, caption=None, media=[MagicMock()], links=[])
        mock_get_post.return_value = post

        with pytest.raises(HTTPException) as exc_info:
            cms_replace_group_post_media_service(
                token="cms_token",
                group_id=group_id,
                post_id=post.id,
                request=ReplaceGroupPostMediaRequest(media=[]),
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == EMPTY_POST_MESSAGE
        mock_replace.assert_not_called()

    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    def test_replace_media_over_limit_rejected(self, mock_validate):
        mock_validate.return_value = MockAuthor()

        request = ReplaceGroupPostMediaRequest(
            media=[
                _media_request(display_order=index + 1, media_key=f"groups/g/posts/{index}.webp")
                for index in range(MAX_MEDIA_ITEMS_PER_POST + 1)
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            cms_replace_group_post_media_service(
                token="cms_token", group_id=uuid4(), post_id=uuid4(), request=request
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == MAX_MEDIA_ITEMS_MESSAGE


class TestCmsReplaceGroupPostLinksService:

    @patch('pecha_api.group_posts.service._generate_presigned_url')
    @patch('pecha_api.group_posts.cms_service.replace_post_links')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_replace_links_success(
        self, mock_session, mock_validate, mock_get_group, mock_require_create,
        mock_get_post, mock_replace, mock_presign
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_presign.return_value = None
        post = MockGroupPost(group_id=group_id, caption="Keeps content")
        mock_get_post.return_value = post

        def fake_replace(db, post, links):
            post.links = links
            for entry in links:
                entry.id = entry.id or uuid4()
            return post

        mock_replace.side_effect = fake_replace

        request = ReplaceGroupPostLinksRequest(
            links=[
                _link_request(display_order=2, url="https://example.com/b"),
                _link_request(display_order=1, url="https://example.com/a"),
            ]
        )

        result = cms_replace_group_post_links_service(
            token="cms_token", group_id=group_id, post_id=post.id, request=request
        )

        replaced_links = mock_replace.call_args.kwargs["links"]
        assert [entry.display_order for entry in replaced_links] == [1, 2]
        assert replaced_links[0].url == "https://example.com/a"
        assert len(result.links) == 2

    @patch('pecha_api.group_posts.cms_service.replace_post_links')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_create_content')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_replace_links_cannot_empty_links_only_post(
        self, mock_session, mock_validate, mock_get_group, mock_require_create,
        mock_get_post, mock_replace
    ):
        group_id = uuid4()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        post = MockGroupPost(group_id=group_id, caption=None, media=[], links=[MagicMock()])
        mock_get_post.return_value = post

        with pytest.raises(HTTPException) as exc_info:
            cms_replace_group_post_links_service(
                token="cms_token",
                group_id=group_id,
                post_id=post.id,
                request=ReplaceGroupPostLinksRequest(links=[]),
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == EMPTY_POST_MESSAGE
        mock_replace.assert_not_called()


class TestCmsDeleteGroupPostService:

    @patch('pecha_api.group_posts.cms_service.soft_delete_post')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_change_status')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_delete_requires_status_permission_and_soft_deletes(
        self, mock_session, mock_validate, mock_get_group,
        mock_require_status, mock_get_post, mock_soft_delete
    ):
        group_id = uuid4()
        author = MockAuthor(email="admin@example.com")
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        post = MockGroupPost(group_id=group_id)
        mock_get_post.return_value = post

        cms_delete_group_post_service(token="cms_token", group_id=group_id, post_id=post.id)

        mock_require_status.assert_called_once_with(db=mock_db, group_id=group_id, author=author)
        mock_soft_delete.assert_called_once_with(db=mock_db, post=post, deleted_by="admin@example.com")

    @patch('pecha_api.group_posts.cms_service.soft_delete_post')
    @patch('pecha_api.group_posts.cms_service.get_post_by_id')
    @patch('pecha_api.group_posts.cms_service.require_can_change_status')
    @patch('pecha_api.group_posts.cms_service.get_group_by_id')
    @patch('pecha_api.group_posts.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_posts.cms_service.SessionLocal')
    def test_delete_post_not_found(
        self, mock_session, mock_validate, mock_get_group,
        mock_require_status, mock_get_post, mock_soft_delete
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup()
        mock_get_post.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            cms_delete_group_post_service(token="cms_token", group_id=uuid4(), post_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        mock_soft_delete.assert_not_called()
