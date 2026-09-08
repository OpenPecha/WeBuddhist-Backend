"""get_event_reminder is called twice per request from the same session (see
reminder_notification_service._reminder_superseded's fail-fast + authoritative
recheck), with no commit on that session in between - so expire_on_commit
never fires to force a refresh. A plain SQLAlchemy query does not otherwise
overwrite an already identity-mapped object's attributes, so without
populate_existing(), the second call would silently hand back the first
call's cached in-memory object instead of observing a change committed by a
genuinely concurrent transaction (e.g. an event update's cancel/reschedule).
Only a real Session against a real engine can exercise the identity map, so
this uses an in-memory SQLite database (shared across two sessions via
StaticPool, to model two independent transactions) rather than mocks."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pecha_api.events.event_reminder_model import EventReminder
from pecha_api.events.event_reminder_repository import get_event_reminder


def _make_sessionmaker():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    EventReminder.metadata.create_all(bind=engine, tables=[EventReminder.__table__])
    return sessionmaker(bind=engine)


def test_recheck_observes_a_cancellation_committed_by_a_concurrent_transaction():
    Session = _make_sessionmaker()
    setup_db = Session()
    event_id = uuid4()
    fire_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    setup_db.add(
        EventReminder(
            id=uuid4(),
            event_id=event_id,
            reminder_type="T_ZERO",
            fire_at=fire_at,
            created_at=datetime.now(timezone.utc),
        )
    )
    setup_db.commit()
    setup_db.close()

    # This session plays the role of get_event_reminder_targets's own
    # session: it never commits between its two reads.
    reader_db = Session()
    first = get_event_reminder(reader_db, event_id, "T_ZERO")
    assert first.canceled_at is None

    # A fully separate session/transaction - e.g. update_event_service
    # canceling this reminder while reader_db's request is still resolving
    # participants/devices.
    writer_db = Session()
    canceled_at = datetime.now(timezone.utc)
    writer_db.query(EventReminder).filter(EventReminder.event_id == event_id).update(
        {EventReminder.canceled_at: canceled_at}, synchronize_session=False,
    )
    writer_db.commit()
    writer_db.close()

    second = get_event_reminder(reader_db, event_id, "T_ZERO")

    assert second is first  # identity map returns the same Python object...
    assert second.canceled_at is not None  # ...but populate_existing() refreshed it in place
