import pytest
from typing import Union
from unittest.mock import AsyncMock, patch
from uuid import UUID
from uuid import uuid4
from fastapi import HTTPException

from pecha_api.texts.segments.segments_utils import SegmentUtils


from pecha_api.texts.segments.segments_response_models import (
    MappingResponse,
    SegmentDTO,
    SegmentTranslation,
    SegmentCommentry,
    SegmentRootMapping,
    MappedSegmentDTO
)
from pecha_api.texts.texts_response_models import (
    TextDTO,
    DetailTableOfContent,
    Section,
    TextSegment,
    TableOfContent,
    TableOfContentType
)
from pecha_api.texts.segments.segments_enum import SegmentType

from pecha_api.texts.groups.groups_response_models import GroupDTO

@pytest.mark.asyncio
async def test_get_count_of_each_commentary_and_version_success():
    parent_text = TextDTO(
        id="parent-text-id",
        title="Parent Text",
        language="bo",
        group_id="group_id",
        type="version",
        is_published=True,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=["categories"],
        views=0
    )
    text_details = {
        "efb26a06-f373-450b-ba57-e7a8d4dd5b64": TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            title="title",
            language="language",
            group_id="group_id",
            type="commentary",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        ),
        "efb26a06-f373-450b-ba57-e7a8d4dd5b65": TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b65",
            title="title",
            language="language",
            group_id="group_id",
            type="version",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        ),
        "efb26a06-f373-450b-ba57-e7a8d4dd5b66": TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b66",
            title="title",
            language="language",
            group_id="group_id",
            type="commentary",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
    }
    list_of_segment_paramenter = [
        SegmentDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            content="content",
            mapping=[],
            type=SegmentType.SOURCE
        ),
        SegmentDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b65",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b65",
            content="content",
            mapping=[],
            type=SegmentType.SOURCE
        ),
        SegmentDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b66",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b66",
            content="content",
            mapping=[],
            type=SegmentType.SOURCE
        )
    ]
    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details):
        result = await SegmentUtils.get_count_of_each_commentary_and_version(list_of_segment_paramenter, parent_text=parent_text)
        assert result["commentary"] == 2
        assert result["version"] == 1

@pytest.mark.asyncio
async def test_filter_segment_mapping_by_type_success():
    """Test filtering segments by commentary type returns correct SegmentCommentry objects."""
    text_details = {
        "efb26a06-f373-450b-ba57-e7a8d4dd5b64": TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            title="Commentary One",
            language="bo",
            group_id="group_id",
            type="commentary",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        ),
        "efb26a06-f373-450b-ba57-e7a8d4dd5b65": TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b65",
            title="Version One",
            language="en",
            group_id="group_id",
            type="version",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        ),
        "efb26a06-f373-450b-ba57-e7a8d4dd5b66": TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b66",
            title="Commentary Two",
            language="bo",
            group_id="group_id",
            type="commentary",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
    }
    segments = [
        SegmentDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            content="commentary one content",
            mapping=[],
            type=SegmentType.SOURCE
        ),
        SegmentDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b65",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b65",
            content="version content",
            mapping=[],
            type=SegmentType.SOURCE
        ),
        SegmentDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b66",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b66",
            content="commentary two content",
            mapping=[],
            type=SegmentType.SOURCE
        )
    ]
    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details):
        response = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments, "commentary")
        
        # Should return 2 commentary results (filtering out the version)
        assert len(response) == 2
        assert isinstance(response[0], SegmentCommentry)
        assert isinstance(response[1], SegmentCommentry)
        
        # Verify first commentary
        assert response[0].text_id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
        assert response[0].title == "Commentary One"
        assert response[0].language == "bo"
        assert len(response[0].segments) == 1
        assert response[0].segments[0].segment_id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
        assert response[0].segments[0].content == "commentary one content"
        assert response[0].count == 1
        
        # Verify second commentary
        assert response[1].text_id == "efb26a06-f373-450b-ba57-e7a8d4dd5b66"
        assert response[1].title == "Commentary Two"
        assert response[1].language == "bo"
        assert len(response[1].segments) == 1
        assert response[1].segments[0].segment_id == "efb26a06-f373-450b-ba57-e7a8d4dd5b66"
        assert response[1].segments[0].content == "commentary two content"
        assert response[1].count == 1
        
