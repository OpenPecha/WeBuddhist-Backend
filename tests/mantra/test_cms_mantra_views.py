import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.mantra.mantra_response_models import MantraDTO, MantraMetadataDTO
from pecha_api.plans.plans_enums import LanguageCode

client = TestClient(api)


def _sample_mantra_dto() -> MantraDTO:
    return MantraDTO(
        id=uuid.uuid4(),
        audio_url="mantras/medicine-buddha.mp3",
        metadata=[
            MantraMetadataDTO(
                id=uuid.uuid4(),
                mantra="Tayatha om bekandze bekandze maha bekandze radza samudgate soha",
                title="Medicine Buddha Mantra",
                pronunciation="tayatha om bekandze...",
                language=LanguageCode.EN,
            )
        ],
    )


def test_create_mantra_success():
    payload = {
        "audio_url": "mantras/medicine-buddha.mp3",
        "metadata": [
            {
                "language": "EN",
                "title": "Medicine Buddha Mantra",
                "pronunciation": "tayatha om bekandze...",
                "mantra": "Tayatha om bekandze bekandze maha bekandze radza samudgate soha",
            },
            {
                "language": "BO",
                "title": "སྨན་བླའི་སྔགས།",
                "mantra": "ཨོཾ་བེ་ཀཱནྜེ་བེ་ཀཱནྜེ་མ་ཧཱ་བེ་ཀཱནྜེ་རཱ་ཇ་ས་མུདྒ་ཏེ་སྭཱ་ཧཱ།",
            },
        ],
    }
    sample_dto = _sample_mantra_dto()

    with patch(
        "pecha_api.mantra.mantra_views.create_mantra_service",
        return_value=sample_dto,
    ) as mock_create:
        response = client.post(
            "/api/v1/cms/mantras",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == 201
    assert response.json()["audio_url"] == sample_dto.audio_url
    mock_create.assert_called_once()


def test_create_mantra_requires_auth():
    response = client.post(
        "/api/v1/cms/mantras",
        json={
            "metadata": [
                {
                    "language": "EN",
                    "mantra": "Om mani padme hum",
                }
            ]
        },
    )

    assert response.status_code == 403


def test_create_mantra_rejects_empty_metadata():
    response = client.post(
        "/api/v1/cms/mantras",
        json={"metadata": []},
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 422


def test_create_mantra_rejects_duplicate_languages():
    response = client.post(
        "/api/v1/cms/mantras",
        json={
            "metadata": [
                {"language": "EN", "mantra": "First"},
                {"language": "EN", "mantra": "Second"},
            ]
        },
        headers={"Authorization": "Bearer dummy"},
    )

    assert response.status_code == 422
