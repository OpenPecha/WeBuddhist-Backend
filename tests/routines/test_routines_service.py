import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi import HTTPException

from pecha_api.routines.routines_service import (
    create_routine_with_time_block,
    add_time_block_to_routine,
    delete_time_block,
    update_time_block_service,
    get_user_routine,
    _validate_time_block_request,
    _resolve_plan_sessions,
    _resolve_recitation_sessions,
    _resolve_sessions,
    group_sessions_by_block,
    build_time_block_dto,
)
from pecha_api.routines.routines_response_models import (
    CreateTimeBlockRequest,
    UpdateTimeBlockRequest,
    SessionRequest,
    RoutineResponse,
)
from pecha_api.routines.routines_enums import SessionType
from pecha_api.routines.response_message import (
    ROUTINE_ALREADY_EXISTS,
    ROUTINE_NOT_FOUND,
    ROUTINE_FORBIDDEN,
    TIME_BLOCK_NOT_FOUND,
    TIME_BLOCK_TIME_CONFLICT,
    INVALID_TIME_FORMAT,
    SESSIONS_REQUIRED,
    DUPLICATE_PLAN,
    TIME_ALREADY_EXISTS,
)

def _mock_session_with_db():
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    return db_mock, session_cm


# --- Validation tests ---


def test_validate_empty_sessions():
    request = CreateTimeBlockRequest(
        time="12:00",
        time_int=1200,
        sessions=[],
    )
    with pytest.raises(HTTPException) as exc_info:
        _validate_time_block_request(request)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["message"] == SESSIONS_REQUIRED


def test_validate_invalid_time_format():
    request = CreateTimeBlockRequest(
        time="25:00",
        time_int=2500,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )
    with pytest.raises(HTTPException) as exc_info:
        _validate_time_block_request(request)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["message"] == INVALID_TIME_FORMAT


def test_validate_valid_time_formats():
    valid_times = ["00:00", "06:00", "12:30", "23:59"]
    for time in valid_times:
        request = CreateTimeBlockRequest(
            time=time,
            time_int=int(time.replace(":", "")),
            sessions=[
                SessionRequest(
                    session_type=SessionType.PLAN,
                    source_id=uuid.uuid4(),
                    display_order=0,
                )
            ],
        )
        _validate_time_block_request(request)


def test_validate_duplicate_plan_source_ids():
    duplicate_id = uuid.uuid4()
    request = CreateTimeBlockRequest(
        time="12:00",
        time_int=1200,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=duplicate_id,
                display_order=0,
            ),
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=duplicate_id,
                display_order=1,
            ),
        ],
    )
    with pytest.raises(HTTPException) as exc_info:
        _validate_time_block_request(request)
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["message"] == DUPLICATE_PLAN


def test_validate_duplicate_recitations_allowed():
    duplicate_id = uuid.uuid4()
    request = CreateTimeBlockRequest(
        time="12:00",
        time_int=1200,
        sessions=[
            SessionRequest(
                session_type=SessionType.RECITATION,
                source_id=duplicate_id,
                display_order=0,
            ),
            SessionRequest(
                session_type=SessionType.RECITATION,
                source_id=duplicate_id,
                display_order=1,
            ),
        ],
    )
    _validate_time_block_request(request)


# --- Create routine tests ---


