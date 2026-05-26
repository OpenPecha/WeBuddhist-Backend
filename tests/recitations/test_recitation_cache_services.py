import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from pecha_api.recitations.recication_cache_services import (
    set_recitation_by_text_id_cache,
    get_recitation_by_text_id_cache
)
from pecha_api.recitations.recitations_response_models import (
    RecitationDetailsRequest,
    RecitationDetailsResponse,
    RecitationSegment,
    Segment
)
from pecha_api.cache.cache_enums import CacheType


class TestSetRecitationByTextIdCache:
    """Test cases for set_recitation_by_text_id_cache function."""

    @pytest.mark.asyncio
    async def test_set_recitation_by_text_id_cache_success(self):
        """Test successful setting of recitation cache."""
        text_id = str(uuid4())
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=["bo"],
            transliterations=["wylie"],
            adaptations=[]
        )
        
        recitation_response = RecitationDetailsResponse(
            text_id=uuid4(),
            title="Test Recitation",
            segments=[]
        )
        
        with patch("pecha_api.recitations.recication_cache_services.set_cache", new_callable=AsyncMock) as mock_set_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="test_hash_key") as mock_hash, \
             patch("pecha_api.recitations.recication_cache_services.config.get_int", return_value=1800) as mock_get_int:
            
            await set_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS,
                data=recitation_response
            )
            
            # Verify hash key generation
            mock_hash.assert_called_once()
            call_args = mock_hash.call_args[1]
            assert "payload" in call_args
            payload = call_args["payload"]
            assert payload[0] == text_id
            assert payload[1] == recitation_request
            assert payload[2] == CacheType.RECITATION_DETAILS
            
            # Verify cache timeout config was retrieved
            mock_get_int.assert_called_once_with("CACHE_TEXT_TIMEOUT")
            
            # Verify cache was set with correct parameters
            mock_set_cache.assert_called_once_with(
                hash_key="test_hash_key",
                value=recitation_response,
                cache_time_out=1800
            )

    @pytest.mark.asyncio
    async def test_set_recitation_by_text_id_cache_with_empty_segments(self):
        """Test setting cache with empty segments list."""
        text_id = str(uuid4())
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        recitation_response = RecitationDetailsResponse(
            text_id=uuid4(),
            title="Empty Segments Recitation",
            segments=[]
        )
        
        with patch("pecha_api.recitations.recication_cache_services.set_cache", new_callable=AsyncMock) as mock_set_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="hash_empty") as mock_hash, \
             patch("pecha_api.recitations.recication_cache_services.config.get_int", return_value=1800):
            
            await set_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS,
                data=recitation_response
            )
            
            mock_set_cache.assert_called_once()
            assert mock_set_cache.call_args[1]["value"].segments == []

    @pytest.mark.asyncio
    async def test_set_recitation_by_text_id_cache_with_multiple_segments(self):
        """Test setting cache with multiple segments."""
        text_id = str(uuid4())
        segment_id_1 = uuid4()
        segment_id_2 = uuid4()
        
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en", "bo"],
            translations=["en"],
            transliterations=["wylie"],
            adaptations=["en"]
        )
        
        segments = [
            RecitationSegment(
                recitation={
                    "en": Segment(id=segment_id_1, content="English recitation 1"),
                    "bo": Segment(id=segment_id_1, content="Tibetan recitation 1")
                },
                translations={"en": Segment(id=segment_id_1, content="Translation 1")},
                transliterations={"wylie": Segment(id=segment_id_1, content="Transliteration 1")},
                adaptations={"en": Segment(id=segment_id_1, content="Adaptation 1")}
            ),
            RecitationSegment(
                recitation={
                    "en": Segment(id=segment_id_2, content="English recitation 2"),
                    "bo": Segment(id=segment_id_2, content="Tibetan recitation 2")
                },
                translations={"en": Segment(id=segment_id_2, content="Translation 2")},
                transliterations={"wylie": Segment(id=segment_id_2, content="Transliteration 2")},
                adaptations={"en": Segment(id=segment_id_2, content="Adaptation 2")}
            )
        ]
        
        recitation_response = RecitationDetailsResponse(
            text_id=uuid4(),
            title="Multi-Segment Recitation",
            segments=segments
        )
        
        with patch("pecha_api.recitations.recication_cache_services.set_cache", new_callable=AsyncMock) as mock_set_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="hash_multi") as mock_hash, \
             patch("pecha_api.recitations.recication_cache_services.config.get_int", return_value=1800):
            
            await set_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS,
                data=recitation_response
            )
            
            mock_set_cache.assert_called_once()
            cached_value = mock_set_cache.call_args[1]["value"]
            assert len(cached_value.segments) == 2
            assert cached_value.segments[0].recitation["en"].content == "English recitation 1"
            assert cached_value.segments[1].recitation["bo"].content == "Tibetan recitation 2"

    @pytest.mark.asyncio
    async def test_set_recitation_by_text_id_cache_different_cache_types(self):
        """Test setting cache with different cache types."""
        text_id = str(uuid4())
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        recitation_response = RecitationDetailsResponse(
            text_id=uuid4(),
            title="Test Recitation",
            segments=[]
        )
        
        # Test with RECITATION_DETAILS cache type
        with patch("pecha_api.recitations.recication_cache_services.set_cache", new_callable=AsyncMock) as mock_set_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="hash_1"), \
             patch("pecha_api.recitations.recication_cache_services.config.get_int", return_value=1800):
            
            await set_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS,
                data=recitation_response
            )
            
            mock_set_cache.assert_called_once()


