from datetime import datetime, timezone as tz
from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.author_group_feed.response_models import (
    AuthorGroupFeedItemType,
    AuthorGroupFeedRequest,
)
from pecha_api.author_group_feed.service import get_author_group_feed_service
from pecha_api.events.event_response_models import EventDTO
from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.response_models import GroupPostDTO


class MockUser:
    def __init__(self):
        self.id = uuid4()
        self.email = "user@example.com"


class MockGroup:
    def __init__(self, group_id=None, is_public=True, title="Siddhartha's Intent"):
        self.id = group_id or uuid4()
        self.is_public = is_public
        self.slug = "siddharthas-intent"
        self.avatar_key = "groups/avatar.webp"
        self.metadata_entries = [MagicMock(title=title, language="EN")]


class MockPost:
    def __init__(self, group_id, published_at=None):
        self.id = uuid4()
        self.group_id = group_id
        self.published_at = published_at or datetime(2026, 8, 4, 12, 0, tzinfo=tz.utc)
        self.created_at = self.published_at
        self.updated_at = None
        self.caption = "Hello"
        self.status = GroupPostStatus.PUBLISHED
        self.created_by = "author@example.com"
        self.media = []
        self.links = []


class MockEvent:
    def __init__(self, group_id, created_at=None):
        self.id = uuid4()
        self.group_id = group_id
        self.created_at = created_at or datetime(2026, 8, 3, 12, 0, tzinfo=tz.utc)
        self.updated_at = None
        self.start_date = self.created_at
        self.end_date = self.created_at
        self.plan_id = None
        self.accumulator_id = None
        self.mantra_id = None
        self.timer_id = None
        self.group_recitation_collection_id = None
        self.location_id = None
        self.featured = False
        self.image_url = None
        self.created_by = "author@example.com"
        self.metadata_entries = []
        self.links = []
        self.location = None


def _post_dto(post: MockPost) -> GroupPostDTO:
    return GroupPostDTO(
        id=post.id,
        group_id=post.group_id,
        caption=post.caption,
        status="PUBLISHED",
        published_at=post.published_at.isoformat(),
        media=[],
        links=[],
        creator_name="Author",
        creator_image_url=None,
        like_count=0,
        comment_count=0,
        created_at=post.created_at.isoformat(),
        updated_at=None,
    )


