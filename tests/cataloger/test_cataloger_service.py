import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi import HTTPException
import httpx
from pecha_api.constants import Constants
from pecha_api.cataloger.cataloger_service import (
    get_cataloged_texts,
    get_cataloged_texts_details,
    call_external_pecha_api_texts,
    call_external_pecha_api_instances,
    call_external_pecha_api_related_instances,
    call_external_pecha_api_cataloged_texts,
    ensure_dict
)
from pecha_api.cataloger.cataloger_response_model import (
    CatalogedTextsDetailsResponse,
    ExternalPechaTextResponse,
    ExternalPechaInstanceRelatedResponse,
    Relation,
    Metadata
)

@pytest.fixture
def mock_single_text_data():
    return [
        {
            "id": "text_1",
            "title": {"bo": "བོད་ཡིག", "en": "Tibetan Text"},
            "language": "bo",
            "type": "critical",
        },
    ]

@pytest.fixture
def mock_multiple_texts_data():
    return [
        {
            "id": "text_1",
            "title": {"bo": "བོད་ཡིག", "en": "Tibetan Text"},
            "language": "bo",
            "type": "critical",
        },
        {
            "id": "text_2",
            "title": {"bo": "བོད་ཡིག", "en": "Tibetan Text"},
            "language": "bo",
            "type": "critical",
        },
    ]



@pytest.mark.asyncio
async def test_get_cataloged_texts_details_success():
    """Test successful retrieval of cataloged text details"""
    text_id = "text_123"
    
    mock_text_response = ExternalPechaTextResponse(
        title={"en": "Test Title", "bo": "ཡིག་ཆ།"},
        type="critical",
        category_id="cat_456"
    )
    
    mock_instance_ids = ["instance_1", "instance_2"]
    
    mock_related_instances = [
        ExternalPechaInstanceRelatedResponse(
            title={"en": "Related Text 1"},
            text_id="related_text_1",
            language="en",
            relation_type="translation"
        ),
        ExternalPechaInstanceRelatedResponse(
            title={"en": "Related Text 2"},
            text_id="related_text_2",
            language="bo",
            relation_type="commentary"
        )
    ]
    
    with patch("pecha_api.cataloger.cataloger_service.call_external_pecha_api_texts", new_callable=AsyncMock, return_value=mock_text_response), \
         patch("pecha_api.cataloger.cataloger_service.call_external_pecha_api_instances", new_callable=AsyncMock, return_value=mock_instance_ids), \
         patch("pecha_api.cataloger.cataloger_service.call_external_pecha_api_related_instances", new_callable=AsyncMock, side_effect=[[mock_related_instances[0]], [mock_related_instances[1]]]):
        
        response = await get_cataloged_texts_details(text_id)
        
        assert response is not None
        assert isinstance(response, CatalogedTextsDetailsResponse)
        assert response.title == {"en": "Test Title", "bo": "ཡིག་ཆ།"}
        assert response.category_id == "cat_456"
        assert response.status is False
        assert len(response.relations) == 2
        assert response.relations[0].relation_type == "translation"
        assert response.relations[0].metadata.text_id == "related_text_1"
        assert response.relations[1].relation_type == "commentary"
        assert response.relations[1].metadata.text_id == "related_text_2"

@pytest.mark.asyncio
async def test_call_external_pecha_api_texts_success():
    """Test successful call to external pecha API for texts"""
    text_id = "text_123"
    
    mock_response_data = {
        "title": {"en": "Test Title", "bo": "ཡིག་ཆ།"},
        "type": "critical",
        "category_id": "cat_456"
    }
    
    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await call_external_pecha_api_texts(text_id)
        
        assert response is not None
        assert isinstance(response, ExternalPechaTextResponse)
        assert response.title == {"en": "Test Title", "bo": "ཡིག་ཆ།"}
        assert response.category_id == "cat_456"
        
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert f"/texts/{text_id}" in call_args[0][0]


@pytest.mark.asyncio
async def test_call_external_pecha_api_texts_http_error():
    """Test call to external pecha API for texts with HTTP error"""
    text_id = "text_123"
    
    mock_http_response = Mock()
    mock_http_response.status_code = 404
    mock_http_response.text = "Text not found"
    
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Not found",
        request=Mock(),
        response=mock_http_response
    ))
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_external_pecha_api_texts(text_id)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_call_external_pecha_api_instances_success():
    """Test successful call to external pecha API for instances"""
    text_id = "text_123"
    
    mock_response_data = [
        {"id": "instance_1", "type": "critical"},
        {"id": "instance_2", "type": "critical"},
        {"other_field": "no_id"}
    ]
    
    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await call_external_pecha_api_instances(text_id)
        
        assert response is not None
        assert isinstance(response, list)
        assert len(response) == 2
        assert "instance_1" in response
        assert "instance_2" in response
        
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert f"/texts/{text_id}/instances" in call_args[0][0]
        assert "instance_type=critical" in call_args[0][0]


