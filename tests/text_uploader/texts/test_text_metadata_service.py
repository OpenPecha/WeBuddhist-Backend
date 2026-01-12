import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from pecha_api.text_uploader.text_metadata.text_metadata_service import TextMetadataService
from pecha_api.text_uploader.text_metadata.text_metadata_model import (
    CriticalInstance,
    CriticalInstanceResponse,
    TextInstanceIds
)
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest


@pytest.mark.asyncio
async def test_create_textmetada_payload_version_sets_group_and_category_from_collection():
    service = TextMetadataService()
    service.version_group_id = "group_v1"

    text_metadata = {
        "language": "en",
        "title": {"en": "A Title"},
        "category_id": "pecha_cat_1",
        "isPublished": True,
        "views": 12,
        "ranking": 3,
        "license": "CC0",
    }

    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="t1"
    )

    with patch.object(
        service,
        "get_text_critical_instance",
        new_callable=AsyncMock,
        return_value=CriticalInstanceResponse(
            critical_instances=[
                CriticalInstance(
                    id="inst_1",
                    type="critical",
                    source="https://source.example",
                )
            ]
        ),
    ), patch.object(
        service,
        "get_wb_collection_id",
        new_callable=AsyncMock,
        return_value="wb_cat_1"
    ):
        payload = await service.create_textmetada_payload(
            text_id="t1",
            text_metadata=text_metadata,
            type="version",
            text_upload_request=text_upload_request
        )

    assert payload.pecha_text_id == "inst_1"
    assert payload.title == "A Title"
    assert payload.language == "en"
    assert payload.group_id == "group_v1"
    assert payload.categories == ["wb_cat_1"]
    assert payload.type == "version"
    assert payload.source_link == "https://source.example"


@pytest.mark.asyncio
async def test_create_textmetada_payload_commentary_sets_group_and_category_from_version_group():
    service = TextMetadataService()
    service.version_group_id = "group_v1"
    service.commentary_group_id = "group_c1"

    text_metadata = {
        "language": "bo",
        "title": {"bo": "མཚན་བྱང་"},
    }

    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="t_commentary"
    )

    with patch.object(
        service,
        "get_text_critical_instance",
        new_callable=AsyncMock,
        return_value=CriticalInstanceResponse(
            critical_instances=[
                CriticalInstance(
                    id="inst_c1",
                    type="critical",
                    source="s",
                )
            ]
        ),
    ):
        payload = await service.create_textmetada_payload(
            text_id="t_commentary",
            text_metadata=text_metadata,
            type="commentary",
            text_upload_request=text_upload_request
        )

    assert payload.group_id == "group_c1"
    assert payload.categories == ["group_v1"]
    assert payload.type == "commentary"


@pytest.mark.asyncio
async def test_get_uploaded_texts_returns_uploaded_text_ids_and_instances_mapping():
    service = TextMetadataService()

    async def _get_critical_instance_side_effect(text_id: str, openpecha_api_url: str):
        instance_id = {"t1": "inst_1", "t2": "inst_2"}[text_id]
        return CriticalInstanceResponse(
            critical_instances=[
                CriticalInstance(
                    id=instance_id,
                    type="critical",
                    source="src",
                )
            ]
        )

    # Only inst_2 is already uploaded in the destination DB
    uploaded_text_row = {"pecha_text_id": "inst_2", "group_id": "g"}

    with patch.object(
        service,
        "get_text_critical_instance",
        new_callable=AsyncMock,
        side_effect=_get_critical_instance_side_effect,
    ), patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_texts_by_pecha_text_ids",
        new_callable=AsyncMock,
        return_value=[uploaded_text_row],
    ):
        texts, uploaded_text_ids, instances = await service.get_uploaded_texts(
            text_ids=["t1", "t2"],
            openpecha_api_url="https://openpecha.example",
            destination_url="https://destination.example"
        )

    assert texts == [uploaded_text_row]
    assert uploaded_text_ids == ["t2"]
    assert instances == {"t1": "inst_1", "t2": "inst_2"}


