import pytest

from pecha_api.traditions.tradition_onboarding import (
    get_tradition_onboarding_content,
    list_tradition_path_codes,
)
from pecha_api.traditions.tradition_service import get_tradition_onboarding_service


@pytest.mark.asyncio
async def test_get_tradition_onboarding_service_returns_english_by_default():
    response = await get_tradition_onboarding_service()

    assert response.title == "How do you follow the Buddha?"
    assert response.paths.pali.title == "Pāli scriptures"
    assert response.paths.chinese.title == "Chinese scriptures"
    assert response.paths.tibetan.title == "Sanskrit & Tibetan scriptures"
    assert response.footer


def test_get_tradition_onboarding_content_supports_language_codes():
    content = get_tradition_onboarding_content(language="zh")

    assert content["title"] == "您如何追随佛陀的教导？"


def test_get_tradition_onboarding_content_falls_back_to_english():
    content = get_tradition_onboarding_content(language="fr")

    assert content["title"] == "How do you follow the Buddha?"


def test_list_tradition_path_codes():
    assert list_tradition_path_codes() == frozenset({"pali", "chinese", "tibetan"})


def test_save_user_tradition_request_accepts_path_codes():
    from pecha_api.traditions.tradition_response_models import SaveUserTraditionRequest

    request = SaveUserTraditionRequest(tradition_code="pali")
    assert request.tradition_code == "pali"


def test_save_user_tradition_request_rejects_unknown_codes():
    from pydantic import ValidationError

    from pecha_api.traditions.tradition_response_models import SaveUserTraditionRequest

    with pytest.raises(ValidationError):
        SaveUserTraditionRequest(tradition_code="theravada")


def test_save_user_tradition_request_rejects_arbitrary_strings():
    from pydantic import ValidationError

    from pecha_api.traditions.tradition_response_models import SaveUserTraditionRequest

    with pytest.raises(ValidationError):
        SaveUserTraditionRequest(tradition_code="My Custom Tradition")
