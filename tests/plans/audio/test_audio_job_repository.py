from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.plans.audio.audio_job_models import AudioJob
from pecha_api.plans.audio.audio_job_repository import (
    mark_audio_job_completed,
    mark_audio_job_failed,
    mark_audio_job_processing,
)
from pecha_api.plans.plans_enums import AudioJobStatus


def _mock_db_execute(*, rowcount: int):
    db = MagicMock()
    result = MagicMock()
    result.rowcount = rowcount
    db.execute.return_value = result
    return db


def test_mark_audio_job_processing_updates_only_pending_rows():
    db = _mock_db_execute(rowcount=1)
    job_id = uuid4()
    now = datetime.now(timezone.utc)
    claimed = AudioJob(
        id=job_id,
        status=AudioJobStatus.PROCESSING.value,
        language="bo",
        audio_type="TEXT_READING",
        voice_name="dolkar_lhasa_female",
        payload={},
        attempt_count=1,
        created_at=now,
        updated_at=now,
        started_at=now,
    )
    db.query.return_value.filter.return_value.first.return_value = claimed

    result = mark_audio_job_processing(db=db, job_id=job_id)

    assert result is claimed
    db.execute.assert_called_once()
    stmt = db.execute.call_args.args[0]
    where_sql = str(stmt.whereclause.compile(compile_kwargs={"literal_binds": True}))
    assert f"status = '{AudioJobStatus.PENDING.value}'" in where_sql
    assert "attempt_count=(audio_jobs.attempt_count +" in str(stmt)
    db.commit.assert_called_once()


def test_mark_audio_job_processing_returns_none_when_no_row_claimed():
    db = _mock_db_execute(rowcount=0)
    result = mark_audio_job_processing(db=db, job_id=uuid4())
    assert result is None
    db.query.assert_not_called()


def test_mark_audio_job_completed_returns_none_when_not_processing():
    db = _mock_db_execute(rowcount=0)
    result = mark_audio_job_completed(db=db, job_id=uuid4(), result={"s3_key": "a.wav"})
    assert result is None


def test_mark_audio_job_failed_returns_none_when_status_mismatch():
    db = _mock_db_execute(rowcount=0)
    result = mark_audio_job_failed(
        db=db,
        job_id=uuid4(),
        error_message="boom",
        expected_statuses=(AudioJobStatus.PROCESSING.value,),
    )
    assert result is None
