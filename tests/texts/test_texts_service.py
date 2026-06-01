from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from uuid import uuid4

import pytest
from pecha_api.texts.texts_service import (
    create_table_of_content,
    update_text_details,
    get_table_of_content_by_type,
    get_root_text_by_collection_id,
    replace_pecha_segment_id_with_segment_id,
)
from pecha_api.texts.texts_response_models import (
    TextDTO,
    TableOfContent,
    TableOfContentType,
    Section,
    TextSegment,
    UpdateTextRequest,
    TextsByPechaTextIdsRequest,
)
from pecha_api.recitations.recitations_response_models import RecitationDTO, RecitationsResponse

from pecha_api.error_contants import ErrorConstants

@pytest.mark.asyncio
async def test_create_table_of_content_success():
    # Incoming TOC from client uses segment_id to hold pecha_segment_id; service will map to real segment_id
    incoming_toc = TableOfContent(
        id="id_1",
        text_id="id_1",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="id_1",
                title="section_1",
                section_number=1,
                parent_id="id_1",
                segments=[
                    # segment_id holds the pecha_segment_id value
                    TextSegment(segment_id="pseg_1", segment_number=1)
                ],
                sections=[],
                created_date="2025-03-16 04:40:54.757652",
                updated_date="2025-03-16 04:40:54.757652",
                published_date="2025-03-16 04:40:54.757652"
            )
        ]
    )
    # Expected TOC after mapping pecha_segment_id -> segment_id
    expected_toc = TableOfContent(
        id="id_1",
        text_id="id_1",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="id_1",
                title="section_1",
                section_number=1,
                parent_id="id_1",
                segments=[TextSegment(segment_id="id_1", segment_number=1)],
                sections=[],
                created_date="2025-03-16 04:40:54.757652",
                updated_date="2025-03-16 04:40:54.757652",
                published_date="2025-03-16 04:40:54.757652"
            )
        ]
    )

    with patch("pecha_api.texts.texts_service.validate_user_exists", return_value=True), \
            patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock) as mock_validate_text_exists, \
            patch("pecha_api.texts.texts_service.SegmentUtils.validate_segments_exists", new_callable=AsyncMock) as mock_validate_segments_exists, \
            patch("pecha_api.texts.texts_service.get_segments_by_text_id", new_callable=AsyncMock) as mock_get_segments_by_text_id, \
            patch("pecha_api.texts.texts_service.create_table_of_content_detail", new_callable=AsyncMock) as mock_create_table_of_content_detail:
        mock_validate_text_exists.return_value = True
        mock_validate_segments_exists.return_value = True
        # Return segments for the text so mapping pseg_1 -> id_1 works
        mock_get_segments_by_text_id.return_value = [type("Seg", (), {"id": "id_1", "pecha_segment_id": "pseg_1"})()]
        mock_create_table_of_content_detail.return_value = expected_toc
        response = await create_table_of_content(table_of_content_request=incoming_toc, token="admin")
        assert response is not None
        assert isinstance(response, TableOfContent)
        assert response.id == expected_toc.id
        assert response.text_id == expected_toc.text_id
        assert response.sections is not None
        assert len(response.sections) == 1
        assert response.sections[0].id == expected_toc.sections[0].id
        assert response.sections[0].title == expected_toc.sections[0].title
        assert response.sections[0].section_number == expected_toc.sections[0].section_number
        assert response.sections[0].parent_id == expected_toc.sections[0].parent_id
        assert response.sections[0].segments is not None
        assert len(response.sections[0].segments) == 1
        assert response.sections[0].segments[0].segment_id == expected_toc.sections[0].segments[0].segment_id
        assert response.sections[0].segments[0].segment_number == expected_toc.sections[0].segments[0].segment_number
    