@pytest.mark.asyncio
async def test_get_root_mapping_count_success():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    group_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b65"
    
    # Create mock text details for each mapped text (non-commentary types to be counted)
    mock_text_details_map = {}
    for i in range(1, 6):
        mock_text_details_map[f"text_id_{i}"] = TextDTO(
            id=f"text_id_{i}",
            title=f"title_{i}",
            language="language",
            type="version",  # Changed to version so they won't be skipped
            group_id=group_id,
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
    
    segment = SegmentDTO(
        id=segment_id,
        text_id=text_id,
        content="content",
        mapping=[
            MappingResponse(
                text_id=f"text_id_{i}",
                segments=[
                    f"segment_id_{i}"
                ]
            )
            for i in range(1,6)
        ],
        type=SegmentType.SOURCE
    )
    
    text_details = TextDTO(
        id=text_id,
        title="title",
        language="language",
        type="commentary",
        group_id=group_id,
        is_published=True,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=["categories"],
        views=0
    )
    
    # Create mapped text details with different type/group to pass the filter
    mapped_text_details = {
        f"text_id_{i}": TextDTO(
            id=f"text_id_{i}",
            title=f"title_{i}",
            language="language",
            type="version",  # Different type from parent
            group_id="different_group_id",  # Different group from parent
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
        for i in range(1, 6)
    }
    
    mock_group_details = GroupDTO(
        id=group_id,
        type="COMMENTARY"
    )
    
    # Mock to return different text details based on text_id
    async def mock_get_text_details_by_id(text_id):
        if text_id in mock_text_details_map:
            return mock_text_details_map[text_id]
        return text_details
    
    with patch("pecha_api.texts.segments.segments_utils.get_segment_by_id", new_callable=AsyncMock, return_value=segment), \
        patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_id", new_callable=AsyncMock, side_effect=mock_get_text_details_by_id), \
        patch("pecha_api.texts.segments.segments_utils.get_group_details", new_callable=AsyncMock, return_value=mock_group_details):
        response = await SegmentUtils.get_root_mapping_count(segment_id=segment_id)
        assert response == 5
    
@pytest.mark.asyncio
async def test_get_segment_root_mapping_details_success():
    parent_text = TextDTO(
        id="parent-text-id",
        title="Parent Title",
        language="bo",
        group_id="group_id",
        type="version",
        is_published=True,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=["categories"],
        views=0
    )
    segments = [
        SegmentDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            text_id="text_id_1",
            content="content",
            mapping=[
                MappingResponse(
                    text_id="text_id_1",
                    segments=[
                        "segment_id_1"
                    ]
                )
            ],
            type=SegmentType.SOURCE
        )
    ]
    text_details = {
        "text_id_1": TextDTO(
            id="text_id_1",
            title="title",
            language="language",
            group_id="different_group_id",
            type="commentary",  # Different type
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
    }
    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details):
        response = await SegmentUtils.get_segment_root_mapping_details(segments=segments, parent_segment_text=parent_text)
        assert isinstance(response[0], SegmentRootMapping)
        assert response[0].text_id == "text_id_1"
        assert response[0].title == "title"
        assert response[0].language == "language"
        assert len(response[0].segments) == 1
        assert response[0].segments[0].segment_id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
        assert response[0].segments[0].content == "content"
          
@pytest.mark.asyncio
async def test_mapped_segment_content_for_table_of_content_without_version_id_success():
    table_of_content = TableOfContent(
        id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        text_id="5f3c2e9d-9b7a-4f5e-8e2a-6a8b7c9d4e0f",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="123e4567-e89b-12d3-a456-426614174000",
                title="title",
                section_number=1,
                parent_id=None,
                segments=[
                    TextSegment(
                        segment_id="anju6a06-f373-a50b-ba57-e7a8d4dd5555",
                        segment_number=1
                    )
                ],
                sections=[],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )
    segment = SegmentDTO(
        id="anju6a06-f373-a50b-ba57-e7a8d4dd5555",
        text_id="4fae1b8e-9f2b-4d3c-8c6e-3a1b9e4d2f7c",
        content="content",
        mapping=[],
        type=SegmentType.SOURCE
    )
    related_mapped_segments = [
        SegmentDTO(
            id=str(uuid4()),
            text_id=str(uuid4()),
            content="content",
            mapping=[
                MappingResponse(
                    text_id="4fae1b8e-9f2b-4d3c-8c6e-3a1b9e4d2f7c",
                    segments=[
                        "anju6a06-f373-a50b-ba57-e7a8d4dd5555"
                    ]
                )
            ],
            type=SegmentType.SOURCE
        )
    ]
    with patch("pecha_api.texts.segments.segments_utils.get_segment_by_id", new_callable=AsyncMock, return_value=segment), \
        patch("pecha_api.texts.segments.segments_utils.get_related_mapped_segments", new_callable=AsyncMock, return_value=related_mapped_segments):
        response = await SegmentUtils.get_mapped_segment_content_for_table_of_content(table_of_content=table_of_content, version_id=None)
        assert isinstance(response, DetailTableOfContent)
        assert response.text_id == "5f3c2e9d-9b7a-4f5e-8e2a-6a8b7c9d4e0f"
        assert response.sections[0].title == "title"
        assert response.sections[0].section_number == 1
        assert response.sections[0].parent_id is None
        assert response.sections[0].segments[0].segment_id == "anju6a06-f373-a50b-ba57-e7a8d4dd5555"
        assert response.sections[0].segments[0].segment_number == 1
        assert response.sections[0].segments[0].content == "content"


@pytest.mark.asyncio
async def test_validate_segment_exists_invalid_uuid():
    with pytest.raises(HTTPException) as exc_info:
        await SegmentUtils.validate_segment_exists(segment_id="not-a-uuid")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_validate_segments_exists_invalid_uuid_in_list():
    with pytest.raises(HTTPException) as exc_info:
        await SegmentUtils.validate_segments_exists(segment_ids=["valid-uuid-wont-parse", "also-bad"])
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_root_mapping_count_group_type_text_returns_zero():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    text_id = "text-id-1"
    
    parent_text = TextDTO(
        id="parent_text_id",
        title="parent title",
        language="en",
        type="root_text",
        group_id="parent_group_id",
        is_published=True,
        created_date="",
        updated_date="",
        published_date="",
        published_by="",
        categories=[],
        views=0,
    )
    
    segment = SegmentDTO(
        id=segment_id,
        text_id=text_id,
        content="content",
        mapping=[
            MappingResponse(text_id="t1", segments=["s1", "s2"]),
        ],
        type=SegmentType.SOURCE,
    )
    text_details = TextDTO(
        id=text_id,
        title="title",
        language="en",
        type="commentary",
        group_id="g1",
        is_published=True,
        created_date="",
        updated_date="",
        published_date="",
        published_by="",
        categories=[],
        views=0,
    )
    
    mapped_text_details = {
        "t1": TextDTO(
            id="t1",
            title="title",
            language="en",
            type="version",
            group_id="different_group",
            is_published=True,
            created_date="",
            updated_date="",
            published_date="",
            published_by="",
            categories=[],
            views=0,
        )
    }
    
    group_detail = GroupDTO(id="g1", type="text")

    with patch("pecha_api.texts.segments.segments_utils.get_segment_by_id", new_callable=AsyncMock, return_value=segment), \
        patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=text_details), \
        patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=mapped_text_details), \
        patch("pecha_api.texts.segments.segments_utils.get_group_details", new_callable=AsyncMock, return_value=group_detail):
        count = await SegmentUtils.get_root_mapping_count(segment_id=segment_id)
        assert count == 0


