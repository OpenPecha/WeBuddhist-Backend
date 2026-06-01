from unittest.mock import patch, AsyncMock, mock_open
import pytest
import io
from fastapi import HTTPException
from starlette.responses import StreamingResponse

from pecha_api.share.share_service import (
    generate_short_url,
    get_generated_image,
    _generate_short_url_payload_,
    _generate_url_,
    _generate_logo_image_,
    _generate_segment_content_image_
)
from pecha_api.share.share_response_models import (
    ShortUrlResponse,
    ShareRequest
)
from pecha_api.share.share_enums import TextColor, BgColor
from pecha_api.texts.segments.segments_response_models import (
    V2SegmentResponse,
    V2SegmentTextDetail,
)
from pecha_api.texts.texts_response_models import TextDTO


@pytest.mark.asyncio
async def test_get_generated_image_success():
    mock_image_data = b"fake_image_data"
    
    with patch("anyio.open_file", new_callable=AsyncMock) as mock_open_file:
        mock_file = AsyncMock()
        mock_file.read.return_value = mock_image_data
        cm = AsyncMock()
        cm.__aenter__.return_value = mock_file
        mock_open_file.return_value = cm
        
        response = await get_generated_image()
        
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "image/png"


@pytest.mark.asyncio
async def test_get_generated_image_file_not_found():
    with patch("anyio.open_file", new_callable=AsyncMock, side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            await get_generated_image()


@pytest.mark.asyncio
async def test_generate_short_url_with_logo():
    share_request = ShareRequest(
        logo=True,
        text_id="text_123",
        url="https://pecha.io/share/123",
    )
    mock_short_url_response = ShortUrlResponse(
        shortUrl="https://pecha.io/share/123"
    )
    mock_text_detail = TextDTO(
        id="text_123",
        title="Test Title",
        language="en",
        type="version",
        group_id="group_1",
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="user_1",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.share.share_service.get_short_url", new_callable=AsyncMock) as mock_short_url, \
         patch("pecha_api.share.share_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
         patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:
        
        mock_short_url.return_value = mock_short_url_response
        
        response = await generate_short_url(share_request=share_request)
        
        assert response is not None
        assert isinstance(response, ShortUrlResponse)
        assert response.shortUrl == "https://pecha.io/share/123"
        # Verify logo image generation was called
        assert mock_generate_image.call_count == 2  # Once for logo, once for content


@pytest.mark.asyncio
async def test_generate_short_url_for_segment_content_success():
    share_request = ShareRequest(
        url="https://pecha.io/share/123",
        segment_id="em5HPUEMRke2e0Qs2519J",
        text_id="text_1",
        language="en",
    )
    mock_short_url_response = ShortUrlResponse(
        shortUrl="https://pecha.io/share/123"
    )
    mock_segment_details = V2SegmentResponse(
        segment_id="em5HPUEMRke2e0Qs2519J",
        content="content_1",
        text=V2SegmentTextDetail(
            text_id="text_1",
            title="title_1",
            language="en",
        ),
    )
    
    with patch("pecha_api.share.share_service.get_short_url", new_callable=AsyncMock, return_value=mock_short_url_response), \
         patch("pecha_api.share.share_service.get_openpecha_segment_details_by_id", new_callable=AsyncMock, return_value=mock_segment_details), \
         patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:
        
        response = await generate_short_url(share_request=share_request)
        
        assert response is not None
        assert isinstance(response, ShortUrlResponse)
        assert response.shortUrl == "https://pecha.io/share/123"
        # Verify image generation was called for segment content
        mock_generate_image.assert_called()


@pytest.mark.asyncio
async def test_generate_short_url_without_segment_id():
    share_request = ShareRequest(
        text_id="text_1",
        language="en",
        url="https://pecha.io/share/123"
    )
    mock_short_url_response = ShortUrlResponse(
        shortUrl="https://pecha.io/share/123"
    )
    mock_text_detail = TextDTO(
        id="text_1",
        title="Test Title",
        language="en",
        type="version",
        group_id="group_1",
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="user_1",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.share.share_service.get_short_url", new_callable=AsyncMock, return_value=mock_short_url_response), \
         patch("pecha_api.share.share_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
         patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:
        
        response = await generate_short_url(share_request=share_request)
        
        assert response is not None
        assert isinstance(response, ShortUrlResponse)
        assert response.shortUrl == "https://pecha.io/share/123"
        # Verify image generation was called with default "PECHA" text
        mock_generate_image.assert_called()


def test_generate_logo_image():
    share_request = ShareRequest(
        text_id="text_123",
        text_color=TextColor.BLACK,
        bg_color=BgColor.DEFAULT
    )
    
    with patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:
        _generate_logo_image_(share_request)
        
        mock_generate_image.assert_called_once_with(
            text_color=TextColor.BLACK,
            bg_color=BgColor.DEFAULT,
            logo_path="pecha_api/share/static/img/pecha-logo.png"
        )


@pytest.mark.asyncio
async def test_generate_segment_content_image_with_segment():
    share_request = ShareRequest(
        text_id="text_1",
        segment_id="em5HPUEMRke2e0Qs2519J",
        language="en",
        text_color=TextColor.BLACK,
        bg_color=BgColor.DEFAULT
    )
    mock_segment = V2SegmentResponse(
        segment_id="em5HPUEMRke2e0Qs2519J",
        content="Test segment content",
        text=V2SegmentTextDetail(
            text_id="text_1",
            title="Test Title",
            language="en",
        ),
    )
    
    with patch(
        "pecha_api.share.share_service.get_openpecha_segment_details_by_id",
        new_callable=AsyncMock,
        return_value=mock_segment,
    ) as mock_get_segment, patch(
        "pecha_api.share.share_service.generate_segment_image"
    ) as mock_generate_image:
        await _generate_segment_content_image_(share_request)
        
        mock_get_segment.assert_awaited_once_with(
            segment_id="em5HPUEMRke2e0Qs2519J",
        )
        mock_generate_image.assert_called_once_with(
            text="Test segment content",
            ref_str="Test Title",
            lang="en",
            text_color=TextColor.BLACK,
            bg_color=BgColor.DEFAULT,
            logo_path="pecha_api/share/static/img/pecha-logo.png"
        )


@pytest.mark.asyncio
async def test_generate_segment_content_image_without_segment():
    share_request = ShareRequest(
        text_id="text_1",
        language="en",
        text_color=TextColor.BLACK,
        bg_color=BgColor.DEFAULT
    )
    mock_text_detail = TextDTO(
        id="text_1",
        title="Test Title",
        language="en",
        type="version",
        group_id="group_1",
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="user_1",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.share.share_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
         patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:
        
        await _generate_segment_content_image_(share_request)
        
        mock_generate_image.assert_called_once_with(
            text="Test Title",
            ref_str="Pecha",
            lang="en",
            text_color=TextColor.BLACK,
            bg_color=BgColor.DEFAULT,
            logo_path="pecha_api/share/static/img/pecha-logo.png"
        )


def test_generate_short_url_payload_with_provided_url():
    share_request = ShareRequest(
        url="https://pecha.io/share/123",
        segment_id="seg_123",
        text_id="text_1",
        language="en",
        logo=True,
        tags="tag1,tag2"
    )
    og_description = "Test description"
    
    with patch("pecha_api.share.share_service.get") as mock_get:
        mock_get.return_value = "https://backend.example.com"
        
        payload = _generate_short_url_payload_(share_request, og_description)
        
        assert payload["url"] == "https://pecha.io/share/123"
        assert payload["og_title"] == "Pecha"
        assert payload["og_description"] == "Test description"
        assert payload["og_image"] == "https://backend.example.com/share/image?segment_id=seg_123&language=en&logo=True"
        assert payload["tags"] == "tag1,tag2"


def test_generate_short_url_payload_without_url():
    share_request = ShareRequest(
        segment_id="seg_123",
        content_id="content_456",
        text_id="text_789",
        content_index=1,
        language="en",
        logo=False,
        tags="tag1"
    )
    og_description = "Test description"
    
    with patch("pecha_api.share.share_service.get") as mock_get:
        mock_get.return_value = "https://backend.example.com"
        
        payload = _generate_short_url_payload_(share_request, og_description)
        
        expected_url = "https://webuddhist.com/chapter?segment_id=seg_123&contentId=content_456&text_id=text_789&contentIndex=1"
        assert payload["url"] == expected_url
        assert payload["og_title"] == "Pecha"
        assert payload["og_description"] == "Test description"
        assert payload["og_image"] == "https://backend.example.com/share/image?segment_id=seg_123&language=en&logo=False"
        assert payload["tags"] == "tag1"


def test_generate_short_url_payload_without_segment_id():
    share_request = ShareRequest(
        content_id="content_456",
        text_id="text_789",
        content_index=1,
        language="en",
        logo=False,
        tags="tag1"
    )
    og_description = "Test description"
    
    with patch("pecha_api.share.share_service.get") as mock_get:
        mock_get.return_value = "https://backend.example.com"
        
        payload = _generate_short_url_payload_(share_request, og_description)
        
        expected_url = "https://webuddhist.com/chapter?contentId=content_456&text_id=text_789&contentIndex=1"
        assert payload["url"] == expected_url
        assert payload["og_title"] == "Pecha"
        assert payload["og_description"] == "Test description"
        assert payload["og_image"] == "https://backend.example.com/share/image?text_id=text_789&language=en&logo=False"
        assert payload["tags"] == "tag1"


def test_generate_url_with_segment_id():
    segment_id = "seg_123"
    content_id = "content_456"
    text_id = "text_789"
    content_index = 2
    
    result = _generate_url_(
        content_id=content_id,
        content_index=content_index,
        text_id=text_id,
        segment_id=segment_id
    )
    
    expected_url = "https://webuddhist.com/chapter?segment_id=seg_123&contentId=content_456&text_id=text_789&contentIndex=2"
    assert result == expected_url


def test_generate_url_without_segment_id():
    content_id = "content_456"
    text_id = "text_789"
    content_index = 2
    
    result = _generate_url_(
        content_id=content_id,
        content_index=content_index,
        text_id=text_id
    )
    
    expected_url = "https://webuddhist.com/chapter?contentId=content_456&text_id=text_789&contentIndex=2"
    assert result == expected_url