@pytest.mark.asyncio
async def test_create_table_of_content_invalid_user():
    with patch("pecha_api.texts.texts_service.validate_user_exists", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await create_table_of_content(table_of_content_request={}, token="user")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

@pytest.mark.asyncio
async def test_create_table_of_content_invalid_text():
    table_of_content = TableOfContent(
        id="id_1",
        text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        type=TableOfContentType.TEXT,
        sections=[]
    )
    with patch("pecha_api.texts.texts_service.validate_user_exists", return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, side_effect=HTTPException(status_code=404, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)):
        with pytest.raises(HTTPException) as exc_info:
            await create_table_of_content(table_of_content_request=table_of_content, token="admin")
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_create_table_of_content_invalid_segment():
    table_of_content = TableOfContent(
        id="id_1",
        text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        type=TableOfContentType.TEXT,
        sections=[]
    )
    segment_ids = [
        "efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        "efb26a06-f373-450b-ba57-e7a8d4dd5b65"
    ]
    with patch("pecha_api.texts.texts_service.validate_user_exists", return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.get_all_segment_ids", return_value=segment_ids), \
        patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.get_segments_by_text_id", new_callable=AsyncMock, return_value=[]), \
        patch("pecha_api.texts.segments.segments_utils.check_all_segment_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await create_table_of_content(table_of_content_request=table_of_content, token="admin")
        assert exc_info.value.status_code == 404
        # The error message includes the segment IDs in the format: "Segment not found {segment_ids}"
        assert ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE in exc_info.value.detail
        assert str(segment_ids) in exc_info.value.detail
    
@pytest.mark.asyncio
async def test_update_text_details_success():
    mock_text_details = TextDTO(
        id="text_id_1",
        title="text_title",
        language="bo",
        group_id="group_id_1",
        type="version",
        is_published=False,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=[],
        views=0
    )
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock) as mock_get_text_detail_by_id, \
        patch("pecha_api.texts.texts_service.update_text_details_by_id", new_callable=AsyncMock, return_value=mock_text_details), \
        patch("pecha_api.texts.texts_service.update_text_details_cache", new_callable=AsyncMock, return_value=None), \
        patch("pecha_api.texts.texts_service.invalidate_text_cache_on_update", new_callable=AsyncMock, return_value=None):
        mock_get_text_detail_by_id.return_value = mock_text_details
        
        response = await update_text_details(text_id="text_id_1", update_text_request=UpdateTextRequest(title="updated_title", is_published=True))
        
        assert response is not None
        assert response.title == "updated_title"
        assert response.is_published == True

@pytest.mark.asyncio
async def test_update_text_details_invalid_text_id():
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exec_info:
            await update_text_details(text_id="invalid_id", update_text_request=UpdateTextRequest(title="updated_title", is_published=True))
        assert exec_info.value.status_code == 404
        assert exec_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE
    
@pytest.mark.asyncio
async def test_get_root_text_by_collection_id_success_with_root_text():
    """Test get_root_text_by_collection_id when root text is found"""
    collection_id = str(uuid4())
    language = "bo"
    text_id_1 = str(uuid4())
    text_id_2 = str(uuid4())
    group_id_1 = str(uuid4())
    
    mock_texts = [
        TextDTO(
            id=text_id_1,
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            language="bo",
            group_id=group_id_1,
            type="version",
            is_published=True,
            created_date="2025-03-20 09:26:16.571522",
            updated_date="2025-03-20 09:26:16.571532",
            published_date="2025-03-20 09:26:16.571536",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id=text_id_2,
            title="The Way of the Bodhisattva",
            language="en",
            group_id=group_id_1,
            type="version",
            is_published=True,
            created_date="2025-03-20 09:28:28.076920",
            updated_date="2025-03-20 09:28:28.076934",
            published_date="2025-03-20 09:28:28.076938",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    
    mock_filtered_result = {
        "root_text": mock_texts[0],  
        "versions": [mock_texts[1]]
    }
    
    with patch("pecha_api.texts.texts_service.get_all_recitation_texts_by_collection", new_callable=AsyncMock) as mock_get_all_texts, \
         patch("pecha_api.texts.texts_service.TextUtils.filter_text_base_on_group_id_type_and_language_preference", new_callable=AsyncMock) as mock_filter:
        
        mock_get_all_texts.return_value = mock_texts
        mock_filter.return_value = mock_filtered_result
        
        result = await get_root_text_by_collection_id(collection_id=collection_id, language=language)
        
        mock_get_all_texts.assert_called_once_with(collection_id=collection_id, language=language)
        
        assert result is not None
        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 1
        assert isinstance(result.recitations[0], RecitationDTO)
        assert str(result.recitations[0].text_id) == text_id_1
        assert result.recitations[0].title == "བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།"

@pytest.mark.asyncio
async def test_get_root_text_by_collection_id_no_root_text():
    """Test get_root_text_by_collection_id when no root text is found"""
    collection_id = str(uuid4())
    language = "zh"
    text_id_1 = str(uuid4())
    group_id_1 = str(uuid4())
    
    mock_texts = [
        TextDTO(
            id=text_id_1,
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            language="bo",
            group_id=group_id_1,
            type="version",
            is_published=True,
            created_date="2025-03-20 09:26:16.571522",
            updated_date="2025-03-20 09:26:16.571532",
            published_date="2025-03-20 09:26:16.571536",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    
    # Mock the filtered result with no root text found
    mock_filtered_result = {
        "root_text": None,
        "versions": mock_texts
    }
    
    with patch("pecha_api.texts.texts_service.get_all_recitation_texts_by_collection", new_callable=AsyncMock) as mock_get_all_texts, \
         patch("pecha_api.texts.texts_service.TextUtils.filter_text_base_on_group_id_type_and_language_preference", new_callable=AsyncMock) as mock_filter:
        
        mock_get_all_texts.return_value = mock_texts
        mock_filter.return_value = mock_filtered_result
        
        result = await get_root_text_by_collection_id(collection_id=collection_id, language=language)
        
        # Verify the result - should return empty RecitationsResponse
        assert result is not None
        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 0
        assert result.recitations == []

@pytest.mark.asyncio
async def test_get_root_text_by_collection_id_multiple_groups():
    """Test get_root_text_by_collection_id with multiple groups"""
    collection_id = str(uuid4())
    language = "bo"
    
    text_id_1 = str(uuid4())
    text_id_2 = str(uuid4())
    text_id_3 = str(uuid4())
    text_id_4 = str(uuid4())
    group_id_1 = str(uuid4())
    group_id_2 = str(uuid4())
    
    mock_texts = [
        # Group 1
        TextDTO(
            id=text_id_1,
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            language="bo",
            group_id=group_id_1,
            type="version",
            is_published=True,
            created_date="2025-03-20 09:26:16.571522",
            updated_date="2025-03-20 09:26:16.571532",
            published_date="2025-03-20 09:26:16.571536",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id=text_id_2,
            title="The Way of the Bodhisattva",
            language="en",
            group_id=group_id_1,
            type="version",
            is_published=True,
            created_date="2025-03-20 09:28:28.076920",
            updated_date="2025-03-20 09:28:28.076934",
            published_date="2025-03-20 09:28:28.076938",
            published_by="pecha",
            categories=[],
            views=0
        ),
        # Group 2
        TextDTO(
            id=text_id_3,
            title="མཁན་པོ་ཞི་བ་ལྷའི་རྣམ་ཐར།",
            language="bo",
            group_id=group_id_2,
            type="root_text",
            is_published=True,
            created_date="2025-03-20 09:30:00.000000",
            updated_date="2025-03-20 09:30:00.000000",
            published_date="2025-03-20 09:30:00.000000",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id=text_id_4,
            title="Biography of Shantideva",
            language="en",
            group_id=group_id_2,
            type="version",
            is_published=True,
            created_date="2025-03-20 09:31:00.000000",
            updated_date="2025-03-20 09:31:00.000000",
            published_date="2025-03-20 09:31:00.000000",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    
    # Mock filters for each group
    def mock_filter_side_effect(texts, language):
        if texts[0].group_id == group_id_1:
            return {"root_text": texts[0], "versions": [texts[1]]}
        elif texts[0].group_id == group_id_2:
            return {"root_text": texts[0], "versions": [texts[1]]}
        return {"root_text": None, "versions": texts}
    
    with patch("pecha_api.texts.texts_service.get_all_recitation_texts_by_collection", new_callable=AsyncMock) as mock_get_all_texts, \
         patch("pecha_api.texts.texts_service.TextUtils.filter_text_base_on_group_id_type_and_language_preference", new_callable=AsyncMock) as mock_filter:
        
        mock_get_all_texts.return_value = mock_texts
        mock_filter.side_effect = mock_filter_side_effect
        
        result = await get_root_text_by_collection_id(collection_id=collection_id, language=language)
        
        mock_get_all_texts.assert_called_once_with(collection_id=collection_id, language=language)
        
        assert result is not None
        assert isinstance(result, RecitationsResponse)
        assert len(result.recitations) == 2
        assert isinstance(result.recitations[0], RecitationDTO)
        assert isinstance(result.recitations[1], RecitationDTO)
        # Check that we got both root texts
        text_ids = {str(rec.text_id) for rec in result.recitations}
        assert text_id_1 in text_ids
        assert text_id_3 in text_ids

@pytest.mark.asyncio
async def test_get_table_of_content_by_type_text_type():
    """Test get_table_of_content_by_type with TEXT type"""
    text_id = "text_id_1"
    
    incoming_toc = TableOfContent(
        id="toc_id_1",
        text_id=text_id,
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_id_1",
                title="section_1",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    TextSegment(segment_id="pseg_1", segment_number=1)
                ],
                sections=[],
                created_date="2025-03-16 04:40:54.757652",
                updated_date="2025-03-16 04:40:54.757652",
                published_date="2025-03-16 04:40:54.757652"
            )
        ]
    )
    
    expected_toc = TableOfContent(
        text_id=text_id,
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_id_1",
                title="section_1",
                section_number=1,
                segments=[TextSegment(segment_id="seg_id_1", segment_number=1)]
            )
        ]
    )
    
    with patch("pecha_api.texts.texts_service.get_segments_by_text_id", new_callable=AsyncMock) as mock_get_segments:
        mock_get_segments.return_value = [type("Seg", (), {"id": "seg_id_1", "pecha_segment_id": "pseg_1"})()]
        
        result = await get_table_of_content_by_type(table_of_content=incoming_toc)
        
        assert result is not None
        assert isinstance(result, TableOfContent)
        assert result.text_id == text_id
        assert result.type == TableOfContentType.TEXT
        assert len(result.sections) == 1
        assert result.sections[0].segments[0].segment_id == "seg_id_1"

@pytest.mark.asyncio
async def test_get_table_of_content_by_type_sheet_type():
    """Test get_table_of_content_by_type with SHEET type"""
    text_id = "text_id_1"
    
    incoming_toc = TableOfContent(
        id="toc_id_1",
        text_id=text_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_id_1",
                title="section_1",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    TextSegment(segment_id="seg_1", segment_number=1)
                ],
                sections=[],
                created_date="2025-03-16 04:40:54.757652",
                updated_date="2025-03-16 04:40:54.757652",
                published_date="2025-03-16 04:40:54.757652"
            )
        ]
    )
    
    result = await get_table_of_content_by_type(table_of_content=incoming_toc)
    
    assert result is not None
    assert isinstance(result, TableOfContent)
    assert result.text_id == text_id
    assert result.type == TableOfContentType.SHEET
    assert result.sections == incoming_toc.sections