@pytest.mark.asyncio
async def test_filter_segment_mapping_by_type_commentary_merges_same_text_id():
    """
    Test that multiple segments from the same commentary text_id are merged into a single
    SegmentCommentry object with all segments included and correct count.
    """
    text_id = "commentary-text-1"
    segments = [
        SegmentDTO(
            id="seg-1",
            text_id=text_id,
            content="First segment content",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
        SegmentDTO(
            id="seg-2",
            text_id=text_id,
            content="Second segment content",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
    ]
    text_details = {
        text_id: TextDTO(
            id=text_id,
            title="Commentary Title",
            language="bo",
            type="commentary",
            group_id="g1",
            is_published=True,
            created_date="",
            updated_date="",
            published_date="",
            published_by="",
            categories=[],
            views=0,
        )
    }

    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details):
        result = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments, type="commentary")
        
        # Should return only 1 commentary (merged)
        assert len(result) == 1
        commentary = result[0]
        
        # Verify it's the correct type
        assert isinstance(commentary, SegmentCommentry)
        
        # Verify commentary details
        assert commentary.text_id == text_id
        assert commentary.title == "Commentary Title"
        assert commentary.language == "bo"
        
        # Verify segments are merged into a single MappedSegmentDTO
        # The implementation merges all content from the same text_id into one segment
        assert len(commentary.segments) == 1
        assert commentary.count == 1
        
        # Verify merged segment has first segment's ID and concatenated content
        assert commentary.segments[0].segment_id == "seg-1"
        assert commentary.segments[0].content == "First segment contentSecond segment content"