@pytest.mark.asyncio
async def test_create_routine_success():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    request = CreateTimeBlockRequest(
        time="12:00",
        time_int=1200,
        notification_enabled=True,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=source_id,
                display_order=0,
            )
        ],
    )

    _db_mock, session_cm = _mock_session_with_db()

    saved_routine = SimpleNamespace(id=routine_id, user_id=user_id)
    saved_time_block = SimpleNamespace(
        id=time_block_id,
        time="12:00",
        time_int=1200,
        notification_enabled=True,
    )
    saved_session = SimpleNamespace(
        id=session_id,
        session_type=SessionType.PLAN,
        source_id=source_id,
        display_order=0,
    )

    mock_plan = SimpleNamespace(
        id=source_id,
        title="Daily Routine",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/image.jpg",
    )

    mock_time_block_model = MagicMock()
    mock_session_model = MagicMock()

    with patch(
        "pecha_api.routines.routines_service.generate_presigned_access_url",
        side_effect=lambda bucket_name, s3_key: s3_key,
    ), patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_user_id",
        return_value=None,
    ), patch(
        "pecha_api.routines.routines_service.Routine",
        return_value=saved_routine,
    ), patch(
        "pecha_api.routines.routines_service.RoutineTimeBlock",
        return_value=mock_time_block_model,
    ), patch(
        "pecha_api.routines.routines_service.RoutineSession",
        return_value=mock_session_model,
    ), patch(
        "pecha_api.routines.routines_service.save_routine",
        return_value=saved_routine,
    ), patch(
        "pecha_api.routines.routines_service.RoutineTimeBlock",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.routines.routines_service.save_time_block",
        return_value=saved_time_block,
    ), patch(
        "pecha_api.routines.routines_service.RoutineSession",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.routines.routines_service.save_sessions",
        return_value=[saved_session],
    ), patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ):
        result = await create_routine_with_time_block(token="token123", request=request)

        assert result.id == routine_id
        assert len(result.time_blocks) == 1
        assert result.time_blocks[0].id == time_block_id
        assert result.time_blocks[0].time == "12:00"
        assert result.time_blocks[0].time_int == 1200
        assert len(result.time_blocks[0].sessions) == 1
        assert result.time_blocks[0].sessions[0].title == "Daily Routine"
        assert result.time_blocks[0].sessions[0].language == "EN"
        assert (
            result.time_blocks[0].sessions[0].image_url
            == "https://example.com/image.jpg"
        )


@pytest.mark.asyncio
async def test_create_routine_already_exists():
    user_id = uuid.uuid4()

    request = CreateTimeBlockRequest(
        time="12:00",
        time_int=1200,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_user_id",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await create_routine_with_time_block(token="token123", request=request)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["message"] == ROUTINE_ALREADY_EXISTS


# --- Resolve sessions tests ---


def test_resolve_plan_sessions_success():
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    session = SimpleNamespace(
        id=session_id,
        session_type=SessionType.PLAN,
        source_id=source_id,
        display_order=0,
    )

    mock_plan = SimpleNamespace(
        id=source_id,
        title="Test Plan",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/plan.jpg",
    )

    with patch(
        "pecha_api.routines.routines_service.generate_presigned_access_url",
        side_effect=lambda bucket_name, s3_key: s3_key,
    ), patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ):
        result = _resolve_plan_sessions(db=MagicMock(), plan_sessions=[session])

        assert len(result) == 1
        assert result[0].title == "Test Plan"
        assert result[0].language == "EN"
        assert result[0].image_url == "https://example.com/plan.jpg"


def test_resolve_plan_sessions_missing_plan():
    session = SimpleNamespace(
        id=uuid.uuid4(),
        session_type=SessionType.PLAN,
        source_id=uuid.uuid4(),
        display_order=0,
    )

    with patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[],
    ):
        result = _resolve_plan_sessions(db=MagicMock(), plan_sessions=[session])

        assert len(result) == 0


def test_resolve_plan_sessions_empty_list():
    result = _resolve_plan_sessions(db=MagicMock(), plan_sessions=[])
    assert result == []


@pytest.mark.asyncio
async def test_resolve_recitation_sessions_success():
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    session = SimpleNamespace(
        id=session_id,
        session_type=SessionType.RECITATION,
        source_id=source_id,
        display_order=0,
    )

    mock_text = SimpleNamespace(
        id=source_id,
        title="Heart Sutra",
        language="bo",
    )

    with patch(
        "pecha_api.routines.routines_service.Text.get_texts_by_ids",
        new_callable=AsyncMock,
        return_value=[mock_text],
    ):
        result = await _resolve_recitation_sessions(recitation_sessions=[session])

        assert len(result) == 1
        assert result[0].title == "Heart Sutra"
        assert result[0].language == "bo"
        assert result[0].image_url is None