@pytest.mark.asyncio
async def test_update_text_details_cache_update_fails():
    """Test update_text_details when cache update fails"""
    mock_text_details = TextDTO(
        id="text_id_1",
        title="text_title",
        language="bo",
        group_id="group_id_1",
        type="version",
        is_published=False,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_details), \
        patch("pecha_api.texts.texts_service.update_text_details_by_id", new_callable=AsyncMock, return_value=mock_text_details), \
        patch("pecha_api.texts.texts_service.update_text_details_cache", new_callable=AsyncMock, side_effect=Exception("Cache error")), \
        patch("pecha_api.texts.texts_service.invalidate_text_cache_on_update", new_callable=AsyncMock, return_value=None) as mock_invalidate:
        
        response = await update_text_details(text_id="text_id_1", update_text_request=UpdateTextRequest(title="updated_title", is_published=True))
        
        assert response is not None
        # Verify that invalidate was called as fallback
        mock_invalidate.assert_called_once_with(text_id="text_id_1")

@pytest.mark.asyncio
async def test_update_text_details_with_cache_invalidation():
    """Test update_text_details updates text successfully"""
    text_id = "123e4567-e89b-12d3-a456-426614174000"
    update_request = UpdateTextRequest(
        title="Updated Title",
        language="bo"
    )
    
    updated_text = TextDTO(
        id=text_id,
        title="Updated Title",
        language="bo",
        group_id="group_id_1",
        type="version",
        is_published=True,
        created_date="2025-03-21 09:40:34.025024",
        updated_date="2025-03-21 09:40:34.025035",
        published_date="2025-03-21 09:40:34.025038",
        published_by="pecha",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
         patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=updated_text), \
         patch("pecha_api.texts.texts_service.update_text_details_by_id", new_callable=AsyncMock, return_value=updated_text) as mock_update, \
         patch("pecha_api.texts.texts_service.invalidate_text_cache_on_update", new_callable=AsyncMock):
        
        result = await update_text_details(text_id=text_id, update_text_request=update_request)
        
        assert result is not None
        assert result.title == "Updated Title"
        mock_update.assert_called_once_with(text_id=text_id, update_text_request=update_request)

