import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from pecha_api.texts.texts_utils import TextUtils
from pecha_api.error_contants import ErrorConstants

from typing import List, Dict, Union

from pecha_api.texts.texts_response_models import (
    TextDTO,
    TableOfContent,
    TableOfContentType,
    Section,
    TextSegment
)

from pecha_api.texts.groups.groups_response_models import GroupDTO
from pecha_api.texts.texts_enums import TextType, TextTypes


@pytest.mark.asyncio
async def test_get_text_details_by_ids_success():
    text_details_dict = {
        "efb26a06-f373-450b-ba57-e7a8d4dd5b64": TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            title="title",
            language="language",
            group_id="group_id",
            type="type",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
    }
    with patch("pecha_api.texts.texts_utils.get_texts_by_ids", new_callable=AsyncMock, return_value=text_details_dict):
        response = await TextUtils.get_text_details_by_ids(text_ids=["efb26a06-f373-450b-ba57-e7a8d4dd5b64"])
        assert response.get("efb26a06-f373-450b-ba57-e7a8d4dd5b64") == text_details_dict.get("efb26a06-f373-450b-ba57-e7a8d4dd5b64")

@pytest.mark.asyncio
async def test_get_text_details_by_id_success():
    text_details = TextDTO(
        id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        title="title",
        language="language",
        group_id="group_id",
        type="type",
        is_published=True,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=["categories"],
        views=0
    )
    with patch("pecha_api.texts.texts_utils.get_texts_by_id", new_callable=AsyncMock, return_value=text_details),\
        patch("pecha_api.texts.texts_utils.check_text_exists", new_callable=AsyncMock, return_value=True),\
        patch("pecha_api.texts.texts_utils.get_text_details_by_id_cache", new_callable=AsyncMock, return_value=None),\
        patch("pecha_api.texts.texts_utils.set_text_details_by_id_cache", new_callable=AsyncMock, return_value=None):
        response = await TextUtils.get_text_details_by_id(text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64")
        assert response.id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
        assert response.title == "title"
        assert response.language == "language"
        assert response.type == "type"
        assert response.is_published == True
        assert response.categories == ["categories"]
        
@pytest.mark.asyncio
async def test_get_text_details_by_id_from_cache():
    """Test that get_text_details_by_id returns cached data when available."""
    cached_text_details = TextDTO(
        id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        title="cached_title",
        language="cached_language",
        group_id="group_id",
        type="type",
        is_published=True,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=["categories"],
        views=0
    )
    with patch("pecha_api.texts.texts_utils.get_text_details_by_id_cache", new_callable=AsyncMock, return_value=cached_text_details):
        response = await TextUtils.get_text_details_by_id(text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64")
        assert response.id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
        assert response.title == "cached_title"
        assert response.language == "cached_language"


@pytest.mark.asyncio
async def test_get_text_details_by_id_not_found():
    """Test that get_text_details_by_id raises HTTPException when text doesn't exist."""
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.texts_utils.get_text_details_by_id_cache", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.texts.texts_utils.check_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await TextUtils.get_text_details_by_id(text_id=text_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE
        
@pytest.mark.asyncio
async def test_validate_text_exists_success():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.texts_utils.check_text_exists", new_callable=AsyncMock, return_value=True):
        response = await TextUtils.validate_text_exists(text_id=text_id)
        assert response == True

@pytest.mark.asyncio
async def test_validate_text_exists_invalid_text_id():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.texts_utils.check_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await TextUtils.validate_text_exists(text_id=text_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE
        
@pytest.mark.asyncio
async def test_validate_texts_exist_success():
    text_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch("pecha_api.texts.texts_utils.check_all_text_exists", new_callable=AsyncMock, return_value=True):
        response = await TextUtils.validate_texts_exist(text_ids=text_ids)
        assert response == True
        
@pytest.mark.asyncio
async def test_validate_texts_exist_invalid_text_id():
    text_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch("pecha_api.texts.texts_utils.check_all_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await TextUtils.validate_texts_exist(text_ids=text_ids)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_get_text_detail_by_id_success():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    text = TextDTO(
        id=text_id,
        title="title",
        language="language",
        group_id="group_id",
        type="type",
        is_published=True,
        created_date="created_date",
        updated_date="updated_date",
        published_date="published_date",
        published_by="published_by",
        categories=["categories"],
        views=0
    )
    with patch("pecha_api.texts.texts_utils.get_texts_by_id", new_callable=AsyncMock, return_value=text):
        response = await TextUtils.get_text_detail_by_id(text_id=text_id)
        assert response.id == text_id
        assert response.title == "title"
        assert response.language == "language"
        assert response.type == "type"
        assert response.is_published == True
        assert response.created_date == "created_date"
        assert response.updated_date == "updated_date"
        assert response.published_date == "published_date"
        assert response.published_by == "published_by"
        assert response.categories == ["categories"]

@pytest.mark.asyncio
async def test_get_text_detail_by_id_empty_text_id():
    text_id = None
    with pytest.raises(HTTPException) as exc_info:
        await TextUtils.get_text_detail_by_id(text_id=text_id)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == ErrorConstants.TEXT_OR_TERM_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_get_text_detail_by_id_invalid_text_id():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.texts_utils.get_texts_by_id", new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            await TextUtils.get_text_detail_by_id(text_id=text_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_get_table_of_content_id_and_respective_section_by_segment_id_success():
    list_of_table_of_content = [
        TableOfContent(
            id="123e4567-e89b-12d3-a456-426614174000",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="123e4567-e89b-12d3-a456-426614174001",
                    title="title",
                    section_number=1,
                    parent_id="123e4567-e89b-12d3-a456-426614174000",
                    segments=[
                        TextSegment(
                            segment_id="123e4567-e89b-12d3-a456-426614174002",
                            segment_number=1
                        )
                    ],
                    created_date="created_date",
                    updated_date="updated_date",
                    published_date="published_date"
                )
            ]
        )
    ]
    with patch("pecha_api.texts.texts_utils.get_contents_by_id", new_callable=AsyncMock, return_value=list_of_table_of_content):
        response = await TextUtils.get_table_of_content_id_and_respective_section_by_segment_id(text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64", segment_id="123e4567-e89b-12d3-a456-426614174002")
        assert isinstance(response, TableOfContent)
        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.text_id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
        assert response.sections[0].id == "123e4567-e89b-12d3-a456-426614174001"
        assert response.sections[0].title == "title"
        assert response.sections[0].section_number == 1
        assert response.sections[0].parent_id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.sections[0].segments[0].segment_id == "123e4567-e89b-12d3-a456-426614174002"
        assert response.sections[0].segments[0].segment_number == 1


@pytest.mark.asyncio
async def test_get_table_of_content_id_and_respective_section_by_segment_id_where_segment_id_not_found_in_table_of_content():
    list_of_table_of_content = [
        TableOfContent(
            id="123e4567-e89b-12d3-a456-426614174000",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="123e4567-e89b-12d3-a456-426614174001",
                    title="title",
                    section_number=1,
                    parent_id="123e4567-e89b-12d3-a456-426614174000",
                    segments=[
                        TextSegment(
                            segment_id="123e4567-e89b-12d3-a456-426614174002",
                            segment_number=1
                        )
                    ],
                    created_date="created_date",
                    updated_date="updated_date",
                    published_date="published_date"
                )
            ]
        )
    ]
    with patch("pecha_api.texts.texts_utils.get_contents_by_id", new_callable=AsyncMock, return_value=list_of_table_of_content):
        response = await TextUtils.get_table_of_content_id_and_respective_section_by_segment_id(text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64", segment_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64")
        assert response is None
        

