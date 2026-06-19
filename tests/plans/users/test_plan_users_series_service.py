import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

from pecha_api.plans.plans_enums import EnrollmentSource, SeriesStatus, UserPlanStatus
from pecha_api.plans.users.plan_user_series_repository import _filter_plans_by_date_availability
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.plans.users.plan_users_response_models import (
    UserSeriesEnrollRequest,
    UpdateSeriesEnrollmentRequest,
)
from pecha_api.plans.authors.plan_authors_service import safe_get_image_url
from pecha_api.plans.users.plan_users_service import (
    _compute_series_plan_progress,
    _build_user_series_enrollment_dto,
    _build_series_plan_dto_for_progress,
    enroll_user_in_series,
    get_user_series_enrollments,
    get_user_series_days_completed,
    get_user_series_progress,
    update_user_series_enrollment_service,
    unenroll_user_from_series,
    is_user_enrolled_in_plan,
    get_or_create_plan_progress,
    handle_plan_completion_and_series_progression,
    auto_enroll_in_next_plan,
    check_plan_completion,
)


def _mock_session_with_db():
    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    return db_mock, session_cm


def _mock_series_query(db_mock, series):
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = series
    db_mock.query.return_value = mock_query


def _plan_for_date_filter(*, plan_id, series_id, display_order, start_date):
    return SimpleNamespace(
        id=plan_id,
        series_id=series_id,
        display_order=display_order,
        start_date=start_date,
    )


def test_filter_plans_by_date_availability_excludes_display_order_zero():
    series_id = uuid.uuid4()
    today = datetime.now(timezone.utc)
    started = today - timedelta(days=1)

    first_plan = _plan_for_date_filter(
        plan_id=uuid.uuid4(),
        series_id=series_id,
        display_order=0,
        start_date=started,
    )
    second_plan = _plan_for_date_filter(
        plan_id=uuid.uuid4(),
        series_id=series_id,
        display_order=1,
        start_date=started,
    )

    result = _filter_plans_by_date_availability([first_plan, second_plan])

    assert len(result) == 1
    assert result[0].id == second_plan.id


def test_safe_get_image_url_returns_none_when_no_key():
    result = safe_get_image_url(None, resource_id=uuid.uuid4(), resource_type="series")
    assert result is None


def test_safe_get_image_url_delegates_to_get_image_url():
    resource_id = uuid.uuid4()
    expected = ImageUrlModel(
        thumbnail="https://signed.example.com/thumb.jpg",
        medium="https://signed.example.com/medium.jpg",
        original="https://signed.example.com/img.jpg",
    )
    with patch(
        "pecha_api.plans.authors.plan_authors_service.get_image_url",
        return_value=expected,
    ) as mock_get:
        result = safe_get_image_url(
            "images/series/original/cover.jpg", resource_id=resource_id, resource_type="series"
        )

    assert result == expected
    mock_get.assert_called_once_with(image_url="images/series/original/cover.jpg")


def test_safe_get_image_url_returns_none_on_error():
    resource_id = uuid.uuid4()
    with patch(
        "pecha_api.plans.authors.plan_authors_service.get_image_url",
        side_effect=Exception("S3 error"),
    ):
        result = safe_get_image_url(
            "images/series.jpg", resource_id=resource_id, resource_type="series"
        )

    assert result is None


def test_compute_series_plan_progress_empty_plans():
    total, completed, percentage = _compute_series_plan_progress([], {})
    assert total == 0
    assert completed == 0
    assert percentage == 0.0


def test_compute_series_plan_progress_partial_completion():
    plan_a_id, plan_b_id = uuid.uuid4(), uuid.uuid4()
    all_plans = [SimpleNamespace(id=plan_a_id), SimpleNamespace(id=plan_b_id)]
    progress_by_plan_id = {
        plan_a_id: SimpleNamespace(is_completed=True),
        plan_b_id: SimpleNamespace(is_completed=False),
    }

    total, completed, percentage = _compute_series_plan_progress(all_plans, progress_by_plan_id)

    assert total == 2
    assert completed == 1
    assert percentage == 50.0