# Tests for new private functions
def test_group_texts_by_group_id_with_language_sorting():
    """Test _group_texts_by_group_id groups texts and sorts by language preference"""
    from pecha_api.texts.texts_service import _group_texts_by_group_id
    
    # Create mock texts with different group_ids and languages
    mock_texts = [
        TextDTO(
            id="text_id_1",
            title="Text 1 Bo",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="Text 2 En",
            language="en",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_3",
            title="Text 3 Zh",
            language="zh",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_4",
            title="Text 4 Bo Group2",
            language="bo",
            group_id="group_2",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    
    # Test with 'en' as preferred language
    result = _group_texts_by_group_id(texts=mock_texts, language="en")
    
    # Verify grouping
    assert len(result) == 2
    assert "group_1" in result
    assert "group_2" in result
    assert len(result["group_1"]) == 3
    assert len(result["group_2"]) == 1
    
    # Verify sorting - 'en' should be first for group_1
    assert result["group_1"][0].language == "en"
    assert result["group_1"][1].language == "bo"
    assert result["group_1"][2].language == "zh"


def test_group_texts_by_group_id_with_bo_preference():
    """Test _group_texts_by_group_id with Tibetan (bo) language preference"""
    from pecha_api.texts.texts_service import _group_texts_by_group_id
    
    mock_texts = [
        TextDTO(
            id="text_id_1",
            title="Text En",
            language="en",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="Text Bo",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    
    result = _group_texts_by_group_id(texts=mock_texts, language="bo")
    
    # Verify 'bo' is first
    assert result["group_1"][0].language == "bo"
    assert result["group_1"][1].language == "en"


def test_get_language_priority_via_textutils():
    """Test language priority through TextUtils (used by service layer)"""
    from pecha_api.texts.texts_utils import TextUtils
    
    # Test with 'bo' preference
    assert TextUtils.get_language_priority("bo", "bo") == 0
    assert TextUtils.get_language_priority("en", "bo") == 1
    assert TextUtils.get_language_priority("zh", "bo") == 2
    assert TextUtils.get_language_priority("unknown", "bo") == 999
    
    # Test with 'en' preference
    assert TextUtils.get_language_priority("en", "en") == 0
    assert TextUtils.get_language_priority("bo", "en") == 1
    assert TextUtils.get_language_priority("zh", "en") == 2
    assert TextUtils.get_language_priority("unknown", "en") == 999
    
    # Test with 'zh' preference
    assert TextUtils.get_language_priority("zh", "zh") == 0
    assert TextUtils.get_language_priority("en", "zh") == 1
    assert TextUtils.get_language_priority("bo", "zh") == 2


def test_get_language_priority_with_none_via_textutils():
    """Test TextUtils.get_language_priority handles None text_language"""
    from pecha_api.texts.texts_utils import TextUtils
    
    # None language should get default priority
    assert TextUtils.get_language_priority(None, "bo") == 999
    assert TextUtils.get_language_priority(None, "en") == 999


def test_group_texts_by_group_id_empty_texts():
    """Test _group_texts_by_group_id with empty text list"""
    from pecha_api.texts.texts_service import _group_texts_by_group_id
    
    result = _group_texts_by_group_id(texts=[], language="bo")
    
    assert result == {}


def test_group_texts_by_group_id_single_group():
    """Test _group_texts_by_group_id with single group"""
    from pecha_api.texts.texts_service import _group_texts_by_group_id
    
    mock_texts = [
        TextDTO(
            id="text_id_1",
            title="Text 1",
            language="bo",
            group_id="single_group",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    
    result = _group_texts_by_group_id(texts=mock_texts, language="bo")
    
    assert len(result) == 1
    assert "single_group" in result
    assert len(result["single_group"]) == 1
    assert result["single_group"][0].id == "text_id_1"



@pytest.mark.asyncio
async def test_replace_pecha_segment_id_with_segment_id_success():
    """Test replace_pecha_segment_id_with_segment_id converts pecha segment IDs to database segment IDs"""
    text_id = "text_id_1"
    
    # Mock segments from database
    class MockSegment:
        def __init__(self, segment_id, pecha_segment_id):
            self.id = segment_id
            self.pecha_segment_id = pecha_segment_id
    
    mock_segments = [
        MockSegment("db_seg_1", "pecha_seg_1"),
        MockSegment("db_seg_2", "pecha_seg_2")
    ]
    
    incoming_toc = TableOfContent(
        text_id=text_id,
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_1",
                title="Section 1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="pecha_seg_1", segment_number=1),
                    TextSegment(segment_id="pecha_seg_2", segment_number=2)
                ]
            )
        ]
    )
    
    with patch("pecha_api.texts.texts_service.get_segments_by_text_id", new_callable=AsyncMock, return_value=mock_segments):
        result = await replace_pecha_segment_id_with_segment_id(table_of_content=incoming_toc)
        
        assert result is not None
        assert isinstance(result, TableOfContent)
        assert result.text_id == text_id
        assert result.type == TableOfContentType.TEXT
        assert len(result.sections) == 1
        assert len(result.sections[0].segments) == 2
        # Verify segment IDs were replaced
        assert result.sections[0].segments[0].segment_id == "db_seg_1"
        assert result.sections[0].segments[1].segment_id == "db_seg_2"


@pytest.mark.asyncio
async def test_replace_pecha_segment_id_with_segment_id_multiple_sections():
    """Test replace_pecha_segment_id_with_segment_id with multiple sections"""
    text_id = "text_id_1"
    
    class MockSegment:
        def __init__(self, segment_id, pecha_segment_id):
            self.id = segment_id
            self.pecha_segment_id = pecha_segment_id
    
    mock_segments = [
        MockSegment("db_seg_1", "pecha_seg_1"),
        MockSegment("db_seg_2", "pecha_seg_2"),
        MockSegment("db_seg_3", "pecha_seg_3")
    ]
    
    incoming_toc = TableOfContent(
        text_id=text_id,
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_1",
                title="Section 1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="pecha_seg_1", segment_number=1)
                ]
            ),
            Section(
                id="section_2",
                title="Section 2",
                section_number=2,
                segments=[
                    TextSegment(segment_id="pecha_seg_2", segment_number=1),
                    TextSegment(segment_id="pecha_seg_3", segment_number=2)
                ]
            )
        ]
    )
    
    with patch("pecha_api.texts.texts_service.get_segments_by_text_id", new_callable=AsyncMock, return_value=mock_segments):
        result = await replace_pecha_segment_id_with_segment_id(table_of_content=incoming_toc)
        
        assert result is not None
        assert len(result.sections) == 2
        assert result.sections[0].segments[0].segment_id == "db_seg_1"
        assert result.sections[1].segments[0].segment_id == "db_seg_2"
        assert result.sections[1].segments[1].segment_id == "db_seg_3"