from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.repository import (
    create_post,
    get_group_posts,
    get_post_by_id,
    replace_post_links,
    replace_post_media,
    soft_delete_post,
    update_post,
)


def _query_chain(db, total=0, results=None):
    """Wire a MagicMock session so every query builder call returns the same
    mock, letting assertions target the individual builder steps."""
    query = MagicMock()
    db.query.return_value = query
    for method in ("filter", "order_by", "options", "offset", "limit"):
        getattr(query, method).return_value = query
    query.count.return_value = total
    query.all.return_value = results if results is not None else []
    return query


class TestGetGroupPosts:

    def test_returns_posts_and_total(self):
        db = MagicMock()
        posts = [MagicMock(), MagicMock()]
        query = _query_chain(db, total=2, results=posts)

        result, total = get_group_posts(db=db, group_id=uuid4(), skip=5, limit=10)

        assert result == posts
        assert total == 2
        query.offset.assert_called_once_with(5)
        query.limit.assert_called_once_with(10)

    def test_without_status_filter_only_filters_group_and_deleted_at(self):
        db = MagicMock()
        query = _query_chain(db)

        get_group_posts(db=db, group_id=uuid4())

        assert query.filter.call_count == 1

    def test_with_status_filter_adds_a_status_filter(self):
        db = MagicMock()
        query = _query_chain(db)

        get_group_posts(db=db, group_id=uuid4(), status=GroupPostStatus.PUBLISHED)

        assert query.filter.call_count == 2


class TestGetPostById:

    def test_returns_matching_post(self):
        db = MagicMock()
        post = MagicMock()
        query = _query_chain(db)
        query.first.return_value = post

        assert get_post_by_id(db=db, post_id=uuid4(), group_id=uuid4()) is post
        assert query.filter.call_count == 1

    def test_with_status_filter_adds_a_status_filter(self):
        db = MagicMock()
        query = _query_chain(db)
        query.first.return_value = None

        result = get_post_by_id(
            db=db,
            post_id=uuid4(),
            group_id=uuid4(),
            status=GroupPostStatus.HIDDEN,
        )

        assert result is None
        assert query.filter.call_count == 2


class TestWritePosts:

    def test_create_post_commits_and_refreshes(self):
        db = MagicMock()
        post = MagicMock()

        assert create_post(db=db, post=post) is post
        db.add.assert_called_once_with(post)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(post)

    def test_update_post_commits_and_refreshes(self):
        db = MagicMock()
        post = MagicMock()

        assert update_post(db=db, post=post) is post
        db.add.assert_not_called()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(post)

    def test_replace_post_media_deletes_before_inserting(self):
        db = MagicMock()
        query = _query_chain(db)
        post = MagicMock()
        media = [MagicMock(), MagicMock()]

        # The delete must be emitted first or the (post_id, display_order)
        # unique constraint can collide with the rows being inserted.
        order = []
        query.delete.side_effect = lambda: order.append("delete")
        db.add_all.side_effect = lambda _: order.append("add_all")

        assert replace_post_media(db=db, post=post, media=media) is post
        assert order == ["delete", "add_all"]
        db.add_all.assert_called_once_with(media)
        db.commit.assert_called_once()

    def test_replace_post_links_deletes_before_inserting(self):
        db = MagicMock()
        query = _query_chain(db)
        post = MagicMock()
        links = [MagicMock()]

        assert replace_post_links(db=db, post=post, links=links) is post
        query.delete.assert_called_once()
        db.add_all.assert_called_once_with(links)
        db.commit.assert_called_once()

    def test_soft_delete_post_stamps_deleted_fields(self):
        db = MagicMock()
        post = MagicMock()

        assert soft_delete_post(db=db, post=post, deleted_by="admin@example.com") is None
        assert post.deleted_at is not None
        assert post.deleted_by == "admin@example.com"
        db.commit.assert_called_once()
