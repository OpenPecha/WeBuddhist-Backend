import uuid
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus, PlanAudioType, MonlamVoiceName, AudioJobStatus
from pecha_api.plans.plans_response_models import CreatePlanRequest, PlanDTO, PlansResponse, PlanDayDTO, GeneratePlanAudioRequest
from pecha_api.plans.cms.cms_plans_views import create_plan, get_plans, get_plan_day_content, generate_plan_audio, get_plan_audio_job_status
from pecha_api.plans.plans_response_models import UpdatePlanRequest, PlanStatusUpdate, PlanWithDays
from pecha_api.plans.cms.cms_plans_views import get_plan_details, update_plan, delete_plan, update_plan_status
from pecha_api.plans.audio.plan_audio_response_models import AudioJobAcceptedResponse, AudioJobStatusResponse


class _Creds:
    def __init__(self, token: str):
        self.credentials = token


@pytest.mark.asyncio
async def test_create_plan_success():
    request = CreatePlanRequest(
        group_id=uuid.uuid4(),
        title="Mindfulness Basics",
        description="A simple plan to get started with mindfulness.",
        difficulty_level=DifficultyLevel.BEGINNER,
        total_days=7,
        language="en",
        image_url="https://example.com/image.jpg",
        tags=["mindfulness", "beginner"],
        start_date=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )

    plan_id = uuid.uuid4()
    expected = PlanDTO(
        id=plan_id,
        title=request.title,
        description=request.description,
        language=request.language,
        image_url=request.image_url,
        total_days=0,
        status=PlanStatus.DRAFT,
        subscription_count=0,
        start_date=request.start_date,
    )

    creds = _Creds(token="token123")

    with patch("pecha_api.plans.cms.cms_plans_views.create_new_plan", return_value=expected) as mock_create:
        response = await create_plan(authentication_credential=creds, create_plan_request=request)

        mock_create.assert_called_once_with(token="token123", create_plan_request=request)

        assert response is not None
        assert isinstance(response, PlanDTO)
        assert response.id == plan_id
        assert response.title == request.title
        assert response.description == request.description
        assert response.image_url == request.image_url
        assert response.total_days == 0
        assert response.status == PlanStatus.DRAFT
        assert response.subscription_count == 0
        assert response.start_date == request.start_date



def test_get_plans_success_with_params():
    creds = _Creds(token="token123")

    plan1 = PlanDTO(
        id=uuid.uuid4(),
        title="Plan One",
        description="Desc 1",
        language="en",
        image_url="https://example.com/1.jpg",
        total_days=0,
        status=PlanStatus.PUBLISHED,
        subscription_count=0,
    )
    plan2 = PlanDTO(
        id=uuid.uuid4(),
        title="Plan Two",
        description="Desc 2",
        language="en",
        image_url="https://example.com/2.jpg",
        total_days=0,
        status=PlanStatus.DRAFT,
        subscription_count=0,
    )
    expected = PlansResponse(plans=[plan1, plan2], skip=1, limit=5, total=2)

    with patch("pecha_api.plans.cms.cms_plans_views.get_filtered_plans", return_value=expected) as mock_service:
        resp = get_plans(
            authentication_credential=creds,
            search="plan",
            language="en",
            sort_by="status",
            sort_order="asc",
            skip=1,
            limit=5,
        )

        assert mock_service.call_count == 1
        called_kwargs = mock_service.call_args.kwargs
        assert called_kwargs == {
            "token": "token123",
            "search": "plan",
            "sort_by": "status",
            "sort_order": "asc",
            "skip": 1,
            "limit": 5,
            "language": "en",
        }

        assert resp == expected