@pytest.mark.asyncio
async def test_call_external_pecha_api_instances_http_error():
    """Test call to external pecha API for instances with HTTP error"""
    text_id = "text_123"
    
    mock_http_response = Mock()
    mock_http_response.status_code = 404
    mock_http_response.text = "Instances not found"
    
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Not found",
        request=Mock(),
        response=mock_http_response
    ))
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_external_pecha_api_instances(text_id)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_call_external_pecha_api_instances_request_error():
    """Test call to external pecha API for instances with request error"""
    text_id = "text_123"
    
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError(
        "Network error",
        request=Mock()
    ))
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_external_pecha_api_instances(text_id)
        
        assert exc_info.value.status_code == 500
        assert "Failed to connect" in exc_info.value.detail

@pytest.mark.asyncio
async def test_call_external_pecha_api_related_instances_success():
    """Test successful call to external pecha API for related instances"""
    instance_id = "instance_123"
    
    mock_response_data = [
        {
            "metadata": {
                "title": {"en": "Related Text 1"},
                "text_id": "related_text_1",
                "language": "en"
            },
            "relationship": "translation"
        },
        {
            "metadata": {
                "title": {"bo": "འབྲེལ་བ་ཡོད་པའི་ཡིག་ཆ།"},
                "text_id": "related_text_2",
                "language": "bo"
            },
            "relationship": "commentary"
        }
    ]
    
    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await call_external_pecha_api_related_instances(instance_id)
        
        assert response is not None
        assert isinstance(response, list)
        assert len(response) == 2
        assert isinstance(response[0], ExternalPechaInstanceRelatedResponse)
        assert response[0].title == {"en": "Related Text 1"}
        assert response[0].text_id == "related_text_1"
        assert response[0].language == "en"
        assert response[0].relation_type == "translation"
        assert response[1].relation_type == "commentary"
        
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert f"/instances/{instance_id}/related" in call_args[0][0]


@pytest.mark.asyncio
async def test_call_external_pecha_api_related_instances_http_error():
    """Test call to external pecha API for related instances with HTTP error"""
    instance_id = "instance_123"
    
    mock_http_response = Mock()
    mock_http_response.status_code = 500
    mock_http_response.text = "Internal server error"
    
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Server error",
        request=Mock(),
        response=mock_http_response
    ))
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_external_pecha_api_related_instances(instance_id)
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_call_external_pecha_api_related_instances_request_error():
    """Test call to external pecha API for related instances with request error"""
    instance_id = "instance_123"
    
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError(
        "Connection failed",
        request=Mock()
    ))
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_external_pecha_api_related_instances(instance_id)
        
        assert exc_info.value.status_code == 500
        assert "Failed to connect" in exc_info.value.detail


@pytest.mark.asyncio
async def test_call_external_pecha_api_related_instances_empty_metadata():
    """Test call to external pecha API for related instances with empty metadata"""
    instance_id = "instance_123"
    
    mock_response_data = [
        {
            "metadata": {},
            "relationship": "source"
        }
    ]
    
    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await call_external_pecha_api_related_instances(instance_id)
        
        assert response is not None
        assert isinstance(response, list)
        assert len(response) == 1
        assert response[0].title == {}
        assert response[0].text_id == ""
        assert response[0].language == ""
        assert response[0].relation_type == "source"


def test_ensure_dict_with_dict():
    """Test ensure_dict function with a dictionary"""
    test_dict = {"en": "English", "bo": "བོད་ཡིག"}
    result = ensure_dict(test_dict)
    assert result == test_dict



def test_ensure_dict_with_list():
    """Test ensure_dict function with a list"""
    test_list = ["item1", "item2"]
    result = ensure_dict(test_list)
    assert result == {}


def test_ensure_dict_with_number():
    """Test ensure_dict function with a number"""
    result = ensure_dict(123)
    assert result == {}


def test_ensure_dict_with_empty_dict():
    """Test ensure_dict function with empty dictionary"""
    result = ensure_dict({})
    assert result == {}


def test_ensure_dict_with_none():
    """Test ensure_dict function with None"""
    result = ensure_dict(None)
    assert result == {}


def test_ensure_dict_with_string():
    """Test ensure_dict function with string"""
    result = ensure_dict("some string")
    assert result == {}

@pytest.mark.asyncio
async def test_get_cataloged_texts_details_with_none_text_id():
    """Test get cataloged texts details with None text_id"""
    response = await get_cataloged_texts_details(None)
    assert response is None


