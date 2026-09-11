from unittest.mock import patch, AsyncMock, mock_open
from types import SimpleNamespace
import pytest
import io
from PIL import Image
from fastapi import HTTPException
from starlette.responses import Response

from pecha_api.share.share_service import (
    generate_short_url,
    get_generated_image,
    _generate_short_url_payload_,
    _generate_url_,
    _generate_logo_image_,
    _generate_segment_content_image_,
    _extract_poem_id_from_url_,
    _get_poem_image_bytes_,
    _generate_fallback_logo_image_
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
        
        assert isinstance(response, Response)
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
         patch("pecha_api.share.share_service.get_text_by_id_from_openpecha", new_callable=AsyncMock, return_value=mock_text_detail), \
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
         patch("pecha_api.share.share_service.get_text_by_id_from_openpecha", new_callable=AsyncMock, return_value=mock_text_detail), \
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
    
    with patch("pecha_api.share.share_service.get_text_by_id_from_openpecha", new_callable=AsyncMock, return_value=mock_text_detail), \
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


def test_extract_poem_id_from_url():
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"

    assert _extract_poem_id_from_url_(f"https://webuddhist.com/open/poem/{poem_id}") == poem_id
    assert _extract_poem_id_from_url_("https://webuddhist.com/chapter?text_id=text_1") is None
    assert _extract_poem_id_from_url_(None) is None


def test_generate_short_url_payload_for_poem():
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    share_request = ShareRequest(
        url=f"https://webuddhist.com/open/poem/{poem_id}",
        poem_id=poem_id,
        tags="tag1"
    )

    with patch("pecha_api.share.share_service.get") as mock_get:
        mock_get.return_value = "https://backend.example.com"

        payload = _generate_short_url_payload_(
            share_request, "Test description", poem_title="Song to Sebän Repa"
        )

        assert payload["og_image"] == f"https://backend.example.com/share/image?poem_id={poem_id}"
        assert payload["og_title"] == "Song to Sebän Repa"


@pytest.mark.asyncio
async def test_generate_short_url_for_poem_skips_image_generation():
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    share_request = ShareRequest(url=f"https://webuddhist.com/open/poem/{poem_id}")
    mock_short_url_response = ShortUrlResponse(shortUrl="https://wb.pub/bodi1")

    with patch("pecha_api.share.share_service.get_short_url", new_callable=AsyncMock, return_value=mock_short_url_response), \
         patch("pecha_api.share.share_service._get_poem_title_", return_value="Song to Sebän Repa"), \
         patch("pecha_api.share.share_service._get_poem_image_bytes_", return_value=(b"jpeg_bytes", "image/jpeg")), \
         patch("pecha_api.share.share_service.get", return_value="https://backend.example.com"), \
         patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:

        response = await generate_short_url(share_request=share_request)

        assert response.shortUrl == "https://wb.pub/bodi1"
        # A poem has its own image, so the shared output.png is never overwritten.
        mock_generate_image.assert_not_called()
        # The poem id is recovered from the url even though the app never sends the field.
        assert share_request.poem_id == poem_id


def _text_dto() -> TextDTO:
    return TextDTO(
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


@pytest.mark.asyncio
@pytest.mark.parametrize("poem_image", [None, RuntimeError("s3 down")])
async def test_generate_short_url_keeps_poem_id_when_image_unavailable(poem_image):
    """A poem whose image is unavailable must still resolve through the poem url,
    which serves a neutral image, rather than the shared mutable output.png."""
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    share_request = ShareRequest(
        url=f"https://webuddhist.com/open/poem/{poem_id}",
        text_id="text_1",
        language="en",
    )
    image_patch = (
        {"side_effect": poem_image} if isinstance(poem_image, Exception) else {"return_value": poem_image}
    )

    with patch("pecha_api.share.share_service.get_short_url", new_callable=AsyncMock, return_value=ShortUrlResponse(shortUrl="https://wb.pub/x")) as mock_short_url, \
         patch("pecha_api.share.share_service._get_poem_title_", return_value="A Poem"), \
         patch("pecha_api.share.share_service._get_poem_image_bytes_", **image_patch), \
         patch("pecha_api.share.share_service.get", return_value="https://backend.example.com"), \
         patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:

        await generate_short_url(share_request=share_request)

        assert share_request.poem_id == poem_id
        # output.png is never written, so a concurrent share cannot leak into it.
        mock_generate_image.assert_not_called()
        payload = mock_short_url.call_args.kwargs["payload"]
        assert payload["og_image"] == f"https://backend.example.com/share/image?poem_id={poem_id}"


@pytest.mark.asyncio
async def test_generate_short_url_keeps_poem_url_when_poem_does_not_resolve():
    """An unknown or unpublished poem id must still resolve through the poem url:
    the segment/text url would serve the shared mutable output.png."""
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    share_request = ShareRequest(
        url=f"https://webuddhist.com/open/poem/{poem_id}",
        text_id="text_1",
        language="en",
    )

    with patch("pecha_api.share.share_service.get_short_url", new_callable=AsyncMock, return_value=ShortUrlResponse(shortUrl="https://wb.pub/x")) as mock_short_url, \
         patch("pecha_api.share.share_service._get_poem_title_", return_value=None), \
         patch("pecha_api.share.share_service.get", return_value="https://backend.example.com"), \
         patch("pecha_api.share.share_service.generate_segment_image") as mock_generate_image:

        await generate_short_url(share_request=share_request)

        assert share_request.poem_id == poem_id
        mock_generate_image.assert_not_called()
        payload = mock_short_url.call_args.kwargs["payload"]
        assert payload["og_image"] == f"https://backend.example.com/share/image?poem_id={poem_id}"
        # No poem resolved, so the title stays the site default.
        assert payload["og_title"] == "Pecha"


@pytest.mark.asyncio
async def test_get_generated_image_returns_distinct_image_per_poem():
    """Two different poems must not resolve to the same image."""
    poem_one = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    poem_two = "5c2504e0-4f89-11d3-9a0c-0305e82c3399"

    def fake_image_bytes(poem_id):
        if poem_id == poem_one:
            return (b"poem_one_image", "image/webp")
        return (b"poem_two_image", "image/webp")

    with patch("pecha_api.share.share_service._get_poem_image_bytes_", side_effect=fake_image_bytes):
        response_one = await get_generated_image(poem_id=poem_one)
        response_two = await get_generated_image(poem_id=poem_two)

        assert isinstance(response_one, Response)
        assert response_one.body == b"poem_one_image"
        assert response_two.body == b"poem_two_image"
        assert response_one.media_type == "image/webp"


@pytest.mark.asyncio
async def test_get_generated_image_falls_back_when_poem_has_no_image():
    with patch("pecha_api.share.share_service._get_poem_image_bytes_", return_value=None), \
         patch("anyio.open_file", new_callable=AsyncMock) as mock_open_file:
        mock_file = AsyncMock()
        mock_file.read.return_value = b"fallback_image"
        cm = AsyncMock()
        cm.__aenter__.return_value = mock_file
        mock_open_file.return_value = cm

        response = await get_generated_image(poem_id="3f2504e0-4f89-11d3-9a0c-0305e82c3301")

        assert isinstance(response, Response)
        assert response.media_type == "image/png"


def test_get_poem_image_bytes_with_invalid_uuid():
    assert _get_poem_image_bytes_("not-a-uuid") is None


def _webp_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="WEBP")
    return buffer.getvalue()


def test_get_poem_image_bytes_converts_webp_to_jpeg():
    """Crawlers unfurl webp unreliably, so stored webp is served as jpeg."""
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    mock_poem = SimpleNamespace(image_key="images/poem_images/x/original/pic.webp", title="A Poem")

    with patch("pecha_api.share.share_service.SessionLocal"), \
         patch("pecha_api.share.share_service.get_poem_by_id", return_value=mock_poem), \
         patch("pecha_api.share.share_service.get", return_value="bucket"), \
         patch("pecha_api.share.share_service.download_bytes", return_value=_webp_bytes()):
        image_bytes, media_type = _get_poem_image_bytes_(poem_id)

        assert media_type == "image/jpeg"
        # The bytes are a real jpeg, not webp relabelled.
        assert Image.open(io.BytesIO(image_bytes)).format == "JPEG"


@pytest.mark.parametrize("stored_bytes", [b"", b"not_an_image", _webp_bytes()[:20]])
def test_get_poem_image_bytes_returns_none_for_unusable_webp(stored_bytes):
    """Empty, corrupt or truncated bytes are not an image, so nothing is served."""
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    mock_poem = SimpleNamespace(image_key="images/poem_images/x/original/pic.webp", title="A Poem")

    with patch("pecha_api.share.share_service.SessionLocal"), \
         patch("pecha_api.share.share_service.get_poem_by_id", return_value=mock_poem), \
         patch("pecha_api.share.share_service.get", return_value="bucket"), \
         patch("pecha_api.share.share_service.download_bytes", return_value=stored_bytes):
        assert _get_poem_image_bytes_(poem_id) is None


def test_get_poem_image_bytes_returns_none_when_download_fails():
    """A missing S3 object must fall back to the generated image, not error."""
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    mock_poem = SimpleNamespace(image_key="images/poem_images/x/original/pic.webp", title="A Poem")

    with patch("pecha_api.share.share_service.SessionLocal"), \
         patch("pecha_api.share.share_service.get_poem_by_id", return_value=mock_poem), \
         patch("pecha_api.share.share_service.get", return_value="bucket"), \
         patch("pecha_api.share.share_service.download_bytes", side_effect=HTTPException(status_code=400, detail="Failed to download file from S3.")):
        assert _get_poem_image_bytes_(poem_id) is None


@pytest.mark.parametrize("failure", [
    ConnectionError("endpoint unreachable"),
    TimeoutError("read timed out"),
    RuntimeError("no credentials"),
])
def test_get_poem_image_bytes_returns_none_on_transport_failures(failure):
    """download_bytes only converts ClientError; everything else surfaces raw."""
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    mock_poem = SimpleNamespace(image_key="images/poem_images/x/original/pic.webp", title="A Poem")

    with patch("pecha_api.share.share_service.SessionLocal"), \
         patch("pecha_api.share.share_service.get_poem_by_id", return_value=mock_poem), \
         patch("pecha_api.share.share_service.get", return_value="bucket"), \
         patch("pecha_api.share.share_service.download_bytes", side_effect=failure):
        assert _get_poem_image_bytes_(poem_id) is None


@pytest.mark.asyncio
async def test_get_generated_image_falls_back_when_poem_lookup_raises():
    """A database failure must still yield an image, not a 500."""
    with patch("pecha_api.share.share_service._get_poem_image_bytes_", side_effect=RuntimeError("db down")):
        response = await get_generated_image(poem_id="3f2504e0-4f89-11d3-9a0c-0305e82c3301")

        body = response.body
        assert Image.open(io.BytesIO(body)).format == "PNG"


@pytest.mark.asyncio
async def test_poem_fallback_never_serves_the_shared_output_png():
    """A poem failing at crawl time must not leak the previous share's image."""
    with patch("pecha_api.share.share_service._get_poem_image_bytes_", return_value=None), \
         patch("anyio.open_file", new_callable=AsyncMock) as mock_open_file:
        response = await get_generated_image(poem_id="3f2504e0-4f89-11d3-9a0c-0305e82c3301")

        # The shared, mutable output.png is never read on the poem path.
        mock_open_file.assert_not_called()

        body = response.body
        assert Image.open(io.BytesIO(body)).size == (1200, 630)


def test_generate_fallback_logo_image_without_logo_file():
    with patch("pecha_api.share.share_service.Image.open", side_effect=OSError("missing logo")):
        response = _generate_fallback_logo_image_()

        assert response.media_type == "image/png"


@pytest.mark.asyncio
async def test_get_generated_image_falls_back_when_download_fails():
    with patch("pecha_api.share.share_service._get_poem_image_bytes_", return_value=None):
        response = await get_generated_image(poem_id="3f2504e0-4f89-11d3-9a0c-0305e82c3301")

        body = response.body
        assert Image.open(io.BytesIO(body)).format == "PNG"


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="blue").save(buffer, format="PNG")
    return buffer.getvalue()


