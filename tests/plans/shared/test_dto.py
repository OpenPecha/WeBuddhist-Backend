from datetime import datetime
from uuid import uuid4

from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.plans.shared.dto import SeriesPlanBriefDTO, UserInfoBriefDTO


def test_user_info_brief_dto_all_fields():
    user_id = uuid4()
    dto = UserInfoBriefDTO(
        id=user_id,
        firstname="John",
        lastname="Doe",
        username="johndoe",
        avatar_url="https://example.com/avatar.jpg"
    )

    assert dto.id == user_id
    assert dto.firstname == "John"
    assert dto.lastname == "Doe"
    assert dto.username == "johndoe"
    assert dto.avatar_url == "https://example.com/avatar.jpg"


def test_user_info_brief_dto_minimal_fields():
    user_id = uuid4()
    dto = UserInfoBriefDTO(
        id=user_id,
        firstname="John"
    )

    assert dto.id == user_id
    assert dto.firstname == "John"
    assert dto.lastname is None
    assert dto.username is None
    assert dto.avatar_url is None


def test_series_plan_brief_dto_all_fields():
    plan_id = uuid4()
    started_at = datetime(2025, 1, 1, 12, 0, 0)
    image = ImageUrlModel(
        thumbnail="https://example.com/thumb.jpg",
        medium="https://example.com/medium.jpg",
        original="https://example.com/original.jpg"
    )

    dto = SeriesPlanBriefDTO(
        id=plan_id,
        title="Morning Practice",
        image=image,
        display_order=1,
        total_days=30,
        is_completed=False,
        started_at=started_at,
        status="in_progress"
    )

    assert dto.id == plan_id
    assert dto.title == "Morning Practice"
    assert dto.image == image
    assert dto.display_order == 1
    assert dto.total_days == 30
    assert dto.is_completed is False
    assert dto.started_at == started_at
    assert dto.status == "in_progress"


def test_series_plan_brief_dto_minimal_fields():
    plan_id = uuid4()
    dto = SeriesPlanBriefDTO(
        id=plan_id,
        title="Meditation"
    )

    assert dto.id == plan_id
    assert dto.title == "Meditation"
    assert dto.image is None
    assert dto.display_order is None
    assert dto.total_days == 0
    assert dto.is_completed is False
    assert dto.started_at is None
    assert dto.status is None


def test_series_plan_brief_dto_completed_status():
    plan_id = uuid4()
    dto = SeriesPlanBriefDTO(
        id=plan_id,
        title="Completed Practice",
        is_completed=True,
        total_days=30,
        status="completed"
    )

    assert dto.is_completed is True
    assert dto.total_days == 30
    assert dto.status == "completed"


def test_user_info_brief_dto_validation():
    user_id = uuid4()
    dto_dict = {
        "id": str(user_id),
        "firstname": "Jane",
        "lastname": "Smith"
    }
    dto = UserInfoBriefDTO(**dto_dict)

    assert dto.id == user_id
    assert dto.firstname == "Jane"
    assert dto.lastname == "Smith"