def test_build_user_series_enrollment_dto_with_metadata_and_progress():
    enrollment_id = uuid.uuid4()
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    current_plan_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    enrollment = SimpleNamespace(
        id=enrollment_id,
        user_id=user_id,
        series_id=series_id,
        current_plan_id=current_plan_id,
        enrolled_at=datetime.now(timezone.utc),
        status=SeriesStatus.ACTIVE,
        auto_enroll_next=True,
        is_completed=False,
        completed_at=None,
    )
    series = SimpleNamespace(
        id=series_id,
        image="images/series.jpg",
        metadata_entries=[SimpleNamespace(title="Series Title", description="Series Desc")],
    )

    from pecha_api.plans.media.media_response_models import ImageUrlModel

    series_image = ImageUrlModel(
        thumbnail="https://signed.example.com/series-thumb.jpg",
        medium="https://signed.example.com/series-medium.jpg",
        original="https://signed.example.com/series.jpg",
    )
    with patch(
        "pecha_api.plans.users.plan_users_service.safe_get_image_url",
        return_value=series_image,
    ):
        dto = _build_user_series_enrollment_dto(
            enrollment,
            series,
            {current_plan_id: "Current Plan"},
            {series_id: [SimpleNamespace(id=plan_id)]},
            {plan_id: SimpleNamespace(is_completed=True)},
        )

    assert dto.id == enrollment_id
    assert dto.series_title == "Series Title"
    assert dto.series_description == "Series Desc"
    assert dto.image == series_image
    assert dto.current_plan_title == "Current Plan"
    assert dto.total_plans == 1
    assert dto.completed_plans == 1
    assert dto.progress_percentage == 100.0


def test_build_user_series_enrollment_dto_without_metadata():
    series_id = uuid.uuid4()
    enrollment = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        series_id=series_id,
        current_plan_id=None,
        enrolled_at=datetime.now(timezone.utc),
        status="ACTIVE",
        auto_enroll_next=False,
        is_completed=False,
        completed_at=None,
    )
    series = SimpleNamespace(id=series_id, image=None, metadata_entries=[])

    with patch(
        "pecha_api.plans.users.plan_users_service.safe_get_image_url",
        return_value=None,
    ):
        dto = _build_user_series_enrollment_dto(
            enrollment, series, {}, {series_id: []}, {}
        )

    assert dto.series_title == "Untitled Series"
    assert dto.series_description is None
    assert dto.current_plan_title is None
    assert dto.progress_percentage == 0.0


def test_build_series_plan_dto_for_progress():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    started_at = datetime.now(timezone.utc)
    plan = SimpleNamespace(
        id=plan_id,
        title="Plan A",
        description="Desc",
        language=SimpleNamespace(value="EN"),
        difficulty_level=SimpleNamespace(value="BEGINNER"),
        image_url="images/plan.jpg",
        tag_list=[],
        start_date=None,
        display_order=1,
    )
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_days_by_plan_id",
        return_value=[SimpleNamespace(), SimpleNamespace()],
    ), patch(
        "pecha_api.plans.users.plan_users_service.safe_get_image_url",
        return_value=ImageUrlModel(
            thumbnail="https://signed.example.com/plan-thumb.jpg",
            medium="https://signed.example.com/plan-medium.jpg",
            original="https://signed.example.com/plan.jpg",
        ),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=SimpleNamespace(started_at=started_at),
    ):
        dto = _build_series_plan_dto_for_progress(db_mock, plan, user_id)

    assert dto.id == plan_id
    assert dto.title == "Plan A"
    assert dto.total_days == 2
    assert dto.image.original == "https://signed.example.com/plan.jpg"
    assert dto.started_at == started_at


