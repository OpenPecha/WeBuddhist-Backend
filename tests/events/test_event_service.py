from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from pecha_api.events.event_response_models import EventDTO, EventsResponse
from pecha_api.events.event_service import get_events_today_service


def test_get_events_today_service_uses_day_bounds():
    start = datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 23, 23, 59, 59, 999999, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    event = EventDTO(
        id=uuid4(),
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        is_one_day=True,
        featured=False,
        metadata=[],
        created_at=now,
        created_by="author@example.com",
    )
    expected = EventsResponse(events=[event], total=1, skip=0, limit=20)

    with patch(
        "pecha_api.events.event_service.get_day_bounds_in_timezone",
        return_value=(start, end),
    ) as mock_bounds, patch(
        "pecha_api.events.event_service.get_events_service",
        return_value=expected,
    ) as mock_get_events:
        result = get_events_today_service(timezone="Asia/Kathmandu", language="en")

    mock_bounds.assert_called_once_with("Asia/Kathmandu")
    mock_get_events.assert_called_once_with(
        group_id=None,
        from_date=start,
        to_date=end,
        language="en",
        fallback=True,
        skip=0,
        limit=20,
        token=None,
    )
    assert result == expected
