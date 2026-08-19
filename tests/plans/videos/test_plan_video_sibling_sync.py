"""Tests for the language-sibling sync behaviour of plan videos.

When a video is added / removed / reordered on one plan, the same change must
be mirrored onto every language sibling of that plan (same series, same
display_order, different language) so all language versions of a plan always
show the same videos in the same order.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from pecha_api.plans.videos.plan_video_service import (
    add_plan_video,
    remove_plan_video,
    reorder_plan_videos_entries,
)
from pecha_api.plans.videos.plan_video_response_models import (
    CreatePlanVideoRequest,
    PlanVideoOrderItem,
    ReorderPlanVideosRequest,
)


def _patch_session(mock_session):
    db = MagicMock()
    mock_session.return_value.__enter__ = MagicMock(return_value=db)
    mock_session.return_value.__exit__ = MagicMock(return_value=False)
    return db


def _video(*, row_id=None, video_id, url, title="T", plan_id=None, display_order=0):
    v = MagicMock()
    v.id = row_id or uuid4()
    v.plan_id = plan_id or uuid4()
    v.url = url
    v.video_id = video_id
    v.title = title
    v.display_order = display_order
    v.created_at = None
    return v


# --------------------------------------------------------------------------- add


@patch("pecha_api.plans.videos.plan_video_service.add_plan_video_no_commit")
@patch("pecha_api.plans.videos.plan_video_service.get_next_display_order")
@patch("pecha_api.plans.videos.plan_video_service.get_sibling_language_plan_ids")
@patch("pecha_api.plans.videos.plan_video_service._get_author_plan")
@patch("pecha_api.plans.videos.plan_video_service.validate_cms_author_details")
@patch("pecha_api.plans.videos.plan_video_service.extract_youtube_video_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_add_video_mirrors_to_all_language_siblings(
    mock_session,
    mock_extract,
    mock_validate,
    mock_get_author_plan,
    mock_siblings,
    mock_next_order,
    mock_create,
):
    _patch_session(mock_session)
    mock_validate.return_value = MagicMock(email="author@example.com")
    mock_extract.return_value = "yt123"

    en_plan = uuid4()
    bo_plan = uuid4()
    zh_plan = uuid4()
    mock_siblings.return_value = [en_plan, bo_plan, zh_plan]
    mock_next_order.return_value = 0
    # create returns whatever PlanVideo it was handed
    def _persist(db, plan_video):
        # the real repository assigns an id via db.refresh()
        plan_video.id = uuid4()
        return plan_video

    mock_create.side_effect = _persist

    result = add_plan_video(
        token="t",
        plan_id=en_plan,
        request=CreatePlanVideoRequest(url="https://youtu.be/yt123", title="Intro"),
    )

    # one insert per language sibling
    assert mock_create.call_count == 3
    inserted_plan_ids = {
        call.kwargs["plan_video"].plan_id for call in mock_create.call_args_list
    }
    assert inserted_plan_ids == {en_plan, bo_plan, zh_plan}
    # every inserted row carries the same video identity
    assert all(
        call.kwargs["plan_video"].video_id == "yt123"
        for call in mock_create.call_args_list
    )
    # the DTO returned is the row for the plan the author actually acted on
    assert result.plan_id == en_plan


@patch("pecha_api.plans.videos.plan_video_service.add_plan_video_no_commit")
@patch("pecha_api.plans.videos.plan_video_service.get_next_display_order")
@patch("pecha_api.plans.videos.plan_video_service.get_sibling_language_plan_ids")
@patch("pecha_api.plans.videos.plan_video_service._get_author_plan")
@patch("pecha_api.plans.videos.plan_video_service.validate_cms_author_details")
@patch("pecha_api.plans.videos.plan_video_service.extract_youtube_video_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_add_video_standalone_plan_inserts_once(
    mock_session,
    mock_extract,
    mock_validate,
    mock_get_author_plan,
    mock_siblings,
    mock_next_order,
    mock_create,
):
    _patch_session(mock_session)
    mock_validate.return_value = MagicMock(email="author@example.com")
    mock_extract.return_value = "yt123"

    plan = uuid4()
    # standalone plan: helper returns only itself
    mock_siblings.return_value = [plan]
    mock_next_order.return_value = 0
    def _persist(db, plan_video):
        # the real repository assigns an id via db.refresh()
        plan_video.id = uuid4()
        return plan_video

    mock_create.side_effect = _persist

    add_plan_video(
        token="t",
        plan_id=plan,
        request=CreatePlanVideoRequest(url="https://youtu.be/yt123", title="Intro"),
    )

    assert mock_create.call_count == 1


@patch("pecha_api.plans.videos.plan_video_service.add_plan_video_no_commit")
@patch("pecha_api.plans.videos.plan_video_service.get_next_display_order")
@patch("pecha_api.plans.videos.plan_video_service.get_sibling_language_plan_ids")
@patch("pecha_api.plans.videos.plan_video_service._get_author_plan")
@patch("pecha_api.plans.videos.plan_video_service.validate_cms_author_details")
@patch("pecha_api.plans.videos.plan_video_service.extract_youtube_video_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_add_video_commits_once_for_whole_fanout(
    mock_session,
    mock_extract,
    mock_validate,
    mock_get_author_plan,
    mock_siblings,
    mock_next_order,
    mock_create,
):
    # The fan-out must be atomic: rows are staged without committing, then a
    # single commit finalizes all language siblings together.
    db = _patch_session(mock_session)
    mock_validate.return_value = MagicMock(email="author@example.com")
    mock_extract.return_value = "yt123"

    en_plan, bo_plan, zh_plan = uuid4(), uuid4(), uuid4()
    mock_siblings.return_value = [en_plan, bo_plan, zh_plan]
    mock_next_order.return_value = 0

    def _persist(db, plan_video):
        plan_video.id = uuid4()
        return plan_video

    mock_create.side_effect = _persist

    add_plan_video(
        token="t",
        plan_id=en_plan,
        request=CreatePlanVideoRequest(url="https://youtu.be/yt123", title="Intro"),
    )

    # three inserts but exactly one commit for the whole fan-out
    assert mock_create.call_count == 3
    db.commit.assert_called_once()


@patch("pecha_api.plans.videos.plan_video_service.extract_youtube_video_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_add_video_rejects_invalid_youtube_url(mock_session, mock_extract):
    _patch_session(mock_session)
    mock_extract.return_value = None  # not a youtube url

    with pytest.raises(Exception):
        add_plan_video(
            token="t",
            plan_id=uuid4(),
            request=CreatePlanVideoRequest(url="https://example.com/x", title="x"),
        )


# ------------------------------------------------------------------------ remove


@patch("pecha_api.plans.videos.plan_video_service.delete_plan_video_across_plans")
@patch("pecha_api.plans.videos.plan_video_service.get_sibling_language_plan_ids")
@patch("pecha_api.plans.videos.plan_video_service.get_plan_video_by_id")
@patch("pecha_api.plans.videos.plan_video_service._get_author_plan")
@patch("pecha_api.plans.videos.plan_video_service.validate_cms_author_details")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_remove_video_deletes_across_all_siblings_by_identity(
    mock_session,
    mock_validate,
    mock_get_author_plan,
    mock_get_video,
    mock_siblings,
    mock_delete,
):
    _patch_session(mock_session)
    mock_validate.return_value = MagicMock(email="author@example.com")

    en_plan, bo_plan, zh_plan = uuid4(), uuid4(), uuid4()
    row_id = uuid4()
    mock_get_video.return_value = _video(
        row_id=row_id, video_id="yt123", url="https://youtu.be/yt123", plan_id=en_plan
    )
    mock_siblings.return_value = [en_plan, bo_plan, zh_plan]

    remove_plan_video(token="t", plan_id=en_plan, video_id=row_id)

    mock_delete.assert_called_once()
    kwargs = mock_delete.call_args.kwargs
    assert set(kwargs["plan_ids"]) == {en_plan, bo_plan, zh_plan}
    # matched by video identity, not the row id
    assert kwargs["video_identity_id"] == "yt123"
    assert kwargs["url"] == "https://youtu.be/yt123"


@patch("pecha_api.plans.videos.plan_video_service.delete_plan_video_across_plans")
@patch("pecha_api.plans.videos.plan_video_service.get_sibling_language_plan_ids")
@patch("pecha_api.plans.videos.plan_video_service.get_plan_video_by_id")
@patch("pecha_api.plans.videos.plan_video_service._get_author_plan")
@patch("pecha_api.plans.videos.plan_video_service.validate_cms_author_details")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_remove_video_404_does_not_touch_siblings(
    mock_session,
    mock_validate,
    mock_get_author_plan,
    mock_get_video,
    mock_siblings,
    mock_delete,
):
    _patch_session(mock_session)
    mock_validate.return_value = MagicMock(email="author@example.com")
    mock_get_video.return_value = None  # not found on the plan

    with pytest.raises(Exception):
        remove_plan_video(token="t", plan_id=uuid4(), video_id=uuid4())

    mock_delete.assert_not_called()


# ----------------------------------------------------------------------- reorder


@patch("pecha_api.plans.videos.plan_video_service.get_plan_videos_by_plan_id")
@patch("pecha_api.plans.videos.plan_video_service.reorder_plan_videos_across_plans")
@patch("pecha_api.plans.videos.plan_video_service.get_sibling_language_plan_ids")
@patch("pecha_api.plans.videos.plan_video_service._get_author_plan")
@patch("pecha_api.plans.videos.plan_video_service.validate_cms_author_details")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_reorder_maps_row_ids_to_identities_and_fans_out(
    mock_session,
    mock_validate,
    mock_get_author_plan,
    mock_siblings,
    mock_reorder,
    mock_get_videos,
):
    _patch_session(mock_session)
    mock_validate.return_value = MagicMock(email="author@example.com")

    en_plan, bo_plan = uuid4(), uuid4()
    v1 = _video(video_id="yt1", url="https://youtu.be/yt1", plan_id=en_plan, display_order=0)
    v2 = _video(video_id="yt2", url="https://youtu.be/yt2", plan_id=en_plan, display_order=1)
    # get_plan_videos_by_plan_id is called twice: once to map ids, once for the response
    mock_get_videos.side_effect = [[v1, v2], [v2, v1]]
    mock_siblings.return_value = [en_plan, bo_plan]

    # request swaps the two videos' order, addressing them by EN row id
    request = ReorderPlanVideosRequest(
        videos=[
            PlanVideoOrderItem(id=v1.id, display_order=1),
            PlanVideoOrderItem(id=v2.id, display_order=0),
        ]
    )

    reorder_plan_videos_entries(token="t", plan_id=en_plan, request=request)

    mock_reorder.assert_called_once()
    kwargs = mock_reorder.call_args.kwargs
    assert set(kwargs["plan_ids"]) == {en_plan, bo_plan}
    # row ids were translated into video identities before fan-out
    assert kwargs["order_by_identity"] == {"yt1": 1, "yt2": 0}