@pytest.mark.asyncio
async def test_filter_segment_mapping_by_type_no_matching_type():
    """Test that filtering returns empty list when no segments match the requested type."""
    text_id = "version-text-1"
    segments = [
        SegmentDTO(
            id="seg-1",
            text_id=text_id,
            content="Version content",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
    ]
    text_details = {
        text_id: TextDTO(
            id=text_id,
            title="Version Title",
            language="en",
            type="version",
            group_id="g1",
            is_published=True,
            created_date="",
            updated_date="",
            published_date="",
            published_by="",
            categories=[],
            views=0,
        )
    }

    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details):
        # Request commentary but only version exists
        result = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments, type="commentary")
        
        # Should return empty list
        assert len(result) == 0
        assert result == []


@pytest.mark.asyncio
async def test_filter_segment_mapping_by_type_with_text_id_filter():
    """Test filtering by both type and specific text_id."""
    commentary_text_id_1 = "commentary-1"
    commentary_text_id_2 = "commentary-2"
    
    segments = [
        SegmentDTO(
            id="seg-1",
            text_id=commentary_text_id_1,
            content="Commentary 1 content",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
        SegmentDTO(
            id="seg-2",
            text_id=commentary_text_id_2,
            content="Commentary 2 content",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
    ]
    
    text_details = {
        commentary_text_id_1: TextDTO(
            id=commentary_text_id_1,
            title="Commentary One",
            language="bo",
            type="commentary",
            group_id="g1",
            is_published=True,
            created_date="",
            updated_date="",
            published_date="",
            published_by="",
            categories=[],
            views=0,
        ),
        commentary_text_id_2: TextDTO(
            id=commentary_text_id_2,
            title="Commentary Two",
            language="bo",
            type="commentary",
            group_id="g1",
            is_published=True,
            created_date="",
            updated_date="",
            published_date="",
            published_by="",
            categories=[],
            views=0,
        )
    }

    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details):
        # Filter by commentary type AND specific text_id
        result = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(
            segments, 
            type="commentary",
            text_id=commentary_text_id_1
        )
        
        # Should return only 1 commentary matching the text_id
        assert len(result) == 1
        assert isinstance(result[0], SegmentCommentry)
        assert result[0].text_id == commentary_text_id_1
        assert result[0].title == "Commentary One"
        assert len(result[0].segments) == 1
        assert result[0].segments[0].segment_id == "seg-1"


@pytest.mark.asyncio
async def test_filter_segment_mapping_by_type_multiple_segments_same_text_grouped():
    """Test that multiple segments from same text_id are properly grouped with correct count."""
    text_id = "commentary-grouped"
    
    segments = [
        SegmentDTO(
            id="seg-1",
            text_id=text_id,
            content="Content 1",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
        SegmentDTO(
            id="seg-2",
            text_id=text_id,
            content="Content 2",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
        SegmentDTO(
            id="seg-3",
            text_id=text_id,
            content="Content 3",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
    ]
    
    text_details = {
        text_id: TextDTO(
            id=text_id,
            title="Grouped Commentary",
            language="bo",
            type="commentary",
            group_id="g1",
            is_published=True,
            created_date="",
            updated_date="",
            published_date="",
            published_by="",
            categories=[],
            views=0,
        )
    }

    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details):
        result = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments, type="commentary")
        
        # Should return 1 grouped commentary
        assert len(result) == 1
        commentary = result[0]
        
        # Verify segments are merged into a single MappedSegmentDTO
        # The implementation merges all content from the same text_id into one segment
        assert len(commentary.segments) == 1
        assert commentary.count == 1
        
        # Verify merged segment has first segment's ID and concatenated content
        assert commentary.segments[0].segment_id == "seg-1"
        assert commentary.segments[0].content == "Content 1Content 2Content 3"


@pytest.mark.asyncio
async def test_mapped_segment_content_for_table_of_content_with_version_id_success():
    table_of_content = TableOfContent(
        id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        text_id="5f3c2e9d-9b7a-4f5e-8e2a-6a8b7c9d4e0f",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="123e4567-e89b-12d3-a456-426614174000",
                title="title",
                section_number=1,
                parent_id=None,
                segments=[
                    TextSegment(
                        segment_id="root-seg-1",
                        segment_number=1
                    )
                ],
                sections=[],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )
    version_id = "version-text-1"

    # Root/source segment content
    root_segment = SegmentDTO(
        id="root-seg-1",
        text_id="root-text-1",
        content="source content",
        mapping=[],
        type=SegmentType.SOURCE
    )

    # Related mapped segments include a version mapped to the root segment
    related_mapped_segments = [
        SegmentDTO(
            id=str(uuid4()),
            text_id=version_id,
            content="translated content",
            mapping=[],
            type=SegmentType.SOURCE
        )
    ]

    # Text details for the version (used by filter and for language)
    version_text_detail = TextDTO(
        id=version_id,
        title="Version Title",
        language="en",
        type="version",
        group_id="group-id",
        is_published=True,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=["cat"],
        views=0
    )

    with patch("pecha_api.texts.segments.segments_utils.get_segment_by_id", new_callable=AsyncMock, return_value=root_segment), \
        patch("pecha_api.texts.segments.segments_utils.get_related_mapped_segments", new_callable=AsyncMock, return_value=related_mapped_segments), \
        patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value={version_id: version_text_detail}), \
        patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=version_text_detail):
        response = await SegmentUtils.get_mapped_segment_content_for_table_of_content(table_of_content=table_of_content, version_id=version_id)

        assert isinstance(response, DetailTableOfContent)
        seg = response.sections[0].segments[0]
        assert seg.segment_id == "root-seg-1"
        assert seg.content == "source content"
        assert seg.translation is not None
        assert seg.translation.text_id == version_id
        assert seg.translation.language == "en"
        assert seg.translation.content == "translated content"