@pytest.mark.asyncio
async def test_get_wb_collection_id_raises_when_collection_missing():
    service = TextMetadataService()
    with patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        with pytest.raises(
            ValueError, match="Collection with pecha_collection_id pecha_missing not found"
        ):
            await service.get_wb_collection_id(
                pecha_collection_id="pecha_missing",
                destination_url="https://destination.example"
            )


@pytest.mark.asyncio
async def test_get_wb_collection_id_returns_collection_id():
    """Test get_wb_collection_id returns the collection ID when found"""
    service = TextMetadataService()
    
    with patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_collection_by_pecha_collection_id",
        new_callable=AsyncMock,
        return_value="wb_collection_123"
    ):
        result = await service.get_wb_collection_id(
            pecha_collection_id="pecha_collection_456",
            destination_url="https://destination.example"
        )
        
        assert result == "wb_collection_123"


@pytest.mark.asyncio
async def test_upload_text_metadata_service_success():
    """Test upload_text_metadata_service with translation texts"""
    service = TextMetadataService()
    
    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="text_1"
    )
    
    text_metadata = {
        "type": "translation",
        "language": "en",
        "title": {"en": "Test Text"}
    }
    
    text_related_by_work = {
        "work_1": {
            "relation": "translation",
            "expression_ids": ["text_2", "text_3"]
        }
    }
    
    with patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_text_metadata",
        new_callable=AsyncMock,
        return_value=text_metadata
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_text_related_by_work",
        new_callable=AsyncMock,
        return_value=text_related_by_work
    ), \
    patch.object(
        service,
        "get_text_meta_data_service",
        new_callable=AsyncMock,
        return_value={"new_text_id_1": "inst_1", "new_text_id_2": "inst_2"}
    ) as mock_get_texts:
        result = await service.upload_text_metadata_service(
            text_upload_request=text_upload_request,
            token="test_token"
        )
        
        assert isinstance(result, TextInstanceIds)
        assert len(result.new_text) > 0
        # Verify the service was called for translations
        assert mock_get_texts.call_count == 2


@pytest.mark.asyncio
async def test_upload_text_metadata_service_with_commentary():
    """Test upload_text_metadata_service with commentary texts"""
    service = TextMetadataService()
    
    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="commentary_1"
    )
    
    text_metadata = {
        "type": "commentary",
        "language": "bo",
        "title": {"bo": "མཚན་བྱང་"}
    }
    
    text_related_by_work = {
        "work_1": {
            "relation": "sibling_commentary",
            "expression_ids": ["commentary_2"]
        }
    }
    
    with patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_text_metadata",
        new_callable=AsyncMock,
        return_value=text_metadata
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_text_related_by_work",
        new_callable=AsyncMock,
        return_value=text_related_by_work
    ), \
    patch.object(
        service,
        "get_text_meta_data_service",
        new_callable=AsyncMock,
        return_value={"commentary_id_1": "inst_c1"}
    ):
        result = await service.upload_text_metadata_service(
            text_upload_request=text_upload_request,
            token="test_token"
        )
        
        assert isinstance(result, TextInstanceIds)
        assert result.new_text is not None


@pytest.mark.asyncio
async def test_get_text_meta_data_service_creates_group_for_first_text():
    """Test get_text_meta_data_service creates a new group for translations"""
    service = TextMetadataService()
    
    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="text_1"
    )
    
    text_metadata = {
        "language": "en",
        "title": {"en": "Test Text"},
        "category_id": "cat_1"
    }
    
    critical_instance = CriticalInstanceResponse(
        critical_instances=[
            CriticalInstance(
                id="inst_1",
                type="critical",
                source="https://source.example"
            )
        ]
    )
    
    with patch.object(
        service,
        "get_uploaded_texts",
        new_callable=AsyncMock,
        return_value=([], [], {"text_1": "inst_1"})
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_text_metadata",
        new_callable=AsyncMock,
        return_value=text_metadata
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.post_group",
        new_callable=AsyncMock,
        return_value={"id": "new_group_id"}
    ) as mock_post_group, \
    patch.object(
        service,
        "create_textmetada_payload",
        new_callable=AsyncMock,
        return_value=MagicMock()
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.post_text",
        new_callable=AsyncMock,
        return_value={"id": "new_text_id", "title": "Test Text"}
    ):
        result = await service.get_text_meta_data_service(
            text_ids=["text_1"],
            type="translation",
            text_upload_request=text_upload_request,
            token="test_token"
        )
        
        mock_post_group.assert_awaited_once()
        assert service.version_group_id == "new_group_id"
        assert "new_text_id" in result


