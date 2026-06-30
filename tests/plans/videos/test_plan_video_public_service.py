from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.plans.videos.plan_video_service import get_public_plan_videos_by_segment_id


def _video(*, video_id, url, title, plan_id=None, display_order=0):
    v = MagicMock()
    v.id = uuid4()
    v.plan_id = plan_id or uuid4()
    v.url = url
    v.video_id = video_id
    v.title = title
    v.display_order = display_order
    v.created_at = None
    return v


def _patch_session(mock_session):
    mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.return_value.__exit__ = MagicMock(return_value=False)


@patch("pecha_api.plans.videos.plan_video_service.get_plan_videos_by_segment_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_returns_videos_from_all_plans(mock_session, mock_get_videos):
    _patch_session(mock_session)
    plan_a, plan_b = uuid4(), uuid4()
    mock_get_videos.return_value = [
        _video(video_id="a1", url="https://youtu.be/a1", title="A1", plan_id=plan_a),
        _video(video_id="b1", url="https://youtu.be/b1", title="B1", plan_id=plan_b),
    ]

    result = get_public_plan_videos_by_segment_id(segment_id=uuid4())

    # both plans' videos appear in one flat list
    assert [v.title for v in result.videos] == ["A1", "B1"]
    mock_get_videos.assert_called_once()


@patch("pecha_api.plans.videos.plan_video_service.get_plan_videos_by_segment_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_dedupes_video_shared_across_plans(mock_session, mock_get_videos):
    _patch_session(mock_session)
    plan_a, plan_b = uuid4(), uuid4()
    # same video_id appears in two different plans -> shown once
    mock_get_videos.return_value = [
        _video(video_id="dup", url="https://youtu.be/dup", title="Dup", plan_id=plan_a),
        _video(video_id="dup", url="https://youtu.be/dup", title="Dup", plan_id=plan_b),
        _video(video_id="x", url="https://youtu.be/x", title="X", plan_id=plan_b),
    ]

    result = get_public_plan_videos_by_segment_id(segment_id=uuid4())

    assert [v.title for v in result.videos] == ["Dup", "X"]


@patch("pecha_api.plans.videos.plan_video_service.get_plan_videos_by_segment_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_dedupes_by_url_when_video_id_missing(mock_session, mock_get_videos):
    _patch_session(mock_session)
    # no video_id -> fall back to url for de-dup
    mock_get_videos.return_value = [
        _video(video_id=None, url="https://example.com/v", title="V1"),
        _video(video_id=None, url="https://example.com/v", title="V2"),
    ]

    result = get_public_plan_videos_by_segment_id(segment_id=uuid4())

    assert len(result.videos) == 1


@patch("pecha_api.plans.videos.plan_video_service.get_plan_videos_by_segment_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_returns_empty_when_no_videos(mock_session, mock_get_videos):
    _patch_session(mock_session)
    mock_get_videos.return_value = []

    result = get_public_plan_videos_by_segment_id(segment_id=uuid4())

    assert result.videos == []
