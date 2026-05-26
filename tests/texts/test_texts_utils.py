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
