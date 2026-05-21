from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient, ASGITransport

from pecha_api.app import api
from pecha_api.texts.text_openpecha_response_models import (
    TextDetailResponse,
    CriticalEditionModel,
    ContributionModel,
    SegmentContentResponse,
    SegmentContentModel,
)

TEXT_ID = "OP0001"

SEGMENT_CONTENT = SegmentContentResponse(
    contents=[
        SegmentContentModel(id="seg-1", content="First segment content.", segment_number=1),
        SegmentContentModel(id="seg-2", content="Second segment content.", segment_number=2),
    ],
    has_more=False,
    offset=0,
    limit=30,
)

TEXT_DETAIL_RESPONSE = TextDetailResponse(
    id=TEXT_ID,
    title={"en": "Test Text"},
    language="en",
    category_id="cat-1",
    license="CC0",
    contributions=[ContributionModel(role="author", person_name={"en": "Author Name"})],
    commentaries=[],
    translations=[],
    edition_details=[
        CriticalEditionModel(id="ed-1", type="critical")
    ],
    segments=SEGMENT_CONTENT,
)


@pytest.mark.asyncio
async def test_get_text_detail_success(mocker):
    """Test GET /v2/texts/detail returns full text detail with segments"""
    mock_service = mocker.patch(
        "pecha_api.texts.texts_openpecha_views.get_text_detail_by_id",
        new_callable=AsyncMock,
        return_value=TEXT_DETAIL_RESPONSE,
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(f"/v2/texts/detail?text_id={TEXT_ID}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == TEXT_ID
    assert data["title"] == {"en": "Test Text"}
    assert data["language"] == "en"
    assert len(data["edition_details"]) == 1
    assert data["edition_details"][0]["id"] == "ed-1"
    mock_service.assert_called_once_with(text_id=TEXT_ID, offset=0, limit=30)


@pytest.mark.asyncio
async def test_get_text_detail_with_pagination(mocker):
    """Test GET /v2/texts/detail forwards offset and limit query params to service"""
    paginated_segments = SegmentContentResponse(
        contents=[
            SegmentContentModel(id="seg-3", content="Third segment.", segment_number=3),
        ],
        has_more=True,
        offset=10,
        limit=5,
    )
    mock_service = mocker.patch(
        "pecha_api.texts.texts_openpecha_views.get_text_detail_by_id",
        new_callable=AsyncMock,
        return_value=TEXT_DETAIL_RESPONSE.model_copy(update={"segments": paginated_segments}),
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(f"/v2/texts/detail?text_id={TEXT_ID}&offset=10&limit=5")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["segments"]["offset"] == 10
    assert data["segments"]["limit"] == 5
    assert data["segments"]["has_more"] is True
    mock_service.assert_called_once_with(text_id=TEXT_ID, offset=10, limit=5)


@pytest.mark.asyncio
async def test_get_text_detail_segments_content(mocker):
    """Test GET /v2/texts/detail returns correct segment shape"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_views.get_text_detail_by_id",
        new_callable=AsyncMock,
        return_value=TEXT_DETAIL_RESPONSE,
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(f"/v2/texts/detail?text_id={TEXT_ID}")

    assert response.status_code == status.HTTP_200_OK
    segments = response.json()["segments"]["contents"]
    assert len(segments) == 2
    assert segments[0]["id"] == "seg-1"
    assert segments[0]["content"] == "First segment content."
    assert segments[0]["segment_number"] == 1


@pytest.mark.asyncio
async def test_get_text_detail_not_found(mocker):
    """Test GET /v2/texts/detail returns 404 when no critical editions exist"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_views.get_text_detail_by_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No critical editions found for text with id 'UNKNOWN'",
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get("/v2/texts/detail?text_id=UNKNOWN")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "UNKNOWN" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_text_detail_missing_text_id():
    """Test GET /v2/texts/detail returns 422 when text_id query param is missing"""
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get("/v2/texts/detail")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_text_detail_default_offset_and_limit(mocker):
    """Test GET /v2/texts/detail uses offset=0 and limit=30 by default"""
    mock_service = mocker.patch(
        "pecha_api.texts.texts_openpecha_views.get_text_detail_by_id",
        new_callable=AsyncMock,
        return_value=TEXT_DETAIL_RESPONSE,
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        await ac.get(f"/v2/texts/detail?text_id={TEXT_ID}")

    mock_service.assert_called_once_with(text_id=TEXT_ID, offset=0, limit=30)


@pytest.mark.asyncio
async def test_get_text_detail_internal_server_error(mocker):
    """Test GET /v2/texts/detail propagates 500 from service"""
    mocker.patch(
        "pecha_api.texts.texts_openpecha_views.get_text_detail_by_id",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ),
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(f"/v2/texts/detail?text_id={TEXT_ID}")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal server error"