@pytest.mark.asyncio
async def test_resolve_recitation_sessions_null_language():
    session = SimpleNamespace(
        id=uuid.uuid4(),
        session_type=SessionType.RECITATION,
        source_id=uuid.uuid4(),
        display_order=0,
    )

    mock_text = SimpleNamespace(
        id=session.source_id,
        title="Test Text",
        language=None,
    )

    with patch(
        "pecha_api.routines.routines_service.Text.get_texts_by_ids",
        new_callable=AsyncMock,
        return_value=[mock_text],
    ):
        result = await _resolve_recitation_sessions(recitation_sessions=[session])

        assert len(result) == 1
        assert result[0].language == "en"


@pytest.mark.asyncio
async def test_resolve_recitation_sessions_missing_text():
    session = SimpleNamespace(
        id=uuid.uuid4(),
        session_type=SessionType.RECITATION,
        source_id=uuid.uuid4(),
        display_order=0,
    )

    with patch(
        "pecha_api.routines.routines_service.Text.get_texts_by_ids",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result = await _resolve_recitation_sessions(recitation_sessions=[session])

        assert len(result) == 0


@pytest.mark.asyncio
async def test_add_time_block_success():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    request = CreateTimeBlockRequest(
        time="08:00",
        time_int=800,
        notification_enabled=True,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=source_id,
                display_order=0,
            )
        ],
    )

    _db_mock, session_cm = _mock_session_with_db()

    saved_time_block = SimpleNamespace(
        id=time_block_id,
        time="08:00",
        time_int=800,
        notification_enabled=True,
    )
    saved_session = SimpleNamespace(
        id=session_id,
        session_type=SessionType.PLAN,
        source_id=source_id,
        display_order=0,
    )

    mock_plan = SimpleNamespace(
        id=source_id,
        title="Morning Plan",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/morning.jpg",
    )

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=SimpleNamespace(id=routine_id, user_id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.get_existing_plan_source_ids",
        return_value=[],
    ), patch(
        "pecha_api.routines.routines_service.time_block_exists_for_routine",
        return_value=False,
    ), patch(
        "pecha_api.routines.routines_service.RoutineTimeBlock",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.routines.routines_service.save_time_block",
        return_value=saved_time_block,
    ), patch(
        "pecha_api.routines.routines_service.RoutineSession",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.routines.routines_service.save_sessions",
        return_value=[saved_session],
    ), patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ):
        result = await add_time_block_to_routine(
            token="token123", routine_id=routine_id, request=request
        )

        assert result.id == time_block_id
        assert result.time == "08:00"
        assert result.time_int == 800
        assert len(result.sessions) == 1
        assert result.sessions[0].title == "Morning Plan"