def test_get_language_priority():
    """Test get_language_priority returns correct priority values for Tibetan preference"""
    # Test with Tibetan preferred language
    assert TextUtils.get_language_priority("bo", "bo") == 0
    assert TextUtils.get_language_priority("en", "bo") == 1
    assert TextUtils.get_language_priority("zh", "bo") == 2
    assert TextUtils.get_language_priority("unknown", "bo") == 999
    
    # Test with English preferred language
    assert TextUtils.get_language_priority("en", "en") == 0
    assert TextUtils.get_language_priority("bo", "en") == 1
    assert TextUtils.get_language_priority("zh", "en") == 2
    assert TextUtils.get_language_priority("unknown", "en") == 999
    
    # Test with Chinese preferred language
    assert TextUtils.get_language_priority("zh", "zh") == 0
    assert TextUtils.get_language_priority("en", "zh") == 1
    assert TextUtils.get_language_priority("bo", "zh") == 2
    assert TextUtils.get_language_priority("unknown", "zh") == 999

def test_get_language_priority_with_none():
    """Test get_language_priority handles None text_language"""
    assert TextUtils.get_language_priority(None, "bo") == 999
    assert TextUtils.get_language_priority(None, "en") == 999
    assert TextUtils.get_language_priority(None, "zh") == 999