def test_enroll_user_in_series_success():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enroll_request = UserSeriesEnrollRequest(series_id=series_id)

    db_mock, session_cm = _mock_session_with_db()
    _mock_series_query(db_mock, SimpleNamespace(id=series_id))

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserSeriesEnrollment",
    ) as MockEnrollment, patch(
        "pecha_api.plans.users.plan_users_service.save_user_series_enrollment",
    ) as mock_save:
        constructed = SimpleNamespace(id=uuid.uuid4())
        MockEnrollment.return_value = constructed

        result = enroll_user_in_series(token="tok", enroll_request=enroll_request)

        assert result is None
        mock_save.assert_called_once_with(db_mock, constructed)


def test_enroll_user_in_series_start_immediately_auto_enrolls_first_plan():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    enrollment_id = uuid.uuid4()
    enroll_request = UserSeriesEnrollRequest(
        series_id=series_id, start_immediately=True, auto_enroll_next=True
    )

    db_mock, session_cm = _mock_session_with_db()
    _mock_series_query(db_mock, SimpleNamespace(id=series_id))
    first_plan = SimpleNamespace(id=plan_id)

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_first_plan_in_series",
        return_value=first_plan,
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserSeriesEnrollment",
    ) as MockEnrollment, patch(
        "pecha_api.plans.users.plan_users_service.save_user_series_enrollment",
    ), patch(
        "pecha_api.plans.users.plan_users_service.auto_enroll_in_next_plan",
    ) as mock_auto_enroll:
        constructed = SimpleNamespace(id=enrollment_id)
        MockEnrollment.return_value = constructed

        enroll_user_in_series(token="tok", enroll_request=enroll_request)

        mock_auto_enroll.assert_called_once_with(db_mock, user_id, plan_id, enrollment_id)


def test_enroll_user_in_series_not_found_raises_404():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enroll_request = UserSeriesEnrollRequest(series_id=series_id)

    db_mock, session_cm = _mock_session_with_db()
    _mock_series_query(db_mock, None)

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ):
        with pytest.raises(HTTPException) as exc_info:
            enroll_user_in_series(token="tok", enroll_request=enroll_request)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == "Series not found"


def test_enroll_user_in_series_already_enrolled_raises_409():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enroll_request = UserSeriesEnrollRequest(series_id=series_id)

    db_mock, session_cm = _mock_session_with_db()
    _mock_series_query(db_mock, SimpleNamespace(id=series_id))

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        with pytest.raises(HTTPException) as exc_info:
            enroll_user_in_series(token="tok", enroll_request=enroll_request)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["error"] == BAD_REQUEST
        assert exc_info.value.detail["message"] == "Already enrolled in series"


def test_get_user_series_enrollments_empty():
    user_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollments_by_user_id",
        return_value=([], 0),
    ):
        result = get_user_series_enrollments(token="tok", skip=0, limit=20)

    assert result.enrollments == []
    assert result.total == 0


def test_get_user_series_enrollments_success():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enrollment_id = uuid.uuid4()
    current_plan_id = uuid.uuid4()
    plan_id = current_plan_id

    enrollment = SimpleNamespace(
        id=enrollment_id,
        user_id=user_id,
        series_id=series_id,
        current_plan_id=current_plan_id,
        enrolled_at=datetime.now(timezone.utc),
        status=SeriesStatus.ACTIVE,
        auto_enroll_next=True,
        is_completed=False,
        completed_at=None,
    )
    series = SimpleNamespace(
        id=series_id,
        image="images/series.jpg",
        metadata_entries=[SimpleNamespace(title="My Series", description="Desc")],
    )
    plan = SimpleNamespace(id=plan_id, title="Plan 1")

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollments_by_user_id",
        return_value=([enrollment], 1),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_series_by_ids",
        return_value=[series],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plans_by_series_ids",
        return_value={series_id: [plan]},
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_ids",
        return_value={plan_id: SimpleNamespace(is_completed=True)},
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plans_by_ids",
        return_value=[plan],
    ), patch(
        "pecha_api.plans.users.plan_users_service.safe_get_image_url",
        return_value=ImageUrlModel(
            thumbnail="https://signed.example.com/series-thumb.jpg",
            medium="https://signed.example.com/series-medium.jpg",
            original="https://signed.example.com/series.jpg",
        ),
    ):
        result = get_user_series_enrollments(
            token="tok", status_filter="active", skip=0, limit=20
        )

    assert result.total == 1
    assert len(result.enrollments) == 1
    dto = result.enrollments[0]
    assert dto.series_title == "My Series"
    assert dto.current_plan_title == "Plan 1"
    assert dto.completed_plans == 1
    assert dto.progress_percentage == 100.0
    assert dto.image is not None
    assert dto.image.original == "https://signed.example.com/series.jpg"