class TestGetRecitationByTextIdCache:
    """Test cases for get_recitation_by_text_id_cache function."""

    @pytest.mark.asyncio
    async def test_get_recitation_by_text_id_cache_empty_cache(self):
        """Test getting recitation from empty cache returns None."""
        text_id = str(uuid4())
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=None) as mock_get_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="test_hash_key"):
            
            result = await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            assert result is None
            mock_get_cache.assert_called_once_with(hash_key="test_hash_key")

    @pytest.mark.asyncio
    async def test_get_recitation_by_text_id_cache_with_dict_response(self):
        """Test getting recitation from cache when it returns a dict."""
        text_id = str(uuid4())
        response_text_id = uuid4()
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=["bo"],
            transliterations=[],
            adaptations=[]
        )
        
        # Mock cache returning a dict (as would happen with JSON deserialization)
        mock_cache_dict = {
            "text_id": str(response_text_id),
            "title": "Cached Recitation",
            "segments": []
        }
        
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_dict) as mock_get_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="test_hash_key"):
            
            result = await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            assert result is not None
            assert isinstance(result, RecitationDetailsResponse)
            assert str(result.text_id) == str(response_text_id)
            assert result.title == "Cached Recitation"
            assert result.segments == []
            mock_get_cache.assert_called_once_with(hash_key="test_hash_key")

    @pytest.mark.asyncio
    async def test_get_recitation_by_text_id_cache_with_pydantic_model(self):
        """Test getting recitation from cache when it returns a Pydantic model."""
        text_id = str(uuid4())
        response_text_id = uuid4()
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        # Mock cache returning a Pydantic model directly
        mock_cache_response = RecitationDetailsResponse(
            text_id=response_text_id,
            title="Direct Model Response",
            segments=[]
        )
        
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_response) as mock_get_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="test_hash_key"):
            
            result = await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            # When cache returns a Pydantic model (not a dict), it should be returned as-is
            assert result == mock_cache_response
            mock_get_cache.assert_called_once_with(hash_key="test_hash_key")

    @pytest.mark.asyncio
    async def test_get_recitation_by_text_id_cache_with_segments_dict(self):
        """Test getting recitation from cache with segments as dict."""
        text_id = str(uuid4())
        response_text_id = uuid4()
        segment_id_1 = uuid4()
        segment_id_2 = uuid4()
        
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en", "bo"],
            translations=["en"],
            transliterations=["wylie"],
            adaptations=[]
        )
        
        # Mock cache returning dict with segments
        mock_cache_dict = {
            "text_id": str(response_text_id),
            "title": "Recitation with Segments",
            "segments": [
                {
                    "recitation": {
                        "en": {"id": str(segment_id_1), "content": "English content 1"},
                        "bo": {"id": str(segment_id_1), "content": "Tibetan content 1"}
                    },
                    "translations": {
                        "en": {"id": str(segment_id_1), "content": "Translation 1"}
                    },
                    "transliterations": {
                        "wylie": {"id": str(segment_id_1), "content": "Transliteration 1"}
                    },
                    "adaptations": {}
                },
                {
                    "recitation": {
                        "en": {"id": str(segment_id_2), "content": "English content 2"}
                    },
                    "translations": {},
                    "transliterations": {},
                    "adaptations": {}
                }
            ]
        }
        
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_dict) as mock_get_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="test_hash_key"):
            
            result = await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            assert result is not None
            assert isinstance(result, RecitationDetailsResponse)
            assert len(result.segments) == 2
            assert result.segments[0].recitation["en"].content == "English content 1"
            assert result.segments[0].recitation["bo"].content == "Tibetan content 1"
            assert result.segments[0].translations["en"].content == "Translation 1"
            assert result.segments[1].recitation["en"].content == "English content 2"

    @pytest.mark.asyncio
    async def test_get_recitation_by_text_id_cache_hash_key_generation(self):
        """Test that hash key is generated correctly with all parameters."""
        text_id = str(uuid4())
        recitation_request = RecitationDetailsRequest(
            language="bo",
            recitation=["bo"],
            translations=["en", "zh"],
            transliterations=["wylie", "pinyin"],
            adaptations=["en"]
        )
        
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=None), \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="complex_hash_key") as mock_hash:
            
            await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            # Verify hash generation was called with correct payload
            mock_hash.assert_called_once()
            call_args = mock_hash.call_args[1]
            assert "payload" in call_args
            payload = call_args["payload"]
            assert len(payload) == 3
            assert payload[0] == text_id
            assert payload[1] == recitation_request
            assert payload[2] == CacheType.RECITATION_DETAILS

    @pytest.mark.asyncio
    async def test_get_recitation_by_text_id_cache_with_none_parameters(self):
        """Test getting recitation from cache with None parameters."""
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=None) as mock_get_cache, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="none_hash_key"):
            
            result = await get_recitation_by_text_id_cache(
                text_id=None,
                recitation_details_request=None,
                cache_type=None
            )
            
            assert result is None
            mock_get_cache.assert_called_once_with(hash_key="none_hash_key")

    @pytest.mark.asyncio
    async def test_get_recitation_by_text_id_cache_complex_segments(self):
        """Test getting recitation with complex nested segment structure."""
        text_id = str(uuid4())
        response_text_id = uuid4()
        
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en", "bo", "zh"],
            translations=["en", "fr", "de"],
            transliterations=["wylie", "pinyin"],
            adaptations=["en", "simple"]
        )
        
        # Create complex segment structure
        segment_id = uuid4()
        mock_cache_dict = {
            "text_id": str(response_text_id),
            "title": "Complex Recitation",
            "segments": [
                {
                    "recitation": {
                        "en": {"id": str(segment_id), "content": "English recitation"},
                        "bo": {"id": str(segment_id), "content": "བོད་ཡིག"},
                        "zh": {"id": str(segment_id), "content": "中文"}
                    },
                    "translations": {
                        "en": {"id": str(segment_id), "content": "English translation"},
                        "fr": {"id": str(segment_id), "content": "Traduction française"},
                        "de": {"id": str(segment_id), "content": "Deutsche Übersetzung"}
                    },
                    "transliterations": {
                        "wylie": {"id": str(segment_id), "content": "bod yig"},
                        "pinyin": {"id": str(segment_id), "content": "zhong wen"}
                    },
                    "adaptations": {
                        "en": {"id": str(segment_id), "content": "Simple English"},
                        "simple": {"id": str(segment_id), "content": "Very simple"}
                    }
                }
            ]
        }
        
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_dict), \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="complex_hash"):
            
            result = await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            assert result is not None
            assert isinstance(result, RecitationDetailsResponse)
            assert len(result.segments) == 1
            
            segment = result.segments[0]
            assert len(segment.recitation) == 3
            assert len(segment.translations) == 3
            assert len(segment.transliterations) == 2
            assert len(segment.adaptations) == 2
            
            assert segment.recitation["bo"].content == "བོད་ཡིག"
            assert segment.translations["fr"].content == "Traduction française"
            assert segment.transliterations["wylie"].content == "bod yig"
            assert segment.adaptations["simple"].content == "Very simple"