@pytest.mark.asyncio
async def test_validate_segment_exists_not_found_raises_404():
    with patch("pecha_api.texts.segments.segments_utils.check_segment_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segment_exists(segment_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64")
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_validate_segment_exists_success():
    with patch("pecha_api.texts.segments.segments_utils.check_segment_exists", new_callable=AsyncMock, return_value=True):
        assert await SegmentUtils.validate_segment_exists(segment_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64") is True


@pytest.mark.asyncio
async def test_validate_segments_exists_not_found_raises_404():
    with patch("pecha_api.texts.segments.segments_utils.check_all_segment_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segments_exists(segment_ids=[
                "efb26a06-f373-450b-ba57-e7a8d4dd5b64",
                "efb26a06-f373-450b-ba57-e7a8d4dd5b65",
            ])
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_validate_segments_exists_success():
    with patch("pecha_api.texts.segments.segments_utils.check_all_segment_exists", new_callable=AsyncMock, return_value=True):
        assert await SegmentUtils.validate_segments_exists(segment_ids=[
            "efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            "efb26a06-f373-450b-ba57-e7a8d4dd5b65",
        ]) is True



@pytest.mark.asyncio
async def test_group_segment_content_by_text_id_with_table_of_contents():
    """Test _group_segment_content_by_text_id groups and sorts segments correctly using TOC."""
    text_id = "text-id-1"
    
    # Create segments in random order
    segments = [
        SegmentDTO(
            id="seg-3",
            text_id=text_id,
            content="Third segment",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
        SegmentDTO(
            id="seg-1",
            text_id=text_id,
            content="First segment",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
        SegmentDTO(
            id="seg-2",
            text_id=text_id,
            content="Second segment",
            mapping=[],
            type=SegmentType.SOURCE,
        ),
    ]
    
    # Create a table of contents with segment order
    table_of_contents = [
        TableOfContent(
            id="toc-1",
            text_id=text_id,
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section-1",
                    title="Section 1",
                    section_number=1,
                    parent_id=None,
                    segments=[
                        TextSegment(segment_id="seg-1", segment_number=1),
                        TextSegment(segment_id="seg-2", segment_number=2),
                        TextSegment(segment_id="seg-3", segment_number=3),
                    ],
                    sections=[],
                    created_date="",
                    updated_date="",
                    published_date=""
                )
            ]
        )
    ]
    
    with patch("pecha_api.texts.segments.segments_utils.get_contents_by_text_ids", new_callable=AsyncMock, return_value={text_id: table_of_contents}):
        result = await SegmentUtils._group_segment_content_by_text_id(segments)
        
        # Check that segments are grouped by text_id
        assert text_id in result
        assert len(result[text_id]) == 3
        
        # Check that segments are ordered correctly according to TOC
        assert result[text_id][0].id == "seg-1"
        assert result[text_id][1].id == "seg-2"
        assert result[text_id][2].id == "seg-3"