def test_get_user_series_enrollments_skips_missing_series():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enrollment = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        series_id=series_id,
        current_plan_id=None,
        enrolled_at=datetime.now(timezone.utc),
        status=SeriesStatus.ACTIVE,
        auto_enroll_next=True,
        is_completed=False,
        completed_at=None,
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollments_by_user_id",
        return_value=([enrollment], 1),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_series_by_ids",
        return_value=[],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plans_by_series_ids",
        return_value={},
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_ids",
        return_value={},
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plans_by_ids",
        return_value=[],
    ):
        result = get_user_series_enrollments(token="tok")

    assert result.enrollments == []


def test_get_user_series_enrollments_presigned_url_error():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enrollment = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        series_id=series_id,
        current_plan_id=None,
        enrolled_at=datetime.now(timezone.utc),
        status=SeriesStatus.ACTIVE,
        auto_enroll_next=True,
        is_completed=False,
        completed_at=None,
    )
    series = SimpleNamespace(
        id=series_id,
        image="images/series.jpg",
        metadata_entries=[],
    )

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollments_by_user_id",
        return_value=([enrollment], 1),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_series_by_ids",
        return_value=[series],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plans_by_series_ids",
        return_value={series_id: []},
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_ids",
        return_value={},
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plans_by_ids",
        return_value=[],
    ), patch(
        "pecha_api.plans.users.plan_users_service.safe_get_image_url",
        return_value=None,
    ):
        result = get_user_series_enrollments(token="tok")

    assert len(result.enrollments) == 1
    assert result.enrollments[0].image is None


def test_get_user_series_days_completed_empty():
    user_id = uuid.uuid4()
    mock_user = SimpleNamespace(id=user_id)
    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_days_completed_paginated",
        return_value=([], 0),
    ):
        result = get_user_series_days_completed(token="tok", skip=0, limit=20)

    assert result.series == []
    assert result.total == 0
    assert result.skip == 0
    assert result.limit == 20


def test_get_user_series_days_completed_success():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    mock_user = SimpleNamespace(id=user_id)
    db_mock, session_cm = _mock_session_with_db()

    series = SimpleNamespace(
        id=series_id,
        image="series-image-key",
        metadata_entries=[SimpleNamespace(title="Morning Practice", description="Daily series")],
    )

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=mock_user,
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_days_completed_paginated",
        return_value=([(series_id, 12)], 1),
    ) as mock_repo, patch(
        "pecha_api.plans.users.plan_users_service.get_series_by_ids",
        return_value=[series],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_group_ids_by_series_ids",
        return_value={series_id: uuid.uuid4()},
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_group_summaries_by_ids",
        return_value={},
    ), patch(
        "pecha_api.plans.users.plan_users_service.safe_get_image_url",
        return_value=ImageUrlModel(
            thumbnail="https://signed.example.com/thumb.jpg",
            medium="https://signed.example.com/medium.jpg",
            original="https://signed.example.com/original.jpg",
        ),
    ):
        result = get_user_series_days_completed(token="tok", skip=0, limit=20)

    mock_repo.assert_called_once_with(
        db=db_mock,
        user_id=user_id,
        skip=0,
        limit=20,
    )
    assert result.total == 1
    assert len(result.series) == 1
    assert result.series[0].series_id == series_id
    assert result.series[0].series_title == "Morning Practice"
    assert result.series[0].days_completed == 12


