import uuid
import pytest
from unittest.mock import patch, AsyncMock
from uuid import UUID, uuid4

from pecha_api.recitations.recitations_view import get_list_of_recitations, get_recitation_details
from pecha_api.recitations.recitations_response_models import (
    RecitationDTO,
    RecitationsResponse,
    RecitationDetailsRequest,
    RecitationDetailsResponse,
    Segment,
    RecitationSegment,
)


@pytest.mark.asyncio
async def test_get_list_of_recitations_success():
    """Test successful retrieval of recitations list."""
    expected = RecitationsResponse(
        recitations=[
            RecitationDTO(title="First Recitation", text_id=uuid.uuid4()),
            RecitationDTO(title="Second Recitation", text_id=uuid.uuid4())
        ]
    )

    with patch(
        "pecha_api.recitations.recitations_view.get_list_of_recitations_service",
        return_value=expected,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_list_of_recitations(search=None, language="en")

        mock_service.assert_awaited_once_with(search=None, language="en")
        assert resp == expected
        assert len(resp.recitations) == 2
        assert resp.recitations[0].title == "First Recitation"
        assert resp.recitations[1].title == "Second Recitation"


@pytest.mark.asyncio
async def test_get_list_of_recitations_single_recitation():
    """Test get_list_of_recitations with single recitation."""
    text_id = uuid.uuid4()
    expected = RecitationsResponse(
        recitations=[
            RecitationDTO(title="Single Recitation", text_id=text_id)
        ]
    )

    with patch(
        "pecha_api.recitations.recitations_view.get_list_of_recitations_service",
        return_value=expected,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_list_of_recitations(search=None, language="bo")

        mock_service.assert_awaited_once_with(search=None, language="bo")
        assert resp == expected
        assert len(resp.recitations) == 1
        assert resp.recitations[0].title == "Single Recitation"
        assert resp.recitations[0].text_id == text_id


@pytest.mark.asyncio
async def test_get_list_of_recitations_with_search():
    """Test get_list_of_recitations with search parameter."""
    text_id = uuid.uuid4()
    expected = RecitationsResponse(
        recitations=[
            RecitationDTO(title="Prayer Recitation", text_id=text_id)
        ]
    )

    with patch(
        "pecha_api.recitations.recitations_view.get_list_of_recitations_service",
        return_value=expected,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_list_of_recitations(search="prayer", language="en")

        mock_service.assert_awaited_once_with(search="prayer", language="en")
        assert resp == expected
        assert len(resp.recitations) == 1
        assert resp.recitations[0].title == "Prayer Recitation"


@pytest.mark.asyncio
async def test_get_recitation_details_success():
    """Test successful retrieval of recitation details."""
    text_id = str(uuid.uuid4())
    request = RecitationDetailsRequest(
        language="en",
        recitation=["en"],
        translations=["en"],
        transliterations=["bo"],
        adaptations=["en"]
    )
    
    expected_response = RecitationDetailsResponse(
        text_id=UUID(text_id),
        title="Test Recitation",
        segments=[
            RecitationSegment(
                recitation={"en": Segment(id=uuid.uuid4(), content="Test content")},
                translations={},
                transliterations={},
                adaptations={}
            )
        ]
    )
    
    with patch(
        "pecha_api.recitations.recitations_view.get_recitation_details_service",
        return_value=expected_response,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_recitation_details(text_id=text_id, recitation_details_request=request)
        
        mock_service.assert_awaited_once_with(text_id=text_id, recitation_details_request=request)
        assert resp == expected_response
        assert resp.text_id == UUID(text_id)
        assert resp.title == "Test Recitation"
        assert len(resp.segments) == 1


@pytest.mark.asyncio
async def test_get_recitation_details_with_multiple_segments():
    """Test get_recitation_details with multiple segments."""
    text_id = str(uuid.uuid4())
    request = RecitationDetailsRequest(
        language="en",
        recitation=["en"],
        translations=[],
        transliterations=[],
        adaptations=[]
    )
    
    expected_response = RecitationDetailsResponse(
        text_id=UUID(text_id),
        title="Multi Segment Recitation",
        segments=[
            RecitationSegment(
                recitation={"en": Segment(id=uuid.uuid4(), content="Segment 1")},
                translations={},
                transliterations={},
                adaptations={}
            ),
            RecitationSegment(
                recitation={"en": Segment(id=uuid.uuid4(), content="Segment 2")},
                translations={},
                transliterations={},
                adaptations={}
            )
        ]
    )
    
    with patch(
        "pecha_api.recitations.recitations_view.get_recitation_details_service",
        return_value=expected_response,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_recitation_details(text_id=text_id, recitation_details_request=request)
        
        mock_service.assert_awaited_once_with(text_id=text_id, recitation_details_request=request)
        assert resp == expected_response
        assert len(resp.segments) == 2


@pytest.mark.asyncio
async def test_get_recitation_details_with_all_types():
    """Test get_recitation_details with recitation, translations, transliterations, and adaptations."""
    text_id = str(uuid.uuid4())
    request = RecitationDetailsRequest(
        language="en",
        recitation=["en"],
        translations=["bo", "en"],
        transliterations=["bo"],
        adaptations=["en"]
    )
    
    expected_response = RecitationDetailsResponse(
        text_id=UUID(text_id),
        title="Complete Recitation",
        segments=[
            RecitationSegment(
                recitation={"en": Segment(id=uuid.uuid4(), content="Recitation content")},
                translations={
                    "bo": Segment(id=uuid.uuid4(), content="Tibetan translation"),
                    "en": Segment(id=uuid.uuid4(), content="English translation")
                },
                transliterations={"bo": Segment(id=uuid.uuid4(), content="Transliteration")},
                adaptations={"en": Segment(id=uuid.uuid4(), content="Adaptation")}
            )
        ]
    )
    
    with patch(
        "pecha_api.recitations.recitations_view.get_recitation_details_service",
        return_value=expected_response,
        new_callable=AsyncMock,
    ) as mock_service:
        resp = await get_recitation_details(text_id=text_id, recitation_details_request=request)
        
        mock_service.assert_awaited_once_with(text_id=text_id, recitation_details_request=request)
        assert resp == expected_response
        assert len(resp.segments[0].recitation) == 1
        assert len(resp.segments[0].translations) == 2
        assert len(resp.segments[0].transliterations) == 1
        assert len(resp.segments[0].adaptations) == 1