@pytest.mark.asyncio
async def test_filter_text_on_root_and_version():
    mock_texts: List[TextDTO] = [
        TextDTO(
            id=f"efb26a06-f373-450b-ba57-e7a8d4dd5b6{i}",
            title=f"en_{i}",
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
        )
        for i in range(1,3)
    ]
    mock_texts.append(
        TextDTO(
            id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            title="bo_1",
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
    )
    response: Dict[str, Union[TextDTO, List[TextDTO]]] = TextUtils.filter_text_on_root_and_version(texts=mock_texts, language="bo")
    assert response is not None
    assert response[TextType.ROOT_TEXT.value] is not None
    assert isinstance(response[TextType.ROOT_TEXT.value], TextDTO)
    assert response[TextType.ROOT_TEXT.value].language == "bo"
    assert response[TextType.ROOT_TEXT.value].id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    assert response[TextType.ROOT_TEXT.value].title == "bo_1"
    assert response[TextTypes.VERSIONS.value] is not None
    assert len(response[TextTypes.VERSIONS.value]) == 2
    index = 0
    assert response[TextTypes.VERSIONS.value][index] is not None
    assert response[TextTypes.VERSIONS.value][index].language == "en"
    assert response[TextTypes.VERSIONS.value][index].id == "efb26a06-f373-450b-ba57-e7a8d4dd5b61"
    
@pytest.mark.asyncio
async def test_filter_text_base_on_group_id_type():
    mock_texts = _generate_mock_texts_version_and_commentary()
    mock_groups = _generate_mock_groups_version_and_commentary(mock_texts=mock_texts)
    with patch("pecha_api.texts.texts_utils.get_groups_by_list_of_ids", new_callable=AsyncMock, return_value=mock_groups):
        response = await TextUtils.filter_text_base_on_group_id_type(texts=mock_texts, language="en")
        response is not None
        assert response[TextType.ROOT_TEXT.value] is not None
        assert response[TextType.ROOT_TEXT.value].id == "ce14bedb-a4ca-402f-b7a0-cbb33efe5181"
        assert response[TextType.ROOT_TEXT.value].language == "en"
        assert response[TextType.ROOT_TEXT.value].type == "version"
        
        assert response[TextType.COMMENTARY.value] is not None
        assert len(response[TextType.COMMENTARY.value]) == 0
        for text_commentary in response[TextType.COMMENTARY.value]:
            assert text_commentary.type == "commentary"


def test_get_all_segment_ids_single_level():
    """Test get_all_segment_ids extracts segment IDs from single-level sections."""
    table_of_content = TableOfContent(
        id="toc-1",
        text_id="text-1",
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
                ],
                sections=[],
                created_date="",
                updated_date="",
                published_date=""
            ),
            Section(
                id="section-2",
                title="Section 2",
                section_number=2,
                parent_id=None,
                segments=[
                    TextSegment(segment_id="seg-3", segment_number=1),
                ],
                sections=[],
                created_date="",
                updated_date="",
                published_date=""
            )
        ]
    )
    
    result = TextUtils.get_all_segment_ids(table_of_content)
    
    # Note: order depends on stack implementation (LIFO), so we check set membership
    assert len(result) == 3
    assert set(result) == {"seg-1", "seg-2", "seg-3"}