def test_get_user_series_progress_success():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enrollment_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    enrollment = SimpleNamespace(
        id=enrollment_id,
        enrolled_at=datetime.now(timezone.utc),
        status=SeriesStatus.ACTIVE,
        auto_enroll_next=True,
        current_plan_id=plan_id,
        is_completed=False,
        completed_at=None,
    )
    series = SimpleNamespace(
        id=series_id,
        metadata_entries=[SimpleNamespace(title="Series", description="Desc")],
    )
    plan = SimpleNamespace(
        id=plan_id,
        title="Plan 1",
        description="Plan desc",
        language=SimpleNamespace(value="EN"),
        difficulty_level=SimpleNamespace(value="BEGINNER"),
        image_url=None,
        tag_list=[],
        start_date=None,
        display_order=1,
    )

    db_mock, session_cm = _mock_session_with_db()
    _mock_series_query(db_mock, series)

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=enrollment,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plans_by_series_id",
        return_value=[plan],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_days_by_plan_id",
        return_value=[SimpleNamespace()],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=SimpleNamespace(started_at=datetime.now(timezone.utc)),
    ), patch(
        "pecha_api.plans.users.plan_users_service.safe_get_image_url",
        return_value=None,
    ):
        result = get_user_series_progress(token="tok", series_id=series_id)

    assert result.id == enrollment_id
    assert result.series_title == "Series"
    assert len(result.plans) == 1
    assert result.plans[0].title == "Plan 1"
    assert result.plans[0].image is None


def test_get_user_series_progress_not_enrolled_raises_404():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_user_series_progress(token="tok", series_id=series_id)

        assert exc_info.value.status_code == 404
        assert "Not enrolled" in exc_info.value.detail["message"]


def test_get_user_series_progress_series_not_found_raises_404():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()
    _mock_series_query(db_mock, None)

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_user_series_progress(token="tok", series_id=series_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["message"] == "Series not found"


def test_update_user_series_enrollment_service_success():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()
    enrollment = SimpleNamespace(
        auto_enroll_next=True,
        status=SeriesStatus.ACTIVE,
    )
    update_request = UpdateSeriesEnrollmentRequest(
        auto_enroll_next=False, status=SeriesStatus.PAUSED
    )

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=enrollment,
    ), patch(
        "pecha_api.plans.users.plan_users_service.update_user_series_enrollment",
    ) as mock_update:
        update_user_series_enrollment_service(
            token="tok", series_id=series_id, update_request=update_request
        )

        assert enrollment.auto_enroll_next is False
        assert enrollment.status == SeriesStatus.PAUSED
        mock_update.assert_called_once_with(db_mock, enrollment)


def test_update_user_series_enrollment_service_not_enrolled_raises_404():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()

    _, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=None,
    ):
        with pytest.raises(HTTPException) as exc_info:
            update_user_series_enrollment_service(
                token="tok",
                series_id=series_id,
                update_request=UpdateSeriesEnrollmentRequest(),
            )

        assert exc_info.value.status_code == 404


def test_unenroll_user_from_series_success():
    user_id = uuid.uuid4()
    series_id = uuid.uuid4()

    db_mock, session_cm = _mock_session_with_db()

    with patch(
        "pecha_api.plans.users.plan_users_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.users.plan_users_service.delete_user_series_enrollment",
    ) as mock_delete:
        result = unenroll_user_from_series(token="tok", series_id=series_id)

        assert result is None
        mock_delete.assert_called_once_with(db_mock, user_id, series_id)


def test_is_user_enrolled_in_plan_direct_enrollment():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        assert is_user_enrolled_in_plan(db_mock, user_id, plan_id) is True


def test_is_user_enrolled_in_plan_via_series_enrollment():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    series_id = uuid.uuid4()
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_by_id",
        return_value=SimpleNamespace(series_id=series_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=SimpleNamespace(id=uuid.uuid4()),
    ):
        assert is_user_enrolled_in_plan(db_mock, user_id, plan_id) is True