@pytest.mark.asyncio
async def test_get_text_meta_data_service_skips_uploaded_texts():
    """Test get_text_meta_data_service skips already uploaded texts"""
    service = TextMetadataService()
    
    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="text_1"
    )
    
    text_metadata = {
        "language": "en",
        "title": {"en": "Already Uploaded Text"},
        "category_id": "cat_1"
    }
    
    # Mock that text_1 is already uploaded
    with patch.object(
        service,
        "get_uploaded_texts",
        new_callable=AsyncMock,
        return_value=(
            [{"id": "existing_id", "pecha_text_id": "inst_1", "group_id": "existing_group_id"}],
            ["text_1"],  # text_1 is already uploaded
            {"text_1": "inst_1"}
        )
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_text_metadata",
        new_callable=AsyncMock,
        return_value=text_metadata
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.post_text",
        new_callable=AsyncMock
    ) as mock_post_text:
        result = await service.get_text_meta_data_service(
            text_ids=["text_1"],
            type="translation",
            text_upload_request=text_upload_request,
            token="test_token"
        )
        
        # Should not post text since it's already uploaded
        mock_post_text.assert_not_awaited()
        assert result == {}
        # Version group should be set from uploaded text
        assert service.version_group_id == "existing_group_id"


@pytest.mark.asyncio
async def test_get_text_critical_instance_returns_critical_instances():
    """Test get_text_critical_instance returns CriticalInstanceResponse"""
    service = TextMetadataService()
    
    expected_instances = [
        CriticalInstance(
            id="inst_1",
            type="critical",
            source="https://source1.example"
        ),
        CriticalInstance(
            id="inst_2",
            type="critical",
            source="https://source2.example"
        )
    ]
    
    with patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_critical_instances",
        new_callable=AsyncMock,
        return_value=CriticalInstanceResponse(critical_instances=expected_instances)
    ):
        result = await service.get_text_critical_instance(
            text_id="text_1",
            openpecha_api_url="https://openpecha.example"
        )
        
        assert isinstance(result, CriticalInstanceResponse)
        assert len(result.critical_instances) == 2
        assert result.critical_instances[0].id == "inst_1"


@pytest.mark.asyncio
async def test_get_text_meta_data_service_commentary_creates_separate_group():
    """Test get_text_meta_data_service creates separate group for commentary"""
    service = TextMetadataService()
    service.version_group_id = "version_group_123"
    
    text_upload_request = TextUploadRequest(
        destination_url="https://destination.example",
        openpecha_api_url="https://openpecha.example",
        text_id="commentary_1"
    )
    
    text_metadata = {
        "language": "bo",
        "title": {"bo": "མཚན་བྱང་"},
        "category_id": "cat_1"
    }
    
    with patch.object(
        service,
        "get_uploaded_texts",
        new_callable=AsyncMock,
        return_value=([], [], {"commentary_1": "inst_c1"})
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.get_text_metadata",
        new_callable=AsyncMock,
        return_value=text_metadata
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.post_group",
        new_callable=AsyncMock,
        return_value={"id": "commentary_group_id"}
    ) as mock_post_group, \
    patch.object(
        service,
        "create_textmetada_payload",
        new_callable=AsyncMock,
        return_value=MagicMock()
    ), \
    patch(
        "pecha_api.text_uploader.text_metadata.text_metadata_service.post_text",
        new_callable=AsyncMock,
        return_value={"id": "commentary_text_id", "title": "Commentary"}
    ):
        result = await service.get_text_meta_data_service(
            text_ids=["commentary_1"],
            type="commentary",
            text_upload_request=text_upload_request,
            token="test_token"
        )
        
        # Should create commentary group
        mock_post_group.assert_awaited_once_with('commentary', text_upload_request.destination_url, "test_token")
        assert service.commentary_group_id == "commentary_group_id"
        assert "commentary_text_id" in result



