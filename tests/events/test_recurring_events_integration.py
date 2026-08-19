from datetime import datetime, timezone
import pytest
from uuid import uuid4

from pecha_api.events.event_response_models import (
    CreateEventRequest,
    RecurrenceInput,
    EventMetadataInput,
)
from pecha_api.events.event_enums import RecurrenceFrequency, RecurrenceDateSystem


class TestRecurringEventsIntegration:
    """Integration tests for recurring events end-to-end flow."""
    
    def test_recurrence_input_validates_gregorian_yearly(self):
        recurrence = RecurrenceInput(
            frequency=RecurrenceFrequency.YEARLY,
            date_system=RecurrenceDateSystem.GREGORIAN,
            month=12,
            day=25,
            duration_days=1,
        )
        
        assert recurrence.frequency == RecurrenceFrequency.YEARLY
        assert recurrence.month == 12
        assert recurrence.day == 25

    def test_recurrence_input_validates_lunar_requires_calendar_type(self):
        with pytest.raises(ValueError, match="calendar_type is required"):
            RecurrenceInput(
                frequency=RecurrenceFrequency.YEARLY,
                date_system=RecurrenceDateSystem.TIBETAN_LUNAR,
                month=4,
                day=15,
                duration_days=1,
            )

    def test_recurrence_input_validates_yearly_requires_month(self):
        with pytest.raises(ValueError, match="month is required"):
            RecurrenceInput(
                frequency=RecurrenceFrequency.YEARLY,
                date_system=RecurrenceDateSystem.GREGORIAN,
                day=15,
                duration_days=1,
            )

    def test_recurrence_input_validates_lunar_day_range(self):
        with pytest.raises(ValueError, match="Lunar day must be between 1 and 30"):
            RecurrenceInput(
                frequency=RecurrenceFrequency.MONTHLY,
                date_system=RecurrenceDateSystem.TIBETAN_LUNAR,
                calendar_type="phugpa",
                day=31,
                duration_days=1,
            )

    def test_recurrence_input_validates_calendar_type_values(self):
        with pytest.raises(ValueError, match="must be 'phugpa' or 'tsurphu'"):
            RecurrenceInput(
                frequency=RecurrenceFrequency.MONTHLY,
                date_system=RecurrenceDateSystem.TIBETAN_LUNAR,
                calendar_type="invalid",
                day=15,
                duration_days=1,
            )

    def test_create_event_request_accepts_recurrence(self):
        request = CreateEventRequest(
            group_id=uuid4(),
            metadata=[
                EventMetadataInput(
                    name="Test Event",
                    description="Test Description",
                    language="EN",
                )
            ],
            recurrence=RecurrenceInput(
                frequency=RecurrenceFrequency.YEARLY,
                date_system=RecurrenceDateSystem.GREGORIAN,
                month=12,
                day=25,
                duration_days=1,
            ),
        )
        
        assert request.recurrence is not None
        assert request.recurrence.frequency == RecurrenceFrequency.YEARLY

    def test_create_event_request_requires_dates_without_recurrence(self):
        with pytest.raises(ValueError, match="start_date and end_date are required"):
            CreateEventRequest(
                group_id=uuid4(),
                metadata=[
                    EventMetadataInput(
                        name="Test Event",
                        description="Test Description",
                        language="EN",
                    )
                ],
            )

    def test_create_event_request_allows_dates_with_recurrence(self):
        request = CreateEventRequest(
            group_id=uuid4(),
            start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            metadata=[
                EventMetadataInput(
                    name="Test Event",
                    description="Test Description",
                    language="EN",
                )
            ],
            recurrence=RecurrenceInput(
                frequency=RecurrenceFrequency.YEARLY,
                date_system=RecurrenceDateSystem.GREGORIAN,
                month=12,
                day=25,
                duration_days=1,
            ),
        )
        
        assert request.recurrence is not None