@pytest.mark.asyncio
async def test_get_cataloged_texts_details_with_empty_instances():
    """Test get cataloged texts details when no instances are returned"""
    text_id = "text_123"
    
    mock_text_response = ExternalPechaTextResponse(
        title={"en": "Test Title"},
        type="critical",
        category_id="cat_456"
    )
    
    mock_instance_ids = []
    
    with patch("pecha_api.cataloger.cataloger_service.call_external_pecha_api_texts", new_callable=AsyncMock, return_value=mock_text_response), \
         patch("pecha_api.cataloger.cataloger_service.call_external_pecha_api_instances", new_callable=AsyncMock, return_value=mock_instance_ids):
        
        response = await get_cataloged_texts_details(text_id)
        
        assert response is not None
        assert isinstance(response, CatalogedTextsDetailsResponse)
        assert response.title == {"en": "Test Title"}
        assert response.category_id == "cat_456"
        assert response.status is False
        assert len(response.relations) == 0


@pytest.mark.asyncio
async def test_get_cataloged_texts_details_integration():
    """Integration test for get cataloged texts details with all components"""
    text_id = "integration_test_123"
    
    mock_text_data = {
        "title": {"en": "Integration Test Text", "bo": "འབྲེལ་མཐུད་བརྟག་དཔྱད།"},
        "type": "critical",
        "category_id": "integration_cat"
    }
    
    mock_instances_data = [
        {"id": "int_instance_1"},
        {"id": "int_instance_2"}
    ]
    
    mock_related_data_1 = [
        {
            "metadata": {
                "title": {"en": "Related Integration 1"},
                "text_id": "rel_int_1",
                "language": "en"
            },
            "relationship": "source"
        }
    ]
    
    mock_related_data_2 = [
        {
            "metadata": {
                "title": {"bo": "འབྲེལ་བ་གཉིས།"},
                "text_id": "rel_int_2",
                "language": "bo"
            },
            "relationship": "derivative"
        }
    ]
    
    mock_http_response_text = Mock()
    mock_http_response_text.status_code = 200
    mock_http_response_text.json.return_value = mock_text_data
    mock_http_response_text.raise_for_status = Mock()
    
    mock_http_response_instances = Mock()
    mock_http_response_instances.status_code = 200
    mock_http_response_instances.json.return_value = mock_instances_data
    mock_http_response_instances.raise_for_status = Mock()
    
    mock_http_response_related_1 = Mock()
    mock_http_response_related_1.status_code = 200
    mock_http_response_related_1.json.return_value = mock_related_data_1
    mock_http_response_related_1.raise_for_status = Mock()
    
    mock_http_response_related_2 = Mock()
    mock_http_response_related_2.status_code = 200
    mock_http_response_related_2.json.return_value = mock_related_data_2
    mock_http_response_related_2.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=[
        mock_http_response_text,
        mock_http_response_instances,
        mock_http_response_related_1,
        mock_http_response_related_2
    ])
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await get_cataloged_texts_details(text_id)
        
        assert response is not None
        assert response.title == {"en": "Integration Test Text", "bo": "འབྲེལ་མཐུད་བརྟག་དཔྱད།"}
        assert response.category_id == "integration_cat"
        assert response.status is False
        assert len(response.relations) == 2
        assert response.relations[0].relation_type == "source"
        assert response.relations[0].metadata.text_id == "rel_int_1"
        assert response.relations[0].metadata.language == "en"
        assert response.relations[1].relation_type == "derivative"
        assert response.relations[1].metadata.text_id == "rel_int_2"
        assert response.relations[1].metadata.language == "bo"
        
        assert mock_client.get.call_count == 4

@pytest.mark.asyncio
async def test_get_cataloged_texts_request_error():
    """Test get cataloged texts with request error"""
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed", request=Mock()))

    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await get_cataloged_texts(search=None, skip=0, limit=10)

        assert exc_info.value.status_code == 500
        assert "Failed to connect" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_cataloged_texts_http_error():
    """Test get cataloged texts with HTTP error"""
    mock_http_response = Mock()
    mock_http_response.status_code = 500
    mock_http_response.text = "Internal Server Error"

    mock_client = Mock()
    mock_client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_http_response
        )
    )

    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await get_cataloged_texts(search=None, skip=0, limit=10)

        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_cataloged_texts_with_search(mock_single_text_data):
    """Test get cataloged texts with search parameter"""
    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_single_text_data
    mock_http_response.raise_for_status = Mock()
    mock_http_response.status_code = 200

    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)

    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await get_cataloged_texts(search="Tibetan", skip=0, limit=10)

        assert len(response.texts) == 1
        assert response.texts[0].text_id == "text_1"