@pytest.mark.asyncio
async def test_add_time_block_routine_not_found():
    request = CreateTimeBlockRequest(
        time="08:00",
        time_int=800,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await add_time_block_to_routine(
                token="token123", routine_id=uuid.uuid4(), request=request
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == ROUTINE_NOT_FOUND


@pytest.mark.asyncio
async def test_add_time_block_forbidden():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()

    request = CreateTimeBlockRequest(
        time="08:00",
        time_int=800,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await add_time_block_to_routine(
                token="token123", routine_id=routine_id, request=request
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == ROUTINE_NOT_FOUND


@pytest.mark.asyncio
async def test_add_time_block_duplicate_plan_across_routine():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    existing_plan_id = uuid.uuid4()

    request = CreateTimeBlockRequest(
        time="08:00",
        time_int=800,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=existing_plan_id,
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=SimpleNamespace(id=routine_id, user_id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.get_existing_plan_source_ids",
        return_value=[existing_plan_id],
    ):
        with pytest.raises(HTTPException) as exc_info:
            await add_time_block_to_routine(
                token="token123", routine_id=routine_id, request=request
            )
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["message"] == DUPLICATE_PLAN


@pytest.mark.asyncio
async def test_add_time_block_duplicate_time():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()

    request = CreateTimeBlockRequest(
        time="12:00",
        time_int=1200,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=SimpleNamespace(id=routine_id, user_id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.get_existing_plan_source_ids",
        return_value=[],
    ), patch(
        "pecha_api.routines.routines_service.time_block_exists_for_routine",
        return_value=True,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await add_time_block_to_routine(
                token="token123", routine_id=routine_id, request=request
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["message"] == TIME_ALREADY_EXISTS


def test_delete_time_block_success():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=SimpleNamespace(id=routine_id, user_id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.get_time_block_by_id_and_routine",
        return_value=SimpleNamespace(id=time_block_id, routine_id=routine_id),
    ), patch(
        "pecha_api.routines.routines_service.soft_delete_time_block",
    ) as mock_soft_delete:
        delete_time_block(
            token="token123", routine_id=routine_id, time_block_id=time_block_id
        )

        mock_soft_delete.assert_called_once()


def test_delete_time_block_routine_not_found():
    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
       "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_time_block(
                token="token123",
                routine_id=uuid.uuid4(),
                time_block_id=uuid.uuid4(),
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == ROUTINE_NOT_FOUND


def test_delete_time_block_forbidden():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_time_block(
                token="token123",
                routine_id=routine_id,
                time_block_id=uuid.uuid4(),
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == ROUTINE_NOT_FOUND


def test_delete_time_block_not_found():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=SimpleNamespace(id=routine_id, user_id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.get_time_block_by_id_and_routine",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            delete_time_block(
                token="token123",
                routine_id=routine_id,
                time_block_id=uuid.uuid4(),
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == TIME_BLOCK_NOT_FOUND


# --- Update Time Block Service Tests ---


@pytest.mark.asyncio
async def test_update_time_block_service_success():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    request = UpdateTimeBlockRequest(
        time="14:00",
        time_int=1400,
        notification_enabled=True,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=source_id,
                display_order=0,
            )
        ],
    )

    _db_mock, session_cm = _mock_session_with_db()

    mock_routine = SimpleNamespace(id=routine_id, user_id=user_id)
    mock_time_block = SimpleNamespace(
        id=time_block_id,
        routine_id=routine_id,
        time="12:00",
        time_int=1200,
        notification_enabled=True,
    )
    updated_time_block = SimpleNamespace(
        id=time_block_id,
        time="14:00",
        time_int=1400,
        notification_enabled=True,
    )
    saved_session = SimpleNamespace(
        id=session_id,
        session_type=SessionType.PLAN,
        source_id=source_id,
        display_order=0,
    )
    mock_plan = SimpleNamespace(
        id=source_id,
        title="Updated Plan",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/image.jpg",
    )

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=mock_routine,
    ), patch(
        "pecha_api.routines.routines_service.get_time_block_by_id_and_routine",
        return_value=mock_time_block,
    ), patch(
        "pecha_api.routines.routines_service.get_time_block_by_routine_and_time",
        return_value=None,
    ), patch(
        "pecha_api.routines.routines_service.delete_sessions_by_time_block_id",
    ), patch(
        "pecha_api.routines.routines_service.update_time_block_repo",
        return_value=updated_time_block,
    ), patch(
        "pecha_api.routines.routines_service.build_session_models",
        return_value=[MagicMock()],
    ), patch(
        "pecha_api.routines.routines_service.save_sessions",
        return_value=[saved_session],
    ), patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ):
        result = await update_time_block_service(
            token="token123",
            routine_id=routine_id,
            time_block_id=time_block_id,
            request=request,
        )

        assert result.id == time_block_id
        assert result.time == "14:00"
        assert result.time_int == 1400
        assert result.notification_enabled is True
        assert len(result.sessions) == 1
        assert result.sessions[0].title == "Updated Plan"


@pytest.mark.asyncio
async def test_update_time_block_service_routine_not_found():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    request = UpdateTimeBlockRequest(
        time="14:00",
        time_int=1400,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await update_time_block_service(
                token="token123",
                routine_id=routine_id,
                time_block_id=time_block_id,
                request=request,
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == ROUTINE_NOT_FOUND


@pytest.mark.asyncio
async def test_update_time_block_service_time_block_not_found():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    request = UpdateTimeBlockRequest(
        time="14:00",
        time_int=1400,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()
    mock_routine = SimpleNamespace(id=routine_id, user_id=user_id)

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=mock_routine,
    ), patch(
        "pecha_api.routines.routines_service.get_time_block_by_id_and_routine",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await update_time_block_service(
                token="token123",
                routine_id=routine_id,
                time_block_id=time_block_id,
                request=request,
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == TIME_BLOCK_NOT_FOUND


@pytest.mark.asyncio
async def test_update_time_block_service_time_conflict():
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    conflicting_time_block_id = uuid.uuid4()

    request = UpdateTimeBlockRequest(
        time="14:00",
        time_int=1400,
        sessions=[
            SessionRequest(
                session_type=SessionType.PLAN,
                source_id=uuid.uuid4(),
                display_order=0,
            )
        ],
    )

    _, session_cm = _mock_session_with_db()
    mock_routine = SimpleNamespace(id=routine_id, user_id=user_id)
    mock_time_block = SimpleNamespace(
        id=time_block_id,
        routine_id=routine_id,
        time="12:00",
        time_int=1200,
    )
    conflicting_time_block = SimpleNamespace(
        id=conflicting_time_block_id,
        routine_id=routine_id,
        time="14:00",
        time_int=1400,
    )

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_id_and_user",
        return_value=mock_routine,
    ), patch(
        "pecha_api.routines.routines_service.get_time_block_by_id_and_routine",
        return_value=mock_time_block,
    ), patch(
        "pecha_api.routines.routines_service.get_time_block_by_routine_and_time",
        return_value=conflicting_time_block,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await update_time_block_service(
                token="token123",
                routine_id=routine_id,
                time_block_id=time_block_id,
                request=request,
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["message"] == TIME_BLOCK_TIME_CONFLICT


# ============================================================================
# Get User Routine Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_user_routine_success():
    """Test successful retrieval of user routine with time blocks and sessions."""
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    _db_mock, session_cm = _mock_session_with_db()

    mock_routine = SimpleNamespace(id=routine_id, user_id=user_id)
    mock_time_block = SimpleNamespace(
        id=time_block_id,
        routine_id=routine_id,
        time="08:00",
        time_int=800,
        notification_enabled=True,
    )
    mock_session = SimpleNamespace(
        id=session_id,
        time_block_id=time_block_id,
        session_type=SessionType.PLAN,
        source_id=source_id,
        display_order=0,
    )
    mock_plan = SimpleNamespace(
        id=source_id,
        title="Morning Meditation",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/image.jpg",
    )

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_user_id",
        return_value=mock_routine,
    ), patch(
        "pecha_api.routines.routines_service.get_time_blocks",
        return_value=([mock_time_block], 1),
    ), patch(
        "pecha_api.routines.routines_service.get_sessions_by_time_block_ids",
        return_value=[mock_session],
    ), patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ):
        result = await get_user_routine(token="token123", skip=0, limit=20)

        assert result.id == routine_id
        assert result.skip == 0
        assert result.limit == 20
        assert result.total == 1
        assert len(result.time_blocks) == 1
        assert result.time_blocks[0].id == time_block_id
        assert result.time_blocks[0].time == "08:00"
        assert result.time_blocks[0].sessions[0].title == "Morning Meditation"


@pytest.mark.asyncio
async def test_get_user_routine_no_existing_routine_raises_bad_request():
    """Test that 400 Bad Request is raised if user has no existing routine."""
    user_id = uuid.uuid4()

    _db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_user_id",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_routine(token="token123", skip=0, limit=20)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["message"] == "No routine created for this user"


@pytest.mark.asyncio
async def test_get_user_routine_empty_time_blocks():
    """Test retrieval of routine with no time blocks."""
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()

    _db_mock, session_cm = _mock_session_with_db()

    mock_routine = SimpleNamespace(id=routine_id, user_id=user_id)

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_user_id",
        return_value=mock_routine,
    ), patch(
        "pecha_api.routines.routines_service.get_time_blocks",
        return_value=([], 0),
    ):
        result = await get_user_routine(token="token123", skip=0, limit=20)

        assert result.id == routine_id
        assert result.time_blocks == []
        assert result.total == 0


@pytest.mark.asyncio
async def test_get_user_routine_with_pagination():
    """Test retrieval of routine with custom pagination parameters."""
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id = uuid.uuid4()

    _db_mock, session_cm = _mock_session_with_db()

    mock_routine = SimpleNamespace(id=routine_id, user_id=user_id)
    mock_time_block = SimpleNamespace(
        id=time_block_id,
        routine_id=routine_id,
        time="12:00",
        time_int=1200,
        notification_enabled=False,
    )

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_user_id",
        return_value=mock_routine,
    ), patch(
        "pecha_api.routines.routines_service.get_time_blocks",
        return_value=([mock_time_block], 15),
    ), patch(
        "pecha_api.routines.routines_service.get_sessions_by_time_block_ids",
        return_value=[],
    ):
        result = await get_user_routine(token="token123", skip=5, limit=10)

        assert result.skip == 5
        assert result.limit == 10
        assert result.total == 15


@pytest.mark.asyncio
async def test_get_user_routine_with_multiple_time_blocks():
    """Test retrieval of routine with multiple time blocks."""
    user_id = uuid.uuid4()
    routine_id = uuid.uuid4()
    time_block_id_1 = uuid.uuid4()
    time_block_id_2 = uuid.uuid4()
    session_id_1 = uuid.uuid4()
    session_id_2 = uuid.uuid4()
    source_id_1 = uuid.uuid4()
    source_id_2 = uuid.uuid4()

    _db_mock, session_cm = _mock_session_with_db()

    mock_routine = SimpleNamespace(id=routine_id, user_id=user_id)
    mock_time_blocks = [
        SimpleNamespace(
            id=time_block_id_1,
            routine_id=routine_id,
            time="06:00",
            time_int=600,
            notification_enabled=True,
        ),
        SimpleNamespace(
            id=time_block_id_2,
            routine_id=routine_id,
            time="20:00",
            time_int=2000,
            notification_enabled=True,
        ),
    ]
    mock_sessions = [
        SimpleNamespace(
            id=session_id_1,
            time_block_id=time_block_id_1,
            session_type=SessionType.PLAN,
            source_id=source_id_1,
            display_order=0,
        ),
        SimpleNamespace(
            id=session_id_2,
            time_block_id=time_block_id_2,
            session_type=SessionType.RECITATION,
            source_id=source_id_2,
            display_order=0,
        ),
    ]
    mock_plan = SimpleNamespace(
        id=source_id_1,
        title="Morning Practice",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/morning.jpg",
    )
    mock_text = SimpleNamespace(
        id=source_id_2,
        title="Evening Recitation",
        language="bo",
    )

    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.routines.routines_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.routines.routines_service.get_routine_by_user_id",
        return_value=mock_routine,
    ), patch(
        "pecha_api.routines.routines_service.get_time_blocks",
        return_value=(mock_time_blocks, 2),
    ), patch(
        "pecha_api.routines.routines_service.get_sessions_by_time_block_ids",
        return_value=mock_sessions,
    ), patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ), patch(
        "pecha_api.routines.routines_service.Text.get_texts_by_ids",
        new_callable=AsyncMock,
        return_value=[mock_text],
    ):
        result = await get_user_routine(token="token123", skip=0, limit=20)

        assert result.id == routine_id
        assert len(result.time_blocks) == 2
        assert result.time_blocks[0].time == "06:00"
        assert result.time_blocks[1].time == "20:00"
        assert result.total == 2


@pytest.mark.asyncio
async def test_get_user_routine_invalid_token():
    """Test that invalid token raises HTTPException."""
    with patch(
        "pecha_api.routines.routines_service.validate_and_extract_user_details",
        side_effect=HTTPException(status_code=401, detail="Invalid token"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_user_routine(token="invalid_token", skip=0, limit=20)
        assert exc_info.value.status_code == 401


# ============================================================================
# Helper Function Tests
# ============================================================================


def test_group_sessions_by_block():
    """Test grouping sessions by their time block IDs."""
    time_block_id_1 = uuid.uuid4()
    time_block_id_2 = uuid.uuid4()

    sessions = [
        SimpleNamespace(
            id=uuid.uuid4(),
            time_block_id=time_block_id_1,
            session_type=SessionType.PLAN,
            source_id=uuid.uuid4(),
            display_order=0,
        ),
        SimpleNamespace(
            id=uuid.uuid4(),
            time_block_id=time_block_id_1,
            session_type=SessionType.RECITATION,
            source_id=uuid.uuid4(),
            display_order=1,
        ),
        SimpleNamespace(
            id=uuid.uuid4(),
            time_block_id=time_block_id_2,
            session_type=SessionType.PLAN,
            source_id=uuid.uuid4(),
            display_order=0,
        ),
    ]

    result = group_sessions_by_block(sessions)

    assert len(result) == 2
    assert len(result[time_block_id_1]) == 2
    assert len(result[time_block_id_2]) == 1


def test_group_sessions_by_block_empty_list():
    """Test grouping empty session list."""
    result = group_sessions_by_block([])
    assert result == {}


@pytest.mark.asyncio
async def test_build_time_block_dto():
    """Test building TimeBlockDTO from time block and sessions."""
    time_block_id = uuid.uuid4()
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    time_block = SimpleNamespace(
        id=time_block_id,
        time="08:00",
        time_int=800,
        notification_enabled=True,
    )
    session = SimpleNamespace(
        id=session_id,
        time_block_id=time_block_id,
        session_type=SessionType.PLAN,
        source_id=source_id,
        display_order=0,
    )
    mock_plan = SimpleNamespace(
        id=source_id,
        title="Test Plan",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/image.jpg",
    )

    with patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ):
        result = await build_time_block_dto(
            db=MagicMock(), time_block=time_block, sessions=[session]
        )

        assert result.id == time_block_id
        assert result.time == "08:00"
        assert result.time_int == 800
        assert result.notification_enabled is True
        assert len(result.sessions) == 1
        assert result.sessions[0].title == "Test Plan"


@pytest.mark.asyncio
async def test_resolve_sessions_mixed_types():
    """Test resolving sessions with both PLAN and RECITATION types."""
    plan_session_id = uuid.uuid4()
    recitation_session_id = uuid.uuid4()
    plan_source_id = uuid.uuid4()
    recitation_source_id = uuid.uuid4()

    sessions = [
        SimpleNamespace(
            id=plan_session_id,
            session_type=SessionType.PLAN,
            source_id=plan_source_id,
            display_order=1,
        ),
        SimpleNamespace(
            id=recitation_session_id,
            session_type=SessionType.RECITATION,
            source_id=recitation_source_id,
            display_order=0,
        ),
    ]

    mock_plan = SimpleNamespace(
        id=plan_source_id,
        title="Plan Title",
        language=SimpleNamespace(value="EN"),
        image_url="https://example.com/plan.jpg",
    )
    mock_text = SimpleNamespace(
        id=recitation_source_id,
        title="Recitation Title",
        language="bo",
    )

    with patch(
        "pecha_api.routines.routines_service.get_plans_by_ids",
        return_value=[mock_plan],
    ), patch(
        "pecha_api.routines.routines_service.Text.get_texts_by_ids",
        new_callable=AsyncMock,
        return_value=[mock_text],
    ):
        result = await _resolve_sessions(db=MagicMock(), sessions=sessions)

        # Results should be sorted by display_order
        assert len(result) == 2
        assert result[0].display_order == 0  # Recitation first
        assert result[1].display_order == 1  # Plan second
        assert result[0].title == "Recitation Title"
        assert result[1].title == "Plan Title"


@pytest.mark.asyncio
async def test_resolve_sessions_empty_list():
    """Test resolving empty session list."""
    result = await _resolve_sessions(db=MagicMock(), sessions=[])
    assert result == []
