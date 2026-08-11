from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.traditions.tradition_onboarding import get_tradition_onboarding_chrome
from pecha_api.traditions.tradition_repository import resolve_tradition_metadata
from pecha_api.traditions.tradition_response_models import SaveUserTraditionRequest
from pecha_api.traditions.tradition_service import (
    get_tradition_onboarding_service,
    list_traditions_service,
)


def test_get_tradition_onboarding_chrome_supports_language_codes():
    content = get_tradition_onboarding_chrome(language="zh")
    assert content["title"] == "您如何追随佛陀的教导？"


def test_get_tradition_onboarding_chrome_falls_back_to_english():
    content = get_tradition_onboarding_chrome(language="fr")
    assert content["title"] == "How do you follow the Buddha?"


def test_save_user_tradition_request_accepts_path_codes():
    request = SaveUserTraditionRequest(tradition_code="pali")
    assert request.tradition_code == "pali"


def test_save_user_tradition_request_rejects_invalid_codes():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SaveUserTraditionRequest(tradition_code="Invalid Code!")


def test_resolve_tradition_metadata_falls_back_to_english():
    tradition = SimpleNamespace(
        metadata_entries=[
            SimpleNamespace(language=LanguageCode.EN, name="Pāli scriptures", description="EN desc"),
            SimpleNamespace(language=LanguageCode.HI, name="पालि ग्रंथ", description="HI desc"),
        ]
    )

    hindi = resolve_tradition_metadata(tradition, language="hi")
    french_fallback = resolve_tradition_metadata(tradition, language="fr")

    assert hindi.name == "पालि ग्रंथ"
    assert french_fallback.name == "Pāli scriptures"


@pytest.mark.asyncio
async def test_list_traditions_service_uses_localized_metadata():
    traditions = [
        SimpleNamespace(
            code="pali",
            regions=["Sri Lanka"],
            metadata_entries=[
                SimpleNamespace(language=LanguageCode.EN, name="Pāli scriptures"),
                SimpleNamespace(language=LanguageCode.HI, name="पालि ग्रंथ"),
            ],
        )
    ]
    session_cm = MagicMock()
    session_cm.__enter__.return_value = MagicMock()
    session_cm.__exit__.return_value = False

    with patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.traditions.tradition_service.list_traditions",
        return_value=traditions,
    ):
        response = await list_traditions_service(language="hi")

    assert len(response.traditions) == 1
    assert response.traditions[0].code == "pali"
    assert response.traditions[0].name == "पालि ग्रंथ"
    assert response.traditions[0].regions == ["Sri Lanka"]


@pytest.mark.asyncio
async def test_get_tradition_onboarding_service_builds_paths_from_db():
    by_code = {
        "pali": SimpleNamespace(
            code="pali",
            metadata_entries=[
                SimpleNamespace(
                    language=LanguageCode.EN,
                    name="Pāli scriptures",
                    description="Followed across Sri Lanka...",
                ),
            ],
        ),
        "chinese": SimpleNamespace(
            code="chinese",
            metadata_entries=[
                SimpleNamespace(
                    language=LanguageCode.EN,
                    name="Chinese scriptures",
                    description="Followed across China...",
                ),
            ],
        ),
        "tibetan": SimpleNamespace(
            code="tibetan",
            metadata_entries=[
                SimpleNamespace(
                    language=LanguageCode.EN,
                    name="Sanskrit & Tibetan scriptures",
                    description="Followed across the Tibetan plateau...",
                ),
            ],
        ),
    }
    session_cm = MagicMock()
    session_cm.__enter__.return_value = MagicMock()
    session_cm.__exit__.return_value = False

    with patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.traditions.tradition_service.get_tradition_by_code",
        side_effect=lambda db, tradition_code: by_code[tradition_code],
    ):
        response = await get_tradition_onboarding_service()

    assert response.title == "How do you follow the Buddha?"
    assert response.paths.pali.title == "Pāli scriptures"
    assert response.paths.chinese.title == "Chinese scriptures"
    assert response.paths.tibetan.title == "Sanskrit & Tibetan scriptures"