@pytest.mark.asyncio
async def test_get_cataloged_texts_with_non_dict_title():
    """Test get cataloged texts with non-dict title (ensure_dict handling)"""
    mock_data = [
        {
            "id": "text_1",
            "title": "String title instead of dict",
            "language": "bo",
            "type": "critical",
        },
        {
            "id": "text_2",
            "title": None,
            "language": "en",
            "type": "critical",
        }
    ]
    
    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_data
    mock_http_response.raise_for_status = Mock()
    mock_http_response.status_code = 200

    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)

    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await get_cataloged_texts(search=None, skip=0, limit=10)

        assert len(response.texts) == 2
        assert response.texts[0].text_id == "text_1"
        assert response.texts[0].title == {}
        assert response.texts[1].text_id == "text_2"
        assert response.texts[1].title == {}


@pytest.mark.asyncio
async def test_get_cataloged_texts_with_empty_response():
    """Test get cataloged texts with empty response from API"""
    mock_http_response = Mock()
    mock_http_response.json.return_value = []
    mock_http_response.raise_for_status = Mock()
    mock_http_response.status_code = 200

    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)

    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await get_cataloged_texts(search=None, skip=0, limit=10)

        assert len(response.texts) == 0


@pytest.mark.asyncio
async def test_get_cataloged_texts_with_none_response():
    """Test get cataloged texts with None response from API"""
    mock_http_response = Mock()
    mock_http_response.json.return_value = None
    mock_http_response.raise_for_status = Mock()
    mock_http_response.status_code = 200

    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)

    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await get_cataloged_texts(search=None, skip=0, limit=10)

        assert len(response.texts) == 0


@pytest.mark.asyncio
async def test_get_cataloged_texts_success(mock_multiple_texts_data):
    """Test successful retrieval of cataloged texts"""
    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_multiple_texts_data
    mock_http_response.raise_for_status = Mock()
    mock_http_response.status_code = 200

    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)

    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await get_cataloged_texts(search=None, skip=0, limit=10)

        assert len(response.texts) == 2
        assert response.texts[0].text_id == "text_1"
        assert response.texts[0].status is False


@pytest.mark.asyncio
async def test_call_external_pecha_api_cataloged_texts_success():
    """Test successful call to external pecha API for cataloged texts"""
    search = "Tibetan"
    skip = 0
    limit = 10
    
    mock_response_data = [
        {
            "id": "text_1",
            "title": {"bo": "བོད་ཡིག", "en": "Tibetan Text 1"},
            "language": "bo",
            "type": "critical",
        },
        {
            "id": "text_2",
            "title": {"bo": "བོད་ཡིག", "en": "Tibetan Text 2"},
            "language": "en",
            "type": "critical",
        }
    ]
    
    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await call_external_pecha_api_cataloged_texts(search=search, skip=skip, limit=limit)
        
        assert response is not None
        assert isinstance(response, list)
        assert len(response) == 2
        assert response[0]["id"] == "text_1"
        assert response[1]["id"] == "text_2"
        
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "offset=0" in str(call_args) or call_args.kwargs.get("params", {}).get("offset") == 0
        assert "limit=10" in str(call_args) or call_args.kwargs.get("params", {}).get("limit") == 10
        assert "title=Tibetan" in str(call_args) or call_args.kwargs.get("params", {}).get("title") == "Tibetan"


@pytest.mark.asyncio
async def test_call_external_pecha_api_cataloged_texts_without_search():
    """Test call to external pecha API for cataloged texts without search parameter"""
    skip = 5
    limit = 20
    
    mock_response_data = [
        {
            "id": "text_3",
            "title": {"en": "Test Text"},
            "language": "en",
            "type": "critical",
        }
    ]
    
    mock_http_response = Mock()
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        response = await call_external_pecha_api_cataloged_texts(search=None, skip=skip, limit=limit)
        
        assert response is not None
        assert isinstance(response, list)
        assert len(response) == 1
        
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        params = call_args.kwargs.get("params", {})
        assert params.get("offset") == 5
        assert params.get("limit") == 20
        assert "title" not in params


@pytest.mark.asyncio
async def test_call_external_pecha_api_cataloged_texts_http_error():
    """Test call to external pecha API for cataloged texts with HTTP error"""
    mock_http_response = Mock()
    mock_http_response.status_code = 503
    mock_http_response.text = "Service unavailable"
    
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Service unavailable",
        request=Mock(),
        response=mock_http_response
    ))
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_external_pecha_api_cataloged_texts(search=None, skip=0, limit=10)
        
        assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_call_external_pecha_api_cataloged_texts_request_error():
    """Test call to external pecha API for cataloged texts with request error"""
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError(
        "Connection timeout",
        request=Mock()
    ))
    
    with patch("pecha_api.cataloger.cataloger_service.client", mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_external_pecha_api_cataloged_texts(search=None, skip=0, limit=10)
        
        assert exc_info.value.status_code == 500
        assert "Failed to connect" in exc_info.value.detail