def test_is_user_enrolled_in_plan_returns_false_when_not_enrolled():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_by_id",
        return_value=SimpleNamespace(series_id=None),
    ):
        assert is_user_enrolled_in_plan(db_mock, user_id, plan_id) is False


def test_get_or_create_plan_progress_returns_existing():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    db_mock = MagicMock()
    existing = SimpleNamespace(id=uuid.uuid4())

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=existing,
    ):
        result = get_or_create_plan_progress(db_mock, user_id, plan_id)

    assert result is existing


def test_get_or_create_plan_progress_creates_for_series_enrollment():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    series_id = uuid.uuid4()
    series_enrollment_id = uuid.uuid4()
    db_mock = MagicMock()
    created = SimpleNamespace(id=uuid.uuid4())

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_by_id",
        return_value=SimpleNamespace(series_id=series_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=SimpleNamespace(id=series_enrollment_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserPlanProgress",
    ) as mock_progress_cls, patch(
        "pecha_api.plans.users.plan_users_service.save_plan_progress",
        return_value=created,
    ) as mock_save:
        mock_progress_cls.return_value = created
        result = get_or_create_plan_progress(db_mock, user_id, plan_id)

    assert result is created
    mock_save.assert_called_once_with(db_mock, created)
    progress_kwargs = mock_progress_cls.call_args.kwargs
    assert progress_kwargs["enrollment_source"] == EnrollmentSource.SERIES
    assert progress_kwargs["series_enrollment_id"] == series_enrollment_id
    assert progress_kwargs["auto_enrolled"] is True


def test_get_or_create_plan_progress_returns_none_without_series_enrollment():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_plan_by_id",
        return_value=SimpleNamespace(series_id=uuid.uuid4()),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_user_series_enrollment_by_user_and_series",
        return_value=None,
    ):
        assert get_or_create_plan_progress(db_mock, user_id, plan_id) is None


def test_handle_plan_completion_returns_when_no_progress():
    db_mock = MagicMock()
    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=None,
    ):
        handle_plan_completion_and_series_progression(db_mock, uuid.uuid4(), uuid.uuid4())


def test_handle_plan_completion_skips_when_already_completed():
    db_mock = MagicMock()
    progress = SimpleNamespace(is_completed=True)

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=progress,
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_plan_progress",
    ) as mock_save:
        handle_plan_completion_and_series_progression(db_mock, uuid.uuid4(), uuid.uuid4())

    mock_save.assert_not_called()


def test_handle_plan_completion_marks_plan_completed_without_series():
    db_mock = MagicMock()
    progress = SimpleNamespace(
        is_completed=False,
        series_enrollment_id=None,
    )

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=progress,
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_plan_progress",
    ) as mock_save:
        handle_plan_completion_and_series_progression(
            db_mock, uuid.uuid4(), uuid.uuid4()
        )

    assert progress.is_completed is True
    assert progress.status == UserPlanStatus.COMPLETED
    assert progress.completed_at is not None
    mock_save.assert_called_once_with(db_mock, progress)


def test_handle_plan_completion_auto_enrolls_next_plan_in_series():
    user_id = uuid.uuid4()
    completed_plan_id = uuid.uuid4()
    series_id = uuid.uuid4()
    next_plan_id = uuid.uuid4()
    series_enrollment_id = uuid.uuid4()
    db_mock = MagicMock()

    progress = SimpleNamespace(
        is_completed=False,
        series_enrollment_id=series_enrollment_id,
    )
    series_enrollment = SimpleNamespace(
        id=series_enrollment_id,
        series_id=series_id,
        auto_enroll_next=True,
    )
    db_mock.query.return_value.filter.return_value.first.return_value = series_enrollment

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=progress,
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_plan_progress",
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_next_plan_in_series",
        return_value=SimpleNamespace(id=next_plan_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.auto_enroll_in_next_plan",
    ) as mock_auto_enroll, patch(
        "pecha_api.plans.users.plan_users_service.update_current_plan_in_series",
    ) as mock_update_current:
        handle_plan_completion_and_series_progression(
            db_mock, user_id, completed_plan_id
        )

    mock_auto_enroll.assert_called_once_with(
        db_mock, user_id, next_plan_id, series_enrollment_id
    )
    mock_update_current.assert_called_once_with(
        db_mock, user_id, series_id, next_plan_id
    )