@pytest.mark.asyncio
async def test_group_segment_content_by_text_id_fallback_to_pecha_id():
    """Test _group_segment_content_by_text_id falls back to pecha_segment_id when TOC fails."""
    text_id = "text-id-1"
    
    # Create segments with pecha_segment_id
    segments = [
        SegmentDTO(
            id="seg-c",
            text_id=text_id,
            content="Third segment",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="03"
        ),
        SegmentDTO(
            id="seg-a",
            text_id=text_id,
            content="First segment",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="01"
        ),
        SegmentDTO(
            id="seg-b",
            text_id=text_id,
            content="Second segment",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="02"
        ),
    ]
    
    # Mock get_contents_by_text_ids to raise an exception (simulating failure)
    with patch("pecha_api.texts.segments.segments_utils.get_contents_by_text_ids", new_callable=AsyncMock, side_effect=Exception("TOC not found")):
        result = await SegmentUtils._group_segment_content_by_text_id(segments)
        
        # Check that segments are grouped
        assert text_id in result
        assert len(result[text_id]) == 3
        
        # Check that segments are sorted by pecha_segment_id
        assert result[text_id][0].pecha_segment_id == "01"
        assert result[text_id][1].pecha_segment_id == "02"
        assert result[text_id][2].pecha_segment_id == "03"


@pytest.mark.asyncio
async def test_group_segment_content_by_text_id_multiple_text_ids():
    """Test _group_segment_content_by_text_id handles multiple text_ids correctly."""
    text_id_1 = "text-id-1"
    text_id_2 = "text-id-2"
    
    segments = [
        SegmentDTO(
            id="seg-1-1",
            text_id=text_id_1,
            content="Text 1 Segment 1",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="01"
        ),
        SegmentDTO(
            id="seg-2-1",
            text_id=text_id_2,
            content="Text 2 Segment 1",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="01"
        ),
        SegmentDTO(
            id="seg-1-2",
            text_id=text_id_1,
            content="Text 1 Segment 2",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="02"
        ),
    ]
    
    with patch("pecha_api.texts.segments.segments_utils.get_contents_by_text_ids", new_callable=AsyncMock, side_effect=Exception("TOC not found")):
        result = await SegmentUtils._group_segment_content_by_text_id(segments)
        
        # Check that both text_ids are present
        assert text_id_1 in result
        assert text_id_2 in result
        
        # Check correct grouping
        assert len(result[text_id_1]) == 2
        assert len(result[text_id_2]) == 1
        
        # Check segments are in correct groups
        assert all(seg.text_id == text_id_1 for seg in result[text_id_1])
        assert all(seg.text_id == text_id_2 for seg in result[text_id_2])