def test_get_all_segment_ids_nested_sections():
    """Test get_all_segment_ids extracts segment IDs from nested sections."""
    table_of_content = TableOfContent(
        id="toc-1",
        text_id="text-1",
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
    
    result = TextUtils.get_all_segment_ids(table_of_content)
    
    assert len(result) == 3
    assert set(result) == {"seg-1", "seg-2", "seg-3"}


def test_get_all_segment_ids_empty_sections():
    """Test get_all_segment_ids handles empty sections."""
    table_of_content = TableOfContent(
        id="toc-1",
        text_id="text-1",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section-1",
                title="Empty Section",
                section_number=1,
                parent_id=None,
                segments=[],
                sections=[],
                created_date="",
                updated_date="",
                published_date=""
            )
        ]
    )
    
    result = TextUtils.get_all_segment_ids(table_of_content)
    
    assert len(result) == 0
    assert result == []


def test_get_all_segment_ids_deeply_nested():
    """Test get_all_segment_ids with deeply nested sections."""
    table_of_content = TableOfContent(
        id="toc-1",
        text_id="text-1",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section-1",
                title="Level 1",
                section_number=1,
                parent_id=None,
                segments=[TextSegment(segment_id="seg-1", segment_number=1)],
                sections=[
                    Section(
                        id="section-2",
                        title="Level 2",
                        section_number=1,
                        parent_id="section-1",
                        segments=[TextSegment(segment_id="seg-2", segment_number=1)],
                        sections=[
                            Section(
                                id="section-3",
                                title="Level 3",
                                section_number=1,
                                parent_id="section-2",
                                segments=[TextSegment(segment_id="seg-3", segment_number=1)],
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
                ],
                created_date="",
                updated_date="",
                published_date=""
            )
        ]
    )
    
    result = TextUtils.get_all_segment_ids(table_of_content)
    
    assert len(result) == 3
    assert set(result) == {"seg-1", "seg-2", "seg-3"}
    


def _generate_mock_texts_version_and_commentary() -> List[TextDTO]:
    mock_commentary_texts: List[TextDTO] = [
        TextDTO(
            id=f"05c36f8b-95cd-4698-bc97-ba4958b2d55{i}",
            title=f"bo_{i}",
            language="bo",
            group_id=f"05c36f8b-95cd-4698-bc97-ba4958b2d55{i}",
            type="commentary",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
        for i in range(1, 6)
    ]
    mock_version_texts: List[TextDTO] = [
        TextDTO(
            id=f"ce14bedb-a4ca-402f-b7a0-cbb33efe518{i}",
            title=f"en_{i}",
            language="en",
            group_id=f"ce14bedb-a4ca-402f-b7a0-cbb33efe518{i}",
            type="version",
            is_published=True,
            created_date="created_date",
            updated_date="updated_date",
            published_date="published_date",
            published_by="published_by",
            categories=["categories"],
            views=0
        )
        for i in range(1, 3)
    ]
    return mock_commentary_texts + mock_version_texts

def _generate_mock_groups_version_and_commentary(mock_texts: List[TextDTO]) -> Dict[str, GroupDTO]:
    mock_groups: Dict[str, GroupDTO] = {}
    for text in mock_texts:
        mock_groups[text.id] = GroupDTO(
            id=text.group_id,
            type="text" if text.type == "version" else "commentary"
        )
    return mock_groups


@pytest.mark.asyncio
async def test_get_commentaries_by_text_type_success():
    """Test get_commentaries_by_text_type returns commentary texts."""
    from uuid import UUID
    
    # Create mock text data as plain objects (not actual Text model instances)
    class MockText:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    mock_text_1 = MockText(
        id=UUID("efb26a06-f373-450b-ba57-e7a8d4dd5b64"),
        pecha_text_id="pecha-1",
        title="Commentary One",
        language="bo",
        group_id="g1",
        type="commentary",
        is_published=True,
        created_date="2024-01-01",
        updated_date="2024-01-01",
        published_date="2024-01-01",
        published_by="Publisher",
        categories=["cat1"],
        views=10,
        source_link="http://example.com",
        ranking=5,
        license="MIT"
    )
    
    mock_text_2 = MockText(
        id=UUID("efb26a06-f373-450b-ba57-e7a8d4dd5b65"),
        pecha_text_id="pecha-2",
        title="Commentary Two",
        language="en",
        group_id="g2",
        type="commentary",
        is_published=True,
        created_date="2024-01-02",
        updated_date="2024-01-02",
        published_date="2024-01-02",
        published_by="Publisher 2",
        categories=["cat2"],
        views=20,
        source_link="http://example2.com",
        ranking=4,
        license="Apache"
    )
    
    mock_texts = [mock_text_1, mock_text_2]
    
    # Mock the Text.find method at the module level
    with patch("pecha_api.texts.texts_utils.Text.find") as mock_find:
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_texts)
        mock_find.return_value = mock_cursor
        
        result = await TextUtils.get_commentaries_by_text_type(
            text_type="commentary",
            language="bo",
            skip=0,
            limit=10
        )
        
        # Verify the result
        assert len(result) == 2
        assert all(isinstance(text, TextDTO) for text in result)
        assert result[0].id == "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
        assert result[0].title == "Commentary One"
        assert result[0].language == "bo"
        assert result[0].type == "commentary"
        assert result[1].id == "efb26a06-f373-450b-ba57-e7a8d4dd5b65"
        assert result[1].title == "Commentary Two"
        
        # Verify the find method was called correctly
        mock_find.assert_called_once_with({"type": "commentary"})


@pytest.mark.asyncio
async def test_get_commentaries_by_text_type_empty_result():
    """Test get_commentaries_by_text_type returns empty list when no commentaries found."""
    # Mock the Text.find method at the module level to return empty list
    with patch("pecha_api.texts.texts_utils.Text.find") as mock_find:
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_find.return_value = mock_cursor
        
        result = await TextUtils.get_commentaries_by_text_type(
            text_type="commentary",
            language="bo",
            skip=0,
            limit=10
        )
        
        # Verify empty result
        assert len(result) == 0
        assert result == []
        mock_find.assert_called_once_with({"type": "commentary"})


@pytest.mark.asyncio
async def test_filter_text_base_on_group_id_type_and_language_preference_with_sorted_texts():
    """Test filter_text_base_on_group_id_type_and_language_preference picks first text regardless of language match"""
    # Create mock texts already sorted by language preference
    mock_texts = [
        TextDTO(
            id="text_id_1",
            title="English Text",
            language="en",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="Tibetan Text",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        )
    ]
    
    mock_groups = {
        "group_1": GroupDTO(
            id="group_1",
            type="text"
        )
    }
    
    with patch("pecha_api.texts.texts_utils.get_groups_by_list_of_ids", new_callable=AsyncMock, return_value=mock_groups):
        result = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(
            texts=mock_texts,
            language="bo"
        )
        
        # Should pick the first text (en) since texts are already sorted
        assert result is not None
        assert result[TextType.ROOT_TEXT.value] is not None
        assert result[TextType.ROOT_TEXT.value].id == "text_id_1"
        assert result[TextType.ROOT_TEXT.value].language == "en"
        assert len(result["commentary"]) == 0


@pytest.mark.asyncio
async def test_filter_text_base_on_group_id_type_and_language_preference_with_commentary():
    """Test filter_text_base_on_group_id_type_and_language_preference separates text and commentary"""
    mock_texts = [
        TextDTO(
            id="text_id_1",
            title="Root Text",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="Commentary Text",
            language="bo",
            group_id="group_2",
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        )
    ]
    
    mock_groups = {
        "group_1": GroupDTO(
            id="group_1",
            type="text"
        ),
        "group_2": GroupDTO(
            id="group_2",
            type="commentary"
        )
    }
    
    with patch("pecha_api.texts.texts_utils.get_groups_by_list_of_ids", new_callable=AsyncMock, return_value=mock_groups):
        result = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(
            texts=mock_texts,
            language="bo"
        )
        
        assert result is not None
        assert result[TextType.ROOT_TEXT.value] is not None
        assert result[TextType.ROOT_TEXT.value].id == "text_id_1"
        assert len(result[TextType.COMMENTARY.value]) == 1
        assert result[TextType.COMMENTARY.value][0].id == "text_id_2"
        assert result[TextType.COMMENTARY.value][0].type == "commentary"


@pytest.mark.asyncio
async def test_filter_text_base_on_group_id_type_and_language_preference_empty_texts():
    """Test filter_text_base_on_group_id_type_and_language_preference with empty texts"""
    result = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(
        texts=[],
        language="bo"
    )
    
    assert result is not None
    assert result[TextType.ROOT_TEXT.value] is None
    assert len(result["commentary"]) == 0


@pytest.mark.asyncio
async def test_filter_text_base_on_group_id_type_and_language_preference_excludes_excluded_ids():
    """Test filter_text_base_on_group_id_type_and_language_preference excludes texts in Constants.excluded_text_ids"""
    from pecha_api.constants import Constants
    
    excluded_id = "excluded_id_test"
    mock_texts = [
        TextDTO(
            id=excluded_id,
            title="Excluded Text",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="Valid Text",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        )
    ]
    
    mock_groups = {
        "group_1": GroupDTO(
            id="group_1",
            type="text"
        )
    }
    
    with patch("pecha_api.texts.texts_utils.get_groups_by_list_of_ids", new_callable=AsyncMock, return_value=mock_groups), \
         patch("pecha_api.constants.Constants.excluded_text_ids", [excluded_id]):
        result = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(
            texts=mock_texts,
            language="bo"
        )
        
        # Should pick the second text, not the excluded one
        assert result is not None
        assert result[TextType.ROOT_TEXT.value] is not None
        assert result[TextType.ROOT_TEXT.value].id == "text_id_2"


@pytest.mark.asyncio
async def test_filter_text_base_on_group_id_type_and_language_preference_no_language_filtering():
    """Test filter_text_base_on_group_id_type_and_language_preference doesn't filter by language for root text"""
    # This test confirms that the function picks the first text regardless of language
    # as long as it's the correct type
    mock_texts = [
        TextDTO(
            id="text_id_1",
            title="English Text",
            language="en",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="Tibetan Text",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        )
    ]
    
    mock_groups = {
        "group_1": GroupDTO(
            id="group_1",
            type="text"
        )
    }
    
    with patch("pecha_api.texts.texts_utils.get_groups_by_list_of_ids", new_callable=AsyncMock, return_value=mock_groups):
        result = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(
            texts=mock_texts,
            language="bo"  # Requesting 'bo' but should get 'en' since it's first
        )
        
        # Should pick the first text (English) not the Tibetan one
        assert result is not None
        assert result[TextType.ROOT_TEXT.value] is not None
        assert result[TextType.ROOT_TEXT.value].id == "text_id_1"
        assert result[TextType.ROOT_TEXT.value].language == "en"


@pytest.mark.asyncio
async def test_filter_text_base_on_group_id_type_and_language_preference_filters_commentary_by_language():
    """Test filter_text_base_on_group_id_type_and_language_preference filters commentaries by language"""
    mock_texts = [
        TextDTO(
            id="text_id_1",
            title="Root Text",
            language="bo",
            group_id="group_1",
            type="version",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="Bo Commentary",
            language="bo",
            group_id="group_2",
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        ),
        TextDTO(
            id="text_id_3",
            title="En Commentary",
            language="en",
            group_id="group_3",
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["categories"],
            views=0
        )
    ]
    
    mock_groups = {
        "group_1": GroupDTO(
            id="group_1",
            type="text"
        ),
        "group_2": GroupDTO(
            id="group_2",
            type="commentary"
        ),
        "group_3": GroupDTO(
            id="group_3",
            type="commentary"
        )
    }
    
    with patch("pecha_api.texts.texts_utils.get_groups_by_list_of_ids", new_callable=AsyncMock, return_value=mock_groups):
        result = await TextUtils.filter_text_base_on_group_id_type_and_language_preference(
            texts=mock_texts,
            language="bo"
        )
        
        # Should only include Tibetan commentary, not English
        assert result is not None
        assert result[TextType.ROOT_TEXT.value] is not None
        assert len(result[TextType.COMMENTARY.value]) == 1
        assert result[TextType.COMMENTARY.value][0].id == "text_id_2"
        assert result[TextType.COMMENTARY.value][0].language == "bo"
    