def test_handle_plan_completion_marks_series_completed_when_no_next_plan():
    user_id = uuid.uuid4()
    completed_plan_id = uuid.uuid4()
    series_id = uuid.uuid4()
    series_enrollment_id = uuid.uuid4()
    db_mock = MagicMock()

    progress = SimpleNamespace(
        is_completed=False,
        series_enrollment_id=series_enrollment_id,
    )
    series_enrollment = SimpleNamespace(
        id=series_enrollment_id,
        series_id=series_id,
        auto_enroll_next=True,
    )
    db_mock.query.return_value.filter.return_value.first.return_value = series_enrollment

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=progress,
    ), patch(
        "pecha_api.plans.users.plan_users_service.save_plan_progress",
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_next_plan_in_series",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.is_series_completed_for_user",
        return_value=True,
    ), patch(
        "pecha_api.plans.users.plan_users_service.mark_series_enrollment_completed",
    ) as mock_mark_completed:
        handle_plan_completion_and_series_progression(
            db_mock, user_id, completed_plan_id
        )

    mock_mark_completed.assert_called_once_with(db_mock, user_id, series_id)


def test_auto_enroll_in_next_plan_returns_existing_progress():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    db_mock = MagicMock()
    existing = SimpleNamespace(id=uuid.uuid4())

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=existing,
    ):
        result = auto_enroll_in_next_plan(
            db_mock, user_id, plan_id, uuid.uuid4()
        )

    assert result is existing


def test_auto_enroll_in_next_plan_creates_progress_record():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    series_enrollment_id = uuid.uuid4()
    db_mock = MagicMock()
    created = SimpleNamespace(id=uuid.uuid4())

    with patch(
        "pecha_api.plans.users.plan_users_service.get_plan_progress_by_user_id_and_plan_id",
        return_value=None,
    ), patch(
        "pecha_api.plans.users.plan_users_service.UserPlanProgress",
    ) as mock_progress_cls, patch(
        "pecha_api.plans.users.plan_users_service.save_plan_progress",
        return_value=created,
    ) as mock_save:
        mock_progress_cls.return_value = created
        result = auto_enroll_in_next_plan(
            db_mock, user_id, plan_id, series_enrollment_id
        )

    assert result is created
    mock_save.assert_called_once_with(db_mock, created)
    progress_kwargs = mock_progress_cls.call_args.kwargs
    assert progress_kwargs["enrollment_source"] == EnrollmentSource.SERIES
    assert progress_kwargs["series_enrollment_id"] == series_enrollment_id


def test_check_plan_completion_returns_when_day_not_found():
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.items.plan_items_repository.get_plan_item_by_id",
        return_value=None,
    ):
        check_plan_completion(db_mock, uuid.uuid4(), uuid.uuid4())


def test_check_plan_completion_triggers_series_progression_when_all_days_done():
    user_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()
    day_a_id, day_b_id = uuid.uuid4(), uuid.uuid4()
    db_mock = MagicMock()

    with patch(
        "pecha_api.plans.items.plan_items_repository.get_plan_item_by_id",
        return_value=SimpleNamespace(plan_id=plan_id),
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_days_by_plan_id",
        return_value=[SimpleNamespace(id=day_a_id), SimpleNamespace(id=day_b_id)],
    ), patch(
        "pecha_api.plans.users.plan_users_service.get_completed_day_ids_by_user_id_and_day_ids",
        return_value=[day_a_id, day_b_id],
    ), patch(
        "pecha_api.plans.users.plan_users_service.handle_plan_completion_and_series_progression",
    ) as mock_handle:
        check_plan_completion(db_mock, user_id, day_id)

    mock_handle.assert_called_once_with(db_mock, user_id, plan_id)