@pytest.mark.asyncio
async def test_group_segment_content_by_text_id_nested_sections():
    """Test _group_segment_content_by_text_id handles nested sections in TOC."""
    text_id = "text-id-1"
    
    segments = [
        SegmentDTO(id="seg-3", text_id=text_id, content="Third", mapping=[], type=SegmentType.SOURCE),
        SegmentDTO(id="seg-1", text_id=text_id, content="First", mapping=[], type=SegmentType.SOURCE),
        SegmentDTO(id="seg-2", text_id=text_id, content="Second", mapping=[], type=SegmentType.SOURCE),
    ]
    
    # Create TOC with nested sections
    table_of_contents = [
        TableOfContent(
            id="toc-1",
            text_id=text_id,
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section-1",
                    title="Parent Section",
                    section_number=1,
                    parent_id=None,
                    segments=[
                        TextSegment(segment_id="seg-1", segment_number=1),
                    ],
                    sections=[
                        Section(
                            id="section-1-1",
                            title="Nested Section",
                            section_number=1,
                            parent_id="section-1",
                            segments=[
                                TextSegment(segment_id="seg-2", segment_number=1),
                                TextSegment(segment_id="seg-3", segment_number=2),
                            ],
                            sections=[],
                            created_date="",
                            updated_date="",
                            published_date=""
                        )
                    ],
                    created_date="",
                    updated_date="",
                    published_date=""
                )
            ]
        )
    ]
    
    with patch("pecha_api.texts.segments.segments_utils.get_contents_by_text_ids", new_callable=AsyncMock, return_value={text_id: table_of_contents}):
        result = await SegmentUtils._group_segment_content_by_text_id(segments)
        
        # Check segments are correctly ordered from nested sections
        assert len(result[text_id]) == 3
        assert result[text_id][0].id == "seg-1"
        assert result[text_id][1].id == "seg-2"
        assert result[text_id][2].id == "seg-3"


@pytest.mark.asyncio
async def test_filter_segment_mapping_uses_grouped_segments():
    """Test that filter_segment_mapping_by_type_or_text_id correctly uses grouped segments."""
    text_id = "commentary-text-1"
    
    # Create segments that should be grouped and merged
    segments = [
        SegmentDTO(
            id="seg-2",
            text_id=text_id,
            content=" content 2",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="02"
        ),
        SegmentDTO(
            id="seg-1",
            text_id=text_id,
            content="content 1",
            mapping=[],
            type=SegmentType.SOURCE,
            pecha_segment_id="01"
        ),
    ]
    
    text_details = {
        text_id: TextDTO(
            id=text_id,
            title="Commentary",
            language="bo",
            type="commentary",
            group_id="g1",
            is_published=True,
            created_date="",
            updated_date="",
            published_date="",
            published_by="",
            categories=[],
            views=0,
        )
    }
    
    # Mock to ensure segments are sorted
    with patch("pecha_api.texts.segments.segments_utils.TextUtils.get_text_details_by_ids", new_callable=AsyncMock, return_value=text_details), \
         patch("pecha_api.texts.segments.segments_utils.get_contents_by_text_ids", new_callable=AsyncMock, side_effect=Exception("TOC not found")):
        
        result = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments, type="commentary")
        
        # Verify segments are merged in correct order (sorted by pecha_segment_id)
        assert len(result) == 1
        assert result[0].segments[0].content == "content 1 content 2"