class TestRecitationCacheIntegration:
    """Integration tests for set and get cache functions."""

    @pytest.mark.asyncio
    async def test_set_and_get_recitation_cache_roundtrip(self):
        """Test setting and getting cache in sequence."""
        text_id = str(uuid4())
        response_text_id = uuid4()
        segment_id = uuid4()
        
        recitation_request = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=["bo"],
            transliterations=[],
            adaptations=[]
        )
        
        recitation_response = RecitationDetailsResponse(
            text_id=response_text_id,
            title="Integration Test Recitation",
            segments=[
                RecitationSegment(
                    recitation={"en": Segment(id=segment_id, content="Test content")},
                    translations={"bo": Segment(id=segment_id, content="བོད་ཡིག")},
                    transliterations={},
                    adaptations={}
                )
            ]
        )
        
        # Convert to dict as cache would do
        response_dict = {
            "text_id": str(response_text_id),
            "title": "Integration Test Recitation",
            "segments": [
                {
                    "recitation": {"en": {"id": str(segment_id), "content": "Test content"}},
                    "translations": {"bo": {"id": str(segment_id), "content": "བོད་ཡིག"}},
                    "transliterations": {},
                    "adaptations": {}
                }
            ]
        }
        
        with patch("pecha_api.recitations.recication_cache_services.set_cache", new_callable=AsyncMock) as mock_set, \
             patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=response_dict) as mock_get, \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", return_value="integration_hash"), \
             patch("pecha_api.recitations.recication_cache_services.config.get_int", return_value=1800):
            
            # Set cache
            await set_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS,
                data=recitation_response
            )
            
            # Get cache
            result = await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=recitation_request,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            # Verify
            mock_set.assert_called_once()
            mock_get.assert_called_once()
            
            assert result is not None
            assert isinstance(result, RecitationDetailsResponse)
            assert str(result.text_id) == str(response_text_id)
            assert result.title == "Integration Test Recitation"
            assert len(result.segments) == 1
            assert result.segments[0].recitation["en"].content == "Test content"
            assert result.segments[0].translations["bo"].content == "བོད་ཡིག"

    @pytest.mark.asyncio
    async def test_different_requests_generate_different_hashes(self):
        """Test that different requests generate different cache keys."""
        text_id = str(uuid4())
        
        request1 = RecitationDetailsRequest(
            language="en",
            recitation=["en"],
            translations=[],
            transliterations=[],
            adaptations=[]
        )
        
        request2 = RecitationDetailsRequest(
            language="bo",
            recitation=["bo"],
            translations=["en"],
            transliterations=[],
            adaptations=[]
        )
        
        hash_calls = []
        
        def capture_hash(payload):
            hash_calls.append(payload)
            return f"hash_{len(hash_calls)}"
        
        with patch("pecha_api.recitations.recication_cache_services.get_cache_data", new_callable=AsyncMock, return_value=None), \
             patch("pecha_api.recitations.recication_cache_services.Utils.generate_hash_key", side_effect=capture_hash):
            
            # Get cache for first request
            await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=request1,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            # Get cache for second request
            await get_recitation_by_text_id_cache(
                text_id=text_id,
                recitation_details_request=request2,
                cache_type=CacheType.RECITATION_DETAILS
            )
            
            # Verify different payloads were used
            assert len(hash_calls) == 2
            assert hash_calls[0] != hash_calls[1]
            assert hash_calls[0][1] == request1
            assert hash_calls[1][1] == request2