def test_get_poem_image_bytes_passes_through_valid_non_webp():
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    mock_poem = SimpleNamespace(image_key="images/poem_images/x/original/pic.png", title="A Poem")
    png = _png_bytes()

    with patch("pecha_api.share.share_service.SessionLocal"), \
         patch("pecha_api.share.share_service.get_poem_by_id", return_value=mock_poem), \
         patch("pecha_api.share.share_service.get", return_value="bucket"), \
         patch("pecha_api.share.share_service.download_bytes", return_value=png):
        image_bytes, media_type = _get_poem_image_bytes_(poem_id)

        assert image_bytes == png
        assert media_type == "image/png"


@pytest.mark.parametrize("suffix", ["pic.png", "pic.jpg", "pic.jpeg"])
@pytest.mark.parametrize("stored_bytes", [b"", b"not_an_image", _png_bytes()[:20]])
def test_get_poem_image_bytes_returns_none_for_unusable_non_webp(suffix, stored_bytes):
    """PNG and JPEG objects are decoded too, not just webp."""
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    mock_poem = SimpleNamespace(image_key=f"images/poem_images/x/original/{suffix}", title="A Poem")

    with patch("pecha_api.share.share_service.SessionLocal"), \
         patch("pecha_api.share.share_service.get_poem_by_id", return_value=mock_poem), \
         patch("pecha_api.share.share_service.get", return_value="bucket"), \
         patch("pecha_api.share.share_service.download_bytes", return_value=stored_bytes):
        assert _get_poem_image_bytes_(poem_id) is None


def test_get_poem_image_bytes_returns_none_when_poem_has_no_image_key():
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    mock_poem = SimpleNamespace(image_key=None, title="A Poem")

    with patch("pecha_api.share.share_service.SessionLocal"), \
         patch("pecha_api.share.share_service.get_poem_by_id", return_value=mock_poem):
        assert _get_poem_image_bytes_(poem_id) is None


def test_generate_short_url_payload_truncates_long_poem_title():
    poem_id = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    share_request = ShareRequest(url=f"https://webuddhist.com/open/poem/{poem_id}", poem_id=poem_id)
    long_title = "A" * 260

    with patch("pecha_api.share.share_service.get", return_value="https://backend.example.com"):
        payload = _generate_short_url_payload_(
            share_request, "Test description", poem_title=long_title
        )

        # The shortener stores og_title in a varchar(200); a longer value errors the share.
        assert len(payload["og_title"]) == 200


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