class TestGetAuthorGroupFeedService:

    @patch("pecha_api.author_group_feed.service.get_joined_event_ids_by_user")
    @patch("pecha_api.author_group_feed.service.get_event_participant_counts")
    @patch("pecha_api.author_group_feed.service._event_to_dto")
    @patch("pecha_api.author_group_feed.service.build_post_dtos")
    @patch("pecha_api.author_group_feed.service.get_events")
    @patch("pecha_api.author_group_feed.service.get_posts_for_group_ids")
    @patch("pecha_api.author_group_feed.service.get_groups_by_ids")
    @patch("pecha_api.author_group_feed.service.get_following_group_ids_by_user")
    @patch("pecha_api.author_group_feed.service.SessionLocal")
    @patch("pecha_api.author_group_feed.service.validate_and_extract_user_details")
    def test_followed_only_mixes_posts_and_events_newest_first(
        self,
        mock_validate,
        mock_session,
        mock_following_ids,
        mock_groups_by_ids,
        mock_get_posts,
        mock_get_events,
        mock_build_posts,
        mock_event_dto,
        mock_counts,
        mock_joined,
    ):
        user = MockUser()
        followed_id = uuid4()
        mock_validate.return_value = user
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_following_ids.return_value = [followed_id]
        mock_groups_by_ids.side_effect = [
            [MockGroup(followed_id)],
            [MockGroup(followed_id)],
        ]

        post = MockPost(followed_id, published_at=datetime(2026, 8, 4, 15, 0, tzinfo=tz.utc))
        event = MockEvent(followed_id, created_at=datetime(2026, 8, 4, 10, 0, tzinfo=tz.utc))
        mock_get_posts.return_value = ([post], 1)
        mock_build_posts.return_value = [_post_dto(post)]
        mock_get_events.return_value = ([event], 1)
        mock_counts.return_value = {event.id: 2}
        mock_joined.return_value = [event.id]
        mock_event_dto.return_value = EventDTO(
            id=event.id,
            group_id=event.group_id,
            start_date=event.start_date,
            end_date=event.end_date,
            is_one_day=True,
            featured=False,
            metadata=None,
            links=[],
            participant_count=2,
            is_joined=True,
            created_at=event.created_at,
            created_by=event.created_by,
        )

        result = get_author_group_feed_service(
            token="token",
            request=AuthorGroupFeedRequest(include_unfollowed=False),
            skip=0,
            limit=20,
        )

        assert result.total == 2
        assert result.include_unfollowed is False
        assert len(result.items) == 2
        assert result.items[0].type == AuthorGroupFeedItemType.POST
        assert result.items[0].is_followed is True
        assert result.items[0].group_name == "Siddhartha's Intent"
        assert result.items[0].group_slug == "siddharthas-intent"
        assert result.items[1].type == AuthorGroupFeedItemType.EVENT
        assert result.items[1].is_followed is True

        _, post_kwargs = mock_get_posts.call_args
        assert post_kwargs["group_ids"] == [followed_id]
        assert post_kwargs["status"] == GroupPostStatus.PUBLISHED

        _, event_kwargs = mock_get_events.call_args
        assert event_kwargs["restrict_group_ids"] == [followed_id]
        assert event_kwargs["newest_first"] is True

    @patch("pecha_api.author_group_feed.service.get_public_group_ids")
    @patch("pecha_api.author_group_feed.service.get_joined_event_ids_by_user")
    @patch("pecha_api.author_group_feed.service.get_event_participant_counts")
    @patch("pecha_api.author_group_feed.service.build_post_dtos")
    @patch("pecha_api.author_group_feed.service.get_events")
    @patch("pecha_api.author_group_feed.service.get_posts_for_group_ids")
    @patch("pecha_api.author_group_feed.service.get_groups_by_ids")
    @patch("pecha_api.author_group_feed.service.get_following_group_ids_by_user")
    @patch("pecha_api.author_group_feed.service.SessionLocal")
    @patch("pecha_api.author_group_feed.service.validate_and_extract_user_details")
    def test_include_unfollowed_mixes_other_public_groups(
        self,
        mock_validate,
        mock_session,
        mock_following_ids,
        mock_groups_by_ids,
        mock_get_posts,
        mock_get_events,
        mock_build_posts,
        mock_counts,
        mock_joined,
        mock_public_ids,
    ):
        user = MockUser()
        followed_id = uuid4()
        other_id = uuid4()
        mock_validate.return_value = user
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_following_ids.return_value = [followed_id]
        mock_groups_by_ids.side_effect = [
            [MockGroup(followed_id)],
            [MockGroup(followed_id), MockGroup(other_id, title="Other Group")],
        ]
        mock_public_ids.return_value = [followed_id, other_id]

        unfollowed_post = MockPost(other_id)
        mock_get_posts.return_value = ([unfollowed_post], 1)
        mock_build_posts.return_value = [_post_dto(unfollowed_post)]
        mock_get_events.return_value = ([], 0)
        mock_counts.return_value = {}
        mock_joined.return_value = []

        result = get_author_group_feed_service(
            token="token",
            request=AuthorGroupFeedRequest(include_unfollowed=True),
        )

        assert result.include_unfollowed is True
        assert result.total == 1
        assert result.items[0].is_followed is False
        assert result.items[0].type == AuthorGroupFeedItemType.POST

        _, post_kwargs = mock_get_posts.call_args
        assert set(post_kwargs["group_ids"]) == {followed_id, other_id}

    @patch("pecha_api.author_group_feed.service.get_posts_for_group_ids")
    @patch("pecha_api.author_group_feed.service.get_groups_by_ids")
    @patch("pecha_api.author_group_feed.service.get_following_group_ids_by_user")
    @patch("pecha_api.author_group_feed.service.SessionLocal")
    @patch("pecha_api.author_group_feed.service.validate_and_extract_user_details")
    def test_empty_when_user_follows_nothing(
        self,
        mock_validate,
        mock_session,
        mock_following_ids,
        mock_groups_by_ids,
        mock_get_posts,
    ):
        mock_validate.return_value = MockUser()
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_following_ids.return_value = []
        mock_groups_by_ids.return_value = []

        result = get_author_group_feed_service(token="token")

        assert result.items == []
        assert result.total == 0
        mock_get_posts.assert_not_called()