def test_get_plans_defaults():
    creds = _Creds(token="tkn")
    expected = PlansResponse(plans=[], skip=0, limit=10, total=0)

    with patch("pecha_api.plans.cms.cms_plans_views.get_filtered_plans", return_value=expected) as mock_service:
        # Pass explicit defaults to avoid FastAPI Query objects when calling directly
        resp = get_plans(
            authentication_credential=creds,
            search=None,
            language=None,
            sort_by="total_days",
            sort_order="asc",
            skip=0,
            limit=10,
        )

        assert mock_service.call_count == 1
        called_kwargs = mock_service.call_args.kwargs
        assert called_kwargs == {
            "token": "tkn",
            "search": None,
            "sort_by": "total_days",
            "sort_order": "asc",
            "skip": 0,
            "limit": 10,
            "language": None,
        }
        assert resp == expected


@pytest.mark.asyncio
async def test_get_plan_day_content_success():
    creds = _Creds(token="token123")
    plan_id = uuid.uuid4()
    day_number = 3

    expected = PlanDayDTO(
        id=uuid.uuid4(),
        day_number=day_number,
        tasks=[],
    )

    with patch(
        "pecha_api.plans.cms.cms_plans_views.get_plan_day_details",
        return_value=expected,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_plan_day_content(
            authentication_credential=creds,
            plan_id=plan_id,
            day_number=day_number,
        )

        assert mock_service.call_count == 1
        called_kwargs = mock_service.call_args.kwargs
        assert called_kwargs == {
            "token": "token123",
            "plan_id": plan_id,
            "day_number": day_number,
        }

        assert resp == expected


@pytest.mark.asyncio
async def test_get_plan_details_success():
    creds = _Creds(token="tkn")
    plan_id = uuid.uuid4()

    expected = PlanWithDays(
        id=plan_id,
        title="Plan",
        description="Desc",
        language="en",
        image_url=None,
        plan_image_url=None,
        total_days=0,
        difficulty_level="BEGINNER",
        tags=[],
        status=PlanStatus.DRAFT,
        days=[],
        start_date=None,
    )

    with patch(
        "pecha_api.plans.cms.cms_plans_views.get_details_plan",
        return_value=expected,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_plan_details(authentication_credential=creds, plan_id=plan_id)

        assert mock_service.call_count == 1
        assert mock_service.call_args.kwargs == {"token": "tkn", "plan_id": plan_id}
        assert resp == expected


@pytest.mark.asyncio
async def test_update_plan_success():
    creds = _Creds(token="token123")
    plan_id = uuid.uuid4()

    request = UpdatePlanRequest(title="Updated", description="Desc")
    expected = PlanDTO(
        id=plan_id,
        title="Updated",
        description="Desc",
        language="en",
        image_url=None,
        image_key=None,
        total_days=3,
        tags=[],
        status=PlanStatus.DRAFT,
        subscription_count=0,
    )

    with patch(
        "pecha_api.plans.cms.cms_plans_views.update_plan_details",
        return_value=expected,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await update_plan(authentication_credential=creds, plan_id=plan_id, update_plan_request=request)

        assert mock_service.call_count == 1
        assert mock_service.call_args.kwargs == {
            "token": "token123",
            "plan_id": plan_id,
            "update_plan_request": request,
        }
        assert resp == expected


@pytest.mark.asyncio
async def test_delete_plan_success():
    creds = _Creds(token="tkn")
    plan_id = uuid.uuid4()

    with patch(
        "pecha_api.plans.cms.cms_plans_views.delete_selected_plan",
        return_value=None,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await delete_plan(authentication_credential=creds, plan_id=plan_id)

        assert mock_service.call_count == 1
        assert mock_service.call_args.kwargs == {"token": "tkn", "plan_id": plan_id}
        assert resp is None


@pytest.mark.asyncio
async def test_update_plan_status_success():
    creds = _Creds(token="token123")
    plan_id = uuid.uuid4()
    status_update = PlanStatusUpdate(status=PlanStatus.PUBLISHED)

    expected = PlanDTO(
        id=plan_id,
        title="Plan",
        description="Desc",
        language="en",
        image_url=None,
        image_key=None,
        total_days=1,
        tags=[],
        status=PlanStatus.PUBLISHED,
        subscription_count=1,
    )

    with patch(
        "pecha_api.plans.cms.cms_plans_views.update_selected_plan_status",
        return_value=expected,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await update_plan_status(authentication_credential=creds, plan_id=plan_id, plan_status_update=status_update)

        assert mock_service.call_count == 1
        assert mock_service.call_args.kwargs == {
            "token": "token123",
            "plan_id": plan_id,
            "plan_status_update": status_update,
        }
        assert resp == expected


@pytest.mark.asyncio
async def test_generate_plan_audio_endpoint_with_day_id():
    day_id = uuid.uuid4()
    job_id = uuid.uuid4()
    request = GeneratePlanAudioRequest(
        day_id=day_id,
        language="bo",
        type=PlanAudioType.TEXT_READING,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE,
    )

    expected = AudioJobAcceptedResponse(job_id=job_id, status=AudioJobStatus.PENDING)

    with patch(
        "pecha_api.plans.cms.cms_plans_views.enqueue_plan_audio_job",
        return_value=expected,
    ) as mock_service:
        resp = await generate_plan_audio(request=request)

        mock_service.assert_called_once_with(
            day_id=day_id,
            sub_task_id=None,
            language="bo",
            audio_type=PlanAudioType.TEXT_READING,
            voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE,
        )
        assert resp == expected


@pytest.mark.asyncio
async def test_generate_plan_audio_endpoint_with_subtask_id():
    sub_task_id = uuid.uuid4()
    job_id = uuid.uuid4()
    request = GeneratePlanAudioRequest(
        sub_task_id=sub_task_id,
        language="en",
        type=PlanAudioType.RECITATION,
        voice_name=MonlamVoiceName.YANGCHEN_LHASA_FEMALE,
    )

    expected = AudioJobAcceptedResponse(job_id=job_id, status=AudioJobStatus.PENDING)

    with patch(
        "pecha_api.plans.cms.cms_plans_views.enqueue_plan_audio_job",
        return_value=expected,
    ) as mock_service:
        resp = await generate_plan_audio(request=request)

        mock_service.assert_called_once_with(
            day_id=None,
            sub_task_id=sub_task_id,
            language="en",
            audio_type=PlanAudioType.RECITATION,
            voice_name=MonlamVoiceName.YANGCHEN_LHASA_FEMALE,
        )
        assert resp == expected


@pytest.mark.asyncio
async def test_get_plan_audio_job_status_endpoint():
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    expected = AudioJobStatusResponse(
        job_id=job_id,
        status=AudioJobStatus.COMPLETED,
        language="bo",
        type=PlanAudioType.TEXT_READING.value,
        voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE.value,
        audio_url="https://s3.example.com/audio.wav",
        audio_duration_ms=5000,
        s3_key="audio/plan_days/test.wav",
        created_at=now,
        updated_at=now,
    )

    with patch(
        "pecha_api.plans.cms.cms_plans_views.get_audio_job_status",
        return_value=expected,
    ) as mock_service:
        resp = await get_plan_audio_job_status(
            job_id=job_id,
            authentication_credential=_Creds("token"),
        )
        mock_service.assert_called_once_with(job_id=job_id)
        assert resp == expected


def test_generate_plan_audio_request_validation_requires_day_or_subtask():
    with pytest.raises(ValueError, match="Either day_id or sub_task_id must be provided"):
        GeneratePlanAudioRequest(
            language="bo",
            type=PlanAudioType.TEXT_READING,
        )


def test_generate_plan_audio_request_validation_rejects_both_ids():
    with pytest.raises(ValueError, match="Provide either day_id or sub_task_id, not both"):
        GeneratePlanAudioRequest(
            day_id=uuid.uuid4(),
            sub_task_id=uuid.uuid4(),
            language="bo",
            type=PlanAudioType.TEXT_READING,
        )

