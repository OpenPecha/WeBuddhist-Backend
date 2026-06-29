from unittest.mock import MagicMock, patch
from uuid import uuid4

from pecha_api.plans.videos.plan_video_service import get_public_plan_videos_by_segment_id


@patch("pecha_api.plans.videos.plan_video_service.get_plan_videos_by_plan_id")
@patch("pecha_api.plans.videos.plan_video_service.get_plan_id_by_segment_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_get_public_plan_videos_by_segment_id_returns_videos(
    mock_session, mock_get_plan_id, mock_get_videos
):
    mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    segment_id = uuid4()
    plan_id = uuid4()
    mock_get_plan_id.return_value = plan_id

    video = MagicMock()
    video.id = uuid4()
    video.plan_id = plan_id
    video.url = "https://youtu.be/abc"
    video.video_id = "abc"
    video.title = "Intro"
    video.display_order = 0
    video.created_at = None
    mock_get_videos.return_value = [video]

    result = get_public_plan_videos_by_segment_id(segment_id=segment_id)

    assert len(result.videos) == 1
    assert result.videos[0].title == "Intro"
    assert result.videos[0].plan_id == plan_id
    mock_get_plan_id.assert_called_once()
    mock_get_videos.assert_called_once()


@patch("pecha_api.plans.videos.plan_video_service.get_plan_videos_by_plan_id")
@patch("pecha_api.plans.videos.plan_video_service.get_plan_id_by_segment_id")
@patch("pecha_api.plans.videos.plan_video_service.SessionLocal")
def test_get_public_plan_videos_by_segment_id_no_plan_returns_empty(
    mock_session, mock_get_plan_id, mock_get_videos
):
    mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    # segment does not belong to any plan
    mock_get_plan_id.return_value = None

    result = get_public_plan_videos_by_segment_id(segment_id=uuid4())

    assert result.videos == []
    # videos should not be fetched when no plan is found
    mock_get_videos.assert_not_called()
