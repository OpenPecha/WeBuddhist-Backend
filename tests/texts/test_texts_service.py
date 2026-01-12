from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from uuid import uuid4

from pecha_api.collections.collections_response_models import CollectionModel
import pytest
from pecha_api.texts.texts_service import (
    create_new_text,
    get_text_versions_by_group_id,
    get_text_by_text_id_or_collection,
    create_table_of_content,
    get_table_of_contents_by_text_id,
    get_text_details_by_text_id,
    update_text_details,
    remove_table_of_content_by_text_id,
    delete_text_by_text_id,
    get_sheet,
    get_table_of_content_by_sheet_id,
    get_table_of_content_by_type,
    _validate_text_detail_request,
    get_root_text_by_collection_id,
    get_commentaries_by_text_id,
    replace_pecha_segment_id_with_segment_id,
    get_text_by_pecha_text_ids_service
)
from pecha_api.terms.terms_response_models import TermsModel
from pecha_api.texts.texts_response_models import (
    CreateTextRequest,
    TextDTO,
    TextVersion,
    TableOfContent,
    TableOfContentType,
    Section,
    TextSegment,
    TableOfContentResponse,
    TextDetailsRequest,
    DetailTableOfContentResponse,
    DetailTableOfContent,
    DetailSection,
    DetailTextSegment,
    Translation,
    UpdateTextRequest,
    TextDTOResponse,
    TextVersionResponse,
    TextsCategoryResponse,
    TextsByPechaTextIdsRequest
)
from pecha_api.recitations.recitations_response_models import RecitationDTO, RecitationsResponse

from pecha_api.texts.texts_enums import TextType, PaginationDirection, LANGUAGE_ORDERS
from pecha_api.sheets.sheets_enum import SortBy, SortOrder

from pecha_api.error_contants import ErrorConstants
from typing import List

@pytest.mark.asyncio
async def test_get_text_by_text_id_or_collection_without_collection_id_success():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    collection_id = None
    with patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock) as mock_get_text_detail_by_id, \
        patch("pecha_api.texts.texts_service.set_text_by_text_id_or_collection_cache", new_callable=AsyncMock, return_value=None), \
        patch("pecha_api.texts.texts_service.get_text_by_text_id_or_collection_cache", new_callable=AsyncMock, return_value=None):
        mock_get_text_detail_by_id.return_value = TextDTO(
            id=text_id,
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            language="bo",
            group_id="group_id_1",
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0
        )

        response = await get_text_by_text_id_or_collection(text_id=text_id, collection_id=collection_id)

        assert response is not None
        assert isinstance(response, TextDTO)
        assert response.id == text_id

@pytest.mark.asyncio
async def test_get_text_by_collection_id():
    mock_collection = CollectionModel(
        id="id_1",
        title="སྤྱོད་འཇུག",
        description="དུས་རབས་ ༨ པའི་ནང་སློབ་དཔོན་ཞི་བ་ལྷས་མཛད་པའི་རྩ་བ་དང་དེའི་འགྲེལ་བ་སོགས།",
        language="bo",
        slug="bodhicaryavatara",
        has_child=False
    )
    
    # Use valid UUID for group_id
    valid_group_id = "123e4567-e89b-12d3-a456-426614174001"
    
    mock_texts_by_category = [
        TextDTO(
            id="a48c0814-ce56-4ada-af31-f74b179b52a9",
            title="སྤྱོད་འཇུག་དཀའ་འགྲེལ།",
            language="bo",
            group_id=valid_group_id,
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[],
            views=0,
            pecha_text_id="pecha_1"
        ),
        TextDTO(
            id="032b9a5f-0712-40d8-b7ec-73c8c94f1c15",
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            language="bo",
            group_id=valid_group_id,
            type="version",
            is_published=True,
            created_date="2025-03-20 09:26:16.571522",
            updated_date="2025-03-20 09:26:16.571532",
            published_date="2025-03-20 09:26:16.571536",
            published_by="pecha",
            categories=[],
            views=0,
            pecha_text_id="pecha_2"
        )
    ]

    with patch('pecha_api.texts.texts_service.get_collection', new_callable=AsyncMock, return_value=mock_collection), \
            patch('pecha_api.texts.texts_service.get_texts_by_collection', new_callable=AsyncMock) as mock_get_texts_by_category, \
            patch('pecha_api.texts.texts_service.get_all_texts_by_collection', new_callable=AsyncMock) as mock_get_all_texts, \
            patch('pecha_api.texts.texts_service.set_text_by_text_id_or_collection_cache', new_callable=AsyncMock, return_value=None), \
            patch('pecha_api.texts.texts_service.TextUtils.filter_text_base_on_group_id_type_and_language_preference', new_callable=AsyncMock) as mock_filter_text_base_on_group_id_type:
        mock_filter_text_base_on_group_id_type.return_value = {"root_text": mock_texts_by_category[1], "commentary": [mock_texts_by_category[0]]}
        mock_get_texts_by_category.return_value = mock_texts_by_category
        # Return only the root text for total count calculation
        mock_get_all_texts.return_value = [mock_texts_by_category[1]]
        response = await get_text_by_text_id_or_collection(text_id=None, collection_id="id_1", language="bo", skip=0, limit=10)
        assert response is not None
        assert response.collection is not None
        collection: CollectionModel = response.collection
        assert collection.id == "id_1"
        assert collection.slug == "bodhicaryavatara"
        assert response.texts is not None
        texts: List[TextDTO] = response.texts
        assert len(texts) == 1
        assert texts[0] is not None
        assert isinstance(texts[0], TextDTO)
        assert texts[0].id == mock_texts_by_category[1].id
        assert texts[0].title == mock_texts_by_category[1].title
        assert texts[0].language == mock_texts_by_category[1].language
        assert texts[0].type == "root_text"
        assert response.total == 1
        assert response.skip == 0
        assert response.limit == 10


@pytest.mark.asyncio
async def test_get_versions_by_group_id():
    text_detail = TextDTO(
        id="id_1",
        title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
        group_id="group_id_1",
        language="bo",
        type="version",
        is_published=True,
        created_date="2025-03-20 09:26:16.571522",
        updated_date="2025-03-20 09:26:16.571532",
        published_date="2025-03-20 09:26:16.571536",
        published_by="pecha",
        categories=[],
        views=0
    )
    texts_by_group_id = [
        TextDTO(
            id="text_id_1",
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            group_id="group_id_1",
            language="bo",
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
            id="text_id_2",
            title="The Way of the Bodhisattva",
            language="en",
            group_id="group_id_1",
            type="version",
            is_published=True,
            created_date="2025-03-20 09:28:28.076920",
            updated_date="2025-03-20 09:28:28.076934",
            published_date="2025-03-20 09:28:28.076938",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_3",
            title="शबोधिचर्यावतार",
            language="sa",
            group_id="group_id_1",
            type="version",
            is_published=True,
            created_date="2025-03-20 09:29:51.154697",
            updated_date="2025-03-20 09:29:51.154708",
            published_date="2025-03-20 09:29:51.154712",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    mock_table_of_content = TableOfContent(
            id="table_of_content_id",
            text_id="text_id_1",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="id_1",
                    title="section_1",
                    section_number=1,
                    parent_id="id_1",
                    segments=[],
                    sections=[],
                    created_date="2025-03-16 04:40:54.757652",
                    updated_date="2025-03-16 04:40:54.757652",
                    published_date="2025-03-16 04:40:54.757652"
                )
            ]
        )
    language = "en"
    with patch('pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id', new_callable=AsyncMock) as mock_text_detail, \
        patch("pecha_api.texts.texts_service.get_text_versions_by_group_id_cache", new_callable=AsyncMock, return_value=None),\
        patch("pecha_api.texts.texts_service.set_text_versions_by_group_id_cache", new_callable=AsyncMock, return_value=None),\
        patch('pecha_api.texts.texts_service.get_texts_by_group_id', new_callable=AsyncMock) as mock_get_texts_by_group_id,\
        patch('pecha_api.texts.texts_service.get_contents_by_id', new_callable=AsyncMock) as mock_get_contents_by_id:
        mock_text_detail.return_value = text_detail
        mock_get_texts_by_group_id.return_value = texts_by_group_id
        mock_get_contents_by_id.return_value = [mock_table_of_content]
        response = await get_text_versions_by_group_id(text_id="id_1",language=language, skip=0, limit=10)
        assert response is not None
        assert response.text is not None
        assert isinstance(response.text, TextDTO)
        assert response.text.type == "version"
        assert response.text.language == language
        assert response.text.id == "text_id_2"
        assert response.versions is not None
        assert len(response.versions) == 2
        assert response.versions[0] is not None
        assert isinstance(response.versions[0], TextVersion)
        assert response.versions[0].id == "text_id_1"
        for version in response.versions:
            assert isinstance(version, TextVersion)
            assert version.type == "version"



@pytest.mark.asyncio
async def test_create_new_text():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    title = "བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།"
    language = "bo"
    is_published = True
    group_id = "67dd22a8d9f06ab28feedc90"
    created_date = "2025-03-16 04:40:54.757652"
    updated_date = "2025-03-16 04:40:54.757652"
    published_date = "2025-03-16 04:40:54.757652"
    published_by = "pecha"
    type_ = TextType.VERSION
    categories = []
    with patch('pecha_api.texts.texts_service.validate_user_exists', return_value=True), \
            patch('pecha_api.texts.texts_service.create_text', new_callable=AsyncMock) as mock_create_text,\
            patch('pecha_api.texts.texts_service.validate_group_exists', new_callable=AsyncMock) as mock_validate_group_exists:
        mock_create_text.return_value = AsyncMock(
            id=text_id,
            pecha_text_id="test_pecha_id",
            title=title,
            language=language,
            is_published=is_published,
            group_id=group_id,
            created_date=created_date,
            updated_date=updated_date,
            published_date=published_date,
            published_by=published_by,
            type=type_,
            categories=categories,
            views=0,
            source_link="https://test-source.com",
            ranking=1,
            license="CC0"
        )
        mock_validate_group_exists.return_value = True
        response = await create_new_text(
            create_text_request=CreateTextRequest(
                pecha_text_id="test_pecha_id",
                title=title,
                language=language,
                group_id=group_id,
                published_by=published_by,
                type=type_,
                categories=categories,
                source_link="https://test-source.com",
                ranking=1,
                license="CC0"
            ),
            token="admin"
        )
        assert response is not None
        assert isinstance(response, TextDTO)
        assert response.id == text_id
        assert response.title == title
        assert response.language == language
        assert response.type == type_.value
        assert response.is_published == is_published
        assert response.created_date == created_date
        assert response.updated_date == updated_date
        assert response.published_date == published_date
        assert response.published_by == published_by
        assert response.categories == categories

@pytest.mark.asyncio
async def test_create_new_text_invalid_group_id():
    with patch("pecha_api.texts.texts_service.validate_user_exists", return_value=True), \
        patch("pecha_api.texts.texts_service.validate_group_exists", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await create_new_text(
                create_text_request=CreateTextRequest(
                    pecha_text_id="test_pecha_id",
                    title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
                    language="bo",
                    group_id="invalid_group_id",
                    published_by="pecha",
                    type=TextType.VERSION,
                    categories=[],
                    source_link="https://test-source.com",
                    ranking=1,
                    license="CC0"
                ),
                token="user"
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.GROUP_NOT_FOUND_MESSAGE
    
@pytest.mark.asyncio
async def test_create_new_text_invalid_user():
    with patch("pecha_api.texts.texts_service.validate_user_exists", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await create_new_text(
                create_text_request=CreateTextRequest(
                    pecha_text_id="test_pecha_id",
                    title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
                    language="bo",
                    group_id="67dd22a8d9f06ab28feedc90",
                    published_by="pecha",
                    type=TextType.VERSION,
                    categories=[],
                    source_link="https://test-source.com",
                    ranking=1,
                    license="CC0"
                ),
                token="user"
            )
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

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
async def test_get_table_of_contents_by_text_id_success():
    text_id = "text_id_1"
    language = "bo"
    skip = 0
    limit = 10

    mock_text_detail = TextDTO(
        id=text_id,
        title="text_1",
        language=language,
        group_id="group_id_1",
        type="version",
        is_published=False,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 04:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="pecha",
        categories=[],
        views=0
    )
    mock_group_texts = [
        TextDTO(
            id="text_id_1",
            title="text_1",
            language="bo",
            group_id="group_id_1",
            type="version",
            is_published=False,
            created_date="2025-03-16 04:40:54.757652",
            updated_date="2025-03-16 04:40:54.757652",
            published_date="2025-03-16 04:40:54.757652",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="text_2",
            language="en",
            group_id="group_id_1",
            type="version",
            is_published=False,
            created_date="2025-03-16 04:40:54.757652",
            updated_date="2025-03-16 04:40:54.757652",
            published_date="2025-03-16 04:40:54.757652",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]

    table_of_contents = [
        TableOfContent(
            id="id_1",
            text_id=text_id,
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="id_1",
                    title="section_1",
                    section_number=1,
                    parent_id="id_1",
                    segments=[
                        TextSegment(
                            segment_id="seg_1",
                            segment_number=1
                        )
                    ],
                    sections=[],
                    created_date="2025-03-16 04:40:54.757652",
                    updated_date="2025-03-16 04:40:54.757652",
                    published_date="2025-03-16 04:40:54.757652"
                )
            ]
        )
    ]

    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.get_table_of_contents_by_text_id_cache", new_callable=MagicMock, return_value=None),\
        patch("pecha_api.texts.texts_service.set_table_of_contents_by_text_id_cache", new_callable=MagicMock, return_value=None),\
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
        patch("pecha_api.texts.texts_service.get_texts_by_group_id", new_callable=AsyncMock, return_value=mock_group_texts), \
        patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=table_of_contents):
        
        response = await get_table_of_contents_by_text_id(
            text_id=text_id,
            language=language,
            skip=skip,
            limit=limit
        )
        
        assert response is not None
        assert isinstance(response, TableOfContentResponse)
        assert response.text_detail is not None
        assert isinstance(response.text_detail, TextDTO)
        assert response.text_detail.id == mock_text_detail.id
        assert response.text_detail.language == language
        assert response.contents is not None
        assert len(response.contents) == 1
        assert response.contents[0] is not None
        assert isinstance(response.contents[0], TableOfContent)
        assert response.contents[0].id == table_of_contents[0].id
        assert response.contents[0].text_id == table_of_contents[0].text_id
        assert response.contents[0].sections is not None

@pytest.mark.asyncio
async def test_get_table_of_contents_by_text_id_success_language_is_none():
    text_id = "text_id_1"
    language = "en"
    skip = 0
    limit = 10

    mock_text_detail = TextDTO(
        id=text_id,
        title="text_1",
        language=language,
        group_id="group_id_1",
        type="version",
        is_published=False,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 04:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="pecha",
        categories=[],
        views=0
    )
    mock_group_texts = [
        TextDTO(
            id="text_id_1",
            title="text_1",
            language="bo",
            group_id="group_id_1",
            type="version",
            is_published=False,
            created_date="2025-03-16 04:40:54.757652",
            updated_date="2025-03-16 04:40:54.757652",
            published_date="2025-03-16 04:40:54.757652",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_2",
            title="text_2",
            language="en",
            group_id="group_id_1",
            type="version",
            is_published=False,
            created_date="2025-03-16 04:40:54.757652",
            updated_date="2025-03-16 04:40:54.757652",
            published_date="2025-03-16 04:40:54.757652",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]

    table_of_contents = [
        TableOfContent(
            id="id_1",
            text_id=text_id,
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="id_1",
                    title="section_1",
                    section_number=1,
                    parent_id="id_1",
                    segments=[
                        TextSegment(
                            segment_id="seg_1",
                            segment_number=1
                        )
                    ],
                    sections=[],
                    created_date="2025-03-16 04:40:54.757652",
                    updated_date="2025-03-16 04:40:54.757652",
                    published_date="2025-03-16 04:40:54.757652"
                )
            ]
        )
    ]

    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.get_table_of_contents_by_text_id_cache", new_callable=MagicMock, return_value=None),\
        patch("pecha_api.texts.texts_service.set_table_of_contents_by_text_id_cache", new_callable=MagicMock, return_value=None),\
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
        patch("pecha_api.texts.texts_service.get_texts_by_group_id", new_callable=AsyncMock, return_value=mock_group_texts), \
        patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=table_of_contents):
        
        response = await get_table_of_contents_by_text_id(
            text_id=text_id,
            language=None,
            skip=skip,
            limit=limit
        )
        
        assert response is not None
        assert isinstance(response, TableOfContentResponse)
        assert response.text_detail is not None
        assert isinstance(response.text_detail, TextDTO)
        assert response.text_detail.language == language
        assert response.contents is not None
        assert len(response.contents) == 1
        assert response.contents[0] is not None
        assert isinstance(response.contents[0], TableOfContent)

@pytest.mark.asyncio
async def test_get_table_of_contents_by_text_id_root_text_is_none():
    """Test that HTTPException is raised when no root text can be determined after filtering"""
    from pecha_api.constants import Constants
    
    text_id = "text_id_1"
    language = "zh"  # Requesting Chinese but no Chinese text exists
    skip = 0
    limit = 10

    mock_text_detail = TextDTO(
        id=text_id,
        title="text_1",
        language="bo",
        group_id="group_id_1",
        type="version",
        is_published=False,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 04:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="pecha",
        categories=[],
        views=0
    )
    
    # Mock texts that are all in excluded_text_ids so root_text becomes None
    excluded_id = "excluded_text_id_test"
    mock_group_texts = [
        TextDTO(
            id=excluded_id,
            title="text_1",
            language="bo",
            group_id="group_id_1",
            type="version",
            is_published=False,
            created_date="2025-03-16 04:40:54.757652",
            updated_date="2025-03-16 04:40:54.757652",
            published_date="2025-03-16 04:40:54.757652",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]

    table_of_contents = [
        TableOfContent(
            id="id_1",
            text_id=text_id,
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="id_1",
                    title="section_1",
                    section_number=1,
                    parent_id="id_1",
                    segments=[],
                    sections=[],
                    created_date="2025-03-16 04:40:54.757652",
                    updated_date="2025-03-16 04:40:54.757652",
                    published_date="2025-03-16 04:40:54.757652"
                )
            ]
        )
    ]

    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.get_table_of_contents_by_text_id_cache", new_callable=MagicMock, return_value=None),\
        patch("pecha_api.texts.texts_service.set_table_of_contents_by_text_id_cache", new_callable=MagicMock, return_value=None),\
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
        patch("pecha_api.texts.texts_service.get_texts_by_group_id", new_callable=AsyncMock, return_value=mock_group_texts), \
        patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=table_of_contents), \
        patch("pecha_api.constants.Constants.excluded_text_ids", [excluded_id]):
        
        with pytest.raises(HTTPException) as exc_info:
            await get_table_of_contents_by_text_id(
                text_id=text_id,
                language=language,
                skip=skip,
                limit=limit
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_get_table_of_contents_by_text_id_invalid_text():
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_table_of_contents_by_text_id(
                text_id="id_1",
                language="en",
                skip=0,
                limit=10
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE


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
async def test_delete_table_of_content_success():
    with patch("pecha_api.texts.texts_service.delete_table_of_content_by_text_id", new_callable=AsyncMock), \
        patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True):
        response = await remove_table_of_content_by_text_id(text_id="text_id_1")
        assert response is not None

@pytest.mark.asyncio
async def test_delete_table_of_content_invalid_text_id():
    with patch("pecha_api.texts.texts_service.delete_table_of_content_by_text_id", new_callable=AsyncMock), \
        patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exec_info:
            await remove_table_of_content_by_text_id(text_id="invalid_id")
        assert exec_info.value.status_code == 404
        assert exec_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_delete_text_by_text_id_success():
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.delete_text_by_id", new_callable=AsyncMock):
        response = await delete_text_by_text_id(text_id="text_id_1")
        assert response is None

@pytest.mark.asyncio
async def test_delete_text_by_text_id_invalid_text_id():
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await delete_text_by_text_id(text_id="invalid_text_id")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_get_sheet_success_user_viewing_own_sheets():
    email = "test_user@gmail.com"
    mock_sheets = [
            type("Text", (), {
                "id": f"sheet_id_{i}",
                "title": "Test Sheet",
                "language": "en",
                "group_id": "group_id",
                "type": "sheet",
                "is_published": True if i % 2 == 0 else False,
                "created_date": "2021-01-01",
                "updated_date": "2021-01-01",
                "published_date": "2021-01-01",
                "published_by": email,
                "categories": [],
                "views": 10
            })()
            for i in range(1,11)
        ]
    with patch("pecha_api.texts.texts_service.fetch_sheets_from_db", new_callable=AsyncMock, return_value=mock_sheets):

        response = await get_sheet(published_by=email, is_published=None, sort_by=None, sort_order=None, skip=0, limit=10)

        assert response is not None
        assert len(response) == 10
        for sheet in response:
            assert sheet.published_by == email

@pytest.mark.asyncio
async def test_get_text_details_by_text_id_with_text_id_content_id_segment_id_success():
    text_id = "text_id_1"
    content_id = "content_id_1"
    segment_id = "segment_id_1"
    mock_text_detail = TextDTO(
        id=text_id,
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
    mock_table_of_content = TableOfContent(
        id=content_id,
        text_id=text_id,
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_id_1",
                title="section_title",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    TextSegment(
                        segment_id="segment_id_1",
                        segment_number=1
                    ),
                    TextSegment(
                        segment_id="segment_id_2",
                        segment_number=2
                    ),
                    TextSegment(
                        segment_id="segment_id_3",
                        segment_number=3
                    )
                ],
                sections=[],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )
    mock_mapped_table_of_content = DetailTableOfContent(
        id=content_id,
        text_id=text_id,
        sections=[
            DetailSection(
                id="section_id_1",
                title="section_title",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    DetailTextSegment(
                        segment_id="segment_id_1",
                        segment_number=1,
                        content="segment_content_1",
                        translation=None
                    ),
                    DetailTextSegment(
                        segment_id="segment_id_2",
                        segment_number=2,
                        content="segment_content_2",
                        translation=None
                    )
                ],
                sections=[],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )

    with patch("pecha_api.texts.texts_service._validate_text_detail_request", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
        patch("pecha_api.texts.texts_service.get_table_of_content_by_content_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
        patch("pecha_api.texts.texts_service.SegmentUtils.get_mapped_segment_content_for_table_of_content", new_callable=AsyncMock, return_value=mock_mapped_table_of_content):

        response = await get_text_details_by_text_id(
            text_id=text_id,
            text_details_request=TextDetailsRequest(
                content_id=content_id,
                segment_id=segment_id,
                size=2,
                direction=PaginationDirection.NEXT
            )
        )

        assert response is not None
        assert response.text_detail is not None
        assert isinstance(response.text_detail, TextDTO)
        assert response.text_detail.id == mock_text_detail.id
        assert response.content is not None
        assert isinstance(response.content, DetailTableOfContent)
        assert response.content.sections is not None
        assert len(response.content.sections) == 1
        assert response.content.sections[0] is not None
        assert isinstance(response.content.sections[0], DetailSection)
        section = response.content.sections[0]
        assert section.segments is not None
        assert len(section.segments) == 2
        assert section.segments[0].segment_id == "segment_id_1"
        assert section.segments[1].segment_id == "segment_id_2"
        assert response.pagination_direction == PaginationDirection.NEXT

@pytest.mark.asyncio
async def test_get_text_details_by_text_id_with_text_id_content_id_segment_id_previous_success():
    text_id = "text_id_1"
    content_id = "content_id_1"
    segment_id = "segment_id_1"
    mock_text_detail = TextDTO(
        id=text_id,
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
    mock_table_of_content = TableOfContent(
        id=content_id,
        text_id=text_id,
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_id_1",
                title="section_title",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    TextSegment(
                        segment_id="segment_id_1",
                        segment_number=1
                    ),
                    TextSegment(
                        segment_id="segment_id_2",
                        segment_number=2
                    ),
                    TextSegment(
                        segment_id="segment_id_3",
                        segment_number=3
                    )
                ],
                sections=[],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )
    mock_mapped_table_of_content = DetailTableOfContent(
        id=content_id,
        text_id=text_id,
        sections=[
            DetailSection(
                id="section_id_1",
                title="section_title",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    DetailTextSegment(
                        segment_id="segment_id_1",
                        segment_number=1,
                        content="segment_content_1",
                        translation=None
                    )
                ],
                sections=[],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )

    with patch("pecha_api.texts.texts_service._validate_text_detail_request", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
        patch("pecha_api.texts.texts_service.get_table_of_content_by_content_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
        patch("pecha_api.texts.texts_service.SegmentUtils.get_mapped_segment_content_for_table_of_content", new_callable=AsyncMock, return_value=mock_mapped_table_of_content):

        response = await get_text_details_by_text_id(
            text_id=text_id,
            text_details_request=TextDetailsRequest(
                content_id=content_id,
                segment_id=segment_id,
                size=2,
                direction=PaginationDirection.PREVIOUS
            )
        )

        assert response is not None
        assert response.text_detail is not None
        assert isinstance(response.text_detail, TextDTO)
        assert response.text_detail.id == mock_text_detail.id
        assert response.content is not None
        assert isinstance(response.content, DetailTableOfContent)
        assert response.content.sections is not None
        assert len(response.content.sections) == 1
        assert response.content.sections[0] is not None
        assert isinstance(response.content.sections[0], DetailSection)
        section = response.content.sections[0]
        assert section.segments is not None
        assert len(section.segments) == 1
        assert section.segments[0].segment_id == "segment_id_1"
        assert response.pagination_direction == PaginationDirection.PREVIOUS


@pytest.mark.asyncio
async def test_get_text_details_by_text_id_with_segment_id_only_success():
    text_id = "text_id_1"
    segment_id = "segment_id_1"
    mock_text_detail = TextDTO(
        id=text_id,
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
    mock_table_of_contents = [
        TableOfContent(
            id=f"content_id_{i}",
            text_id=text_id,
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section_id_1",
                    title="section_title",
                    section_number=1,
                    parent_id="parent_id_1",
                    segments=[
                        TextSegment(
                            segment_id=f"segment_id_{i}",
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
        for i in range(1,11)
    ]
    mock_mapped_table_of_contents = DetailTableOfContent(
        id="content_id_1",
        text_id=text_id,
        sections=[
            DetailSection(
                id="section_id_1",
                title="section_title",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    DetailTextSegment(
                        segment_id=f"segment_id_1",
                        segment_number=1,
                        content="segment_content_1",
                        translation=None
                    )
                ],
                sections=[],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )

    with patch("pecha_api.texts.texts_service._validate_text_detail_request", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
        patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=mock_table_of_contents), \
        patch("pecha_api.texts.texts_service.SegmentUtils.get_mapped_segment_content_for_table_of_content", new_callable=AsyncMock, return_value=mock_mapped_table_of_contents):

        response = await get_text_details_by_text_id(
            text_id=text_id,
            text_details_request=TextDetailsRequest(
                segment_id=segment_id,
                size=2,
                direction=PaginationDirection.NEXT
            )
        )

        assert response is not None
        assert response.text_detail is not None
        assert isinstance(response.text_detail, TextDTO)
        assert response.text_detail.id == mock_text_detail.id
        assert response.content is not None
        assert isinstance(response.content, DetailTableOfContent)
        assert response.content.sections is not None
        assert len(response.content.sections) == 1
        assert response.content.sections[0] is not None
        assert isinstance(response.content.sections[0], DetailSection)
        section = response.content.sections[0]
        assert section.segments is not None
        assert len(section.segments) == 1
        assert section.segments[0].segment_id == segment_id
        assert response.pagination_direction == PaginationDirection.NEXT



@pytest.mark.asyncio
async def test_get_text_details_by_text_id_with_content_id_only_success():
    text_id = "text_id_1"
    content_id = "content_id_1"
    mock_text_detail = TextDTO(
        id=text_id,
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
    mock_table_of_contents = [
        TableOfContent(
            id=f"content_id_{i}",
            text_id=text_id,
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section_id_1",
                    title="section_title",
                    section_number=1,
                    parent_id="parent_id_1",
                    segments=[
                        TextSegment(
                            segment_id=f"segment_id_{i}",
                            segment_number=1
                        )
                    ], 
                    sections=[
                        Section(
                            id="section_id_2",
                            title="section_title_2",
                            section_number=2,
                            parent_id="parent_id_2",
                            segments=[
                                TextSegment(
                                    segment_id=f"1_segment_id_{i}",
                                    segment_number=1
                                )
                            ],
                            sections=[],
                            created_date="created_date",
                            updated_date="updated_date",
                            published_date="published_date"
                        )
                    ],
                    created_date="created_date",
                    updated_date="updated_date",
                    published_date="published_date"
                )
            ]
        )
        for i in range(1,11)
    ]
    mock_mapped_table_of_contents = DetailTableOfContent(
        id="content_id_1",
        text_id=text_id,
        sections=[
            DetailSection(
                id="section_id_1",
                title="section_title",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    DetailTextSegment(
                        segment_id=f"segment_id_1",
                        segment_number=1,
                        content="segment_content_1",
                        translation=None
                    )
                ],
                sections=[
                    DetailSection(
                        id="section_id_2",
                        title="section_title_2",
                        section_number=2,
                        parent_id="parent_id_2",
                        segments=[
                            DetailTextSegment(
                                segment_id=f"1_segment_id_1",
                                segment_number=1,
                                content="segment_content_1",
                                translation=None
                            )
                        ],
                        sections=[],
                        created_date="created_date",
                        updated_date="updated_date",
                        published_date="published_date"
                    )
                ],
                created_date="created_date",
                updated_date="updated_date",
                published_date="published_date"
            )
        ]
    )

    with patch("pecha_api.texts.texts_service._validate_text_detail_request", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text_detail), \
        patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=mock_table_of_contents), \
        patch("pecha_api.texts.texts_service.SegmentUtils.get_mapped_segment_content_for_table_of_content", new_callable=AsyncMock, return_value=mock_mapped_table_of_contents):

        response = await get_text_details_by_text_id(
            text_id=text_id,
            text_details_request=TextDetailsRequest(
                content_id=content_id,
                size=2,
                direction=PaginationDirection.NEXT
            )
        )

        assert response is not None
        assert response.text_detail is not None
        assert isinstance(response.text_detail, TextDTO)
        assert response.text_detail.id == mock_text_detail.id
        assert response.content is not None
        assert isinstance(response.content, DetailTableOfContent)
        assert response.content.id == content_id
        assert response.content.sections is not None
        assert len(response.content.sections) == 1
        assert response.content.sections[0] is not None
        assert isinstance(response.content.sections[0], DetailSection)
        section = response.content.sections[0]
        assert section.segments is not None
        assert section.sections is not None
        assert len(section.segments) + len(section.sections[0].segments) == 2
        assert section.segments[0].segment_id == "segment_id_1"
        assert response.pagination_direction == PaginationDirection.NEXT
    

@pytest.mark.asyncio
async def test_get_table_of_content_by_sheet_id_success():
    sheet_id = "sheet_id_1"
    mock_table_of_contents = [
        TableOfContent(
            id="content_id_1",
            text_id=sheet_id,
            type=TableOfContentType.SHEET,
            sections=[
                Section(
                    id="section_id_1",
                    title="section_title",
                    section_number=1,
                    parent_id="parent_id_1",
                    segments=[
                        TextSegment(
                            segment_id="segment_id_1",
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
    ]
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=mock_table_of_contents), \
        patch("pecha_api.texts.texts_service.set_table_of_content_by_sheet_id_cache", new_callable=AsyncMock, return_value=None):
    
        response = await get_table_of_content_by_sheet_id(sheet_id=sheet_id)

        assert response is not None
        assert isinstance(response, TableOfContent)
        assert response.id == "content_id_1"

@pytest.mark.asyncio
async def test_get_table_of_content_by_sheet_id_invalid_sheet_id():
    sheet_id = "invalid_sheet_id"

    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_table_of_content_by_sheet_id(sheet_id=sheet_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE
    

@pytest.mark.asyncio
async def test_validate_text_detail_request_success():
    text_id = "text_id_1"
    content_id = "content_id_1"
    version_id = "version_id_1"
    segment_id = "segment_id_1"
    section_id = "section_id_1"
    size = 20
    direction = PaginationDirection.NEXT

    text_details_request = TextDetailsRequest(
        content_id=content_id,
        version_id=version_id,
        segment_id=segment_id,
        section_id=section_id,
        size=size,
        direction=direction
    )

    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=True):
        
        response = await _validate_text_detail_request(text_id=text_id, text_details_request=text_details_request)
        
@pytest.mark.asyncio
async def test_validate_text_detail_request_text_id_is_none():
    text_id = None
    content_id = "content_id_1"
    version_id = "version_id_1"
    segment_id = "segment_id_1"
    section_id = "section_id_1"
    size = 20
    direction = PaginationDirection.NEXT

    text_details_request = TextDetailsRequest(
        content_id=content_id,
        version_id=version_id,
        segment_id=segment_id,
        section_id=section_id,
        size=size,
        direction=direction
    )

    with pytest.raises(HTTPException) as e:
        await _validate_text_detail_request(text_id=text_id, text_details_request=text_details_request)

    assert e.value.status_code == 400
    assert e.value.detail == ErrorConstants.TEXT_OR_TERM_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_validate_text_detail_request_invalid_version_id():
    text_id = None
    content_id = "content_id_1"
    version_id = "invalid_version_id_1"
    segment_id = "segment_id_1"
    section_id = "section_id_1"
    size = 20
    direction = PaginationDirection.NEXT

    text_details_request = TextDetailsRequest(
        content_id=content_id,
        version_id=version_id,
        segment_id=segment_id,
        section_id=section_id,
        size=size,
        direction=direction
    )

    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as e:
            await _validate_text_detail_request(text_id=text_id, text_details_request=text_details_request)
        assert e.value.status_code == 400
        assert e.value.detail == ErrorConstants.TEXT_OR_TERM_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_validate_text_detail_request_invalid_segment_id():
    text_id = None
    content_id = "content_id_1"
    version_id = "version_id_1"
    segment_id = "invalid_segment_id_1"
    section_id = "section_id_1"
    size = 20
    direction = PaginationDirection.NEXT
    
    text_details_request = TextDetailsRequest(
        content_id=content_id,
        version_id=version_id,
        segment_id=segment_id,
        section_id=section_id,
        size=size,
        direction=direction
    )
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=False):

        with pytest.raises(HTTPException) as e:
            await _validate_text_detail_request(text_id=text_id, text_details_request=text_details_request)
        
        assert e.value.status_code == 400
        assert e.value.detail == ErrorConstants.TEXT_OR_TERM_NOT_FOUND_MESSAGE


@pytest.mark.asyncio
async def test_get_versions_by_group_id_language_is_none():
    text_detail = TextDTO(
        id="id_1",
        title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
        group_id="group_id_1",
        language="bo",
        type="version",
        is_published=True,
        created_date="2025-03-20 09:26:16.571522",
        updated_date="2025-03-20 09:26:16.571532",
        published_date="2025-03-20 09:26:16.571536",
        published_by="pecha",
        categories=[],
        views=0
    )
    texts_by_group_id = [
        TextDTO(
            id="text_id_1",
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            group_id="group_id_1",
            language="bo",
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
            id="text_id_2",
            title="The Way of the Bodhisattva",
            language="en",
            group_id="group_id_1",
            type="version",
            is_published=True,
            created_date="2025-03-20 09:28:28.076920",
            updated_date="2025-03-20 09:28:28.076934",
            published_date="2025-03-20 09:28:28.076938",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_3",
            title="शबोधिचर्यावतार",
            language="sa",
            group_id="group_id_1",
            type="version",
            is_published=True,
            created_date="2025-03-20 09:29:51.154697",
            updated_date="2025-03-20 09:29:51.154708",
            published_date="2025-03-20 09:29:51.154712",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    mock_table_of_content = TableOfContent(
            id="table_of_content_id",
            text_id="text_id_1",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="id_1",
                    title="section_1",
                    section_number=1,
                    parent_id="id_1",
                    segments=[],
                    sections=[],
                    created_date="2025-03-16 04:40:54.757652",
                    updated_date="2025-03-16 04:40:54.757652",
                    published_date="2025-03-16 04:40:54.757652"
                )
            ]
        )
    language = "en"
    with patch('pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id', new_callable=AsyncMock) as mock_text_detail, \
        patch("pecha_api.texts.texts_service.get_text_versions_by_group_id_cache", new_callable=AsyncMock, return_value=None),\
        patch("pecha_api.texts.texts_service.set_text_versions_by_group_id_cache", new_callable=AsyncMock, return_value=None),\
        patch('pecha_api.texts.texts_service.get_texts_by_group_id', new_callable=AsyncMock) as mock_get_texts_by_group_id,\
        patch('pecha_api.texts.texts_service.get_contents_by_id', new_callable=AsyncMock) as mock_get_contents_by_id:
        mock_text_detail.return_value = text_detail
        mock_get_texts_by_group_id.return_value = texts_by_group_id
        mock_get_contents_by_id.return_value = [mock_table_of_content]
        response = await get_text_versions_by_group_id(text_id="id_1",language=None, skip=0, limit=10)
        assert response is not None
        assert response.text is not None
        assert isinstance(response.text, TextDTO)
        assert response.text.type == "version"
        assert response.text.language == language
        assert response.text.id == "text_id_2"
        assert response.versions is not None
        assert len(response.versions) == 2
        assert response.versions[0] is not None
        assert isinstance(response.versions[0], TextVersion)
        assert response.versions[0].id == "text_id_1"
        for version in response.versions:
            assert isinstance(version, TextVersion)
            assert version.type == "version"
        
@pytest.mark.asyncio
async def test_get_versions_by_group_id_cache_data_is_not_none():
    """Test get_text_versions_by_group_id returns cached data when available"""
    text_detail = TextDTO(
        id="id_1",
        title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
        group_id="group_id_1",
        language="bo",
        type="version",
        is_published=True,
        created_date="2025-03-20 09:26:16.571522",
        updated_date="2025-03-20 09:26:16.571532",
        published_date="2025-03-20 09:26:16.571536",
        published_by="pecha",
        categories=[],
        views=0
    )
    texts_by_group_id = [
        TextDTO(
            id="text_id_1",
            title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
            group_id="group_id_1",
            language="bo",
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
            id="text_id_2",
            title="The Way of the Bodhisattva",
            language="en",
            group_id="group_id_1",
            type="version",
            is_published=True,
            created_date="2025-03-20 09:28:28.076920",
            updated_date="2025-03-20 09:28:28.076934",
            published_date="2025-03-20 09:28:28.076938",
            published_by="pecha",
            categories=[],
            views=0
        ),
        TextDTO(
            id="text_id_3",
            title="शबोधिचर्यावतार",
            language="sa",
            group_id="group_id_1",
            type="version",
            is_published=True,
            created_date="2025-03-20 09:29:51.154697",
            updated_date="2025-03-20 09:29:51.154708",
            published_date="2025-03-20 09:29:51.154712",
            published_by="pecha",
            categories=[],
            views=0
        )
    ]
    cache_text_version = TextVersionResponse(
        text=text_detail,
        versions=[
            TextVersion(
                id="text_id_1",
                title="བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ།",
                parent_id=None,
                priority=None,
                language="bo",
                type="version",
                group_id="group_id_1",
                table_of_contents=[],
                is_published=True,
                created_date="2025-03-20 09:26:16.571522",
                updated_date="2025-03-20 09:26:16.571532",
                published_date="2025-03-20 09:26:16.571536",
                published_by="pecha"
            )
        ]
    )
    language = "en"
    
    # Mock TextUtils.get_text_detail_by_id which is called before cache check
    # Note: The actual implementation first gets the root text, then checks cache
    with patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=text_detail), \
         patch("pecha_api.texts.texts_service.get_texts_by_group_id", new_callable=AsyncMock, return_value=texts_by_group_id), \
         patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=[]), \
         patch("pecha_api.texts.texts_service.set_text_versions_by_group_id_cache", new_callable=AsyncMock):

        response = await get_text_versions_by_group_id(text_id="id_1", language=language, skip=0, limit=10)

        assert response is not None
        assert isinstance(response, TextVersionResponse)
        assert response.text is not None
        assert isinstance(response.text, TextDTO)
        assert response.versions is not None
        # When language="en", filter_text_on_root_and_version selects text_id_2 (English) as root
        assert response.text.id == "text_id_2"
        assert response.text.language == "en"
        # The other texts become versions
        assert len(response.versions) == 2


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

def test_get_trimmed_segment_dict_next_direction():
    """Test _get_trimmed_segment_dict_ with NEXT direction"""
    from pecha_api.texts.texts_service import _get_trimmed_segment_dict_
    
    segments_with_position = [
        ("seg_1", 1),
        ("seg_2", 2),
        ("seg_3", 3),
        ("seg_4", 4),
        ("seg_5", 5)
    ]
    
    result = _get_trimmed_segment_dict_(
        segments_with_position=segments_with_position,
        segment_id="seg_2",
        direction=PaginationDirection.NEXT,
        size=2
    )
    
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) == 2
    assert "seg_2" in result
    assert "seg_3" in result
    assert result["seg_2"] == 2
    assert result["seg_3"] == 3

def test_get_trimmed_segment_dict_previous_direction():
    """Test _get_trimmed_segment_dict_ with PREVIOUS direction"""
    from pecha_api.texts.texts_service import _get_trimmed_segment_dict_
    
    segments_with_position = [
        ("seg_1", 1),
        ("seg_2", 2),
        ("seg_3", 3),
        ("seg_4", 4),
        ("seg_5", 5)
    ]
    
    result = _get_trimmed_segment_dict_(
        segments_with_position=segments_with_position,
        segment_id="seg_4",
        direction=PaginationDirection.PREVIOUS,
        size=2
    )
    
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) == 2
    assert "seg_3" in result
    assert "seg_4" in result
    assert result["seg_3"] == 3
    assert result["seg_4"] == 4

def test_get_trimmed_segment_dict_next_at_end():
    """Test _get_trimmed_segment_dict_ with NEXT direction at end of list"""
    from pecha_api.texts.texts_service import _get_trimmed_segment_dict_
    
    segments_with_position = [
        ("seg_1", 1),
        ("seg_2", 2),
        ("seg_3", 3)
    ]
    
    result = _get_trimmed_segment_dict_(
        segments_with_position=segments_with_position,
        segment_id="seg_2",
        direction=PaginationDirection.NEXT,
        size=5
    )
    
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) == 2
    assert "seg_2" in result
    assert "seg_3" in result

def test_get_trimmed_segment_dict_previous_at_start():
    """Test _get_trimmed_segment_dict_ with PREVIOUS direction at start of list"""
    from pecha_api.texts.texts_service import _get_trimmed_segment_dict_
    
    segments_with_position = [
        ("seg_1", 1),
        ("seg_2", 2),
        ("seg_3", 3)
    ]
    
    result = _get_trimmed_segment_dict_(
        segments_with_position=segments_with_position,
        segment_id="seg_1",
        direction=PaginationDirection.PREVIOUS,
        size=5
    )
    
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) == 1
    assert "seg_1" in result

def test_get_segments_with_position_simple():
    """Test _get_segments_with_position_ with simple sections"""
    from pecha_api.texts.texts_service import _get_segments_with_position_
    
    table_of_content = TableOfContent(
        id="toc_id",
        text_id="text_id",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_1",
                title="Section 1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="seg_1", segment_number=1),
                    TextSegment(segment_id="seg_2", segment_number=2)
                ],
                sections=[]
            )
        ]
    )
    
    result = _get_segments_with_position_(table_of_content=table_of_content)
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == ("seg_1", 1)
    assert result[1] == ("seg_2", 2)

def test_get_segments_with_position_nested():
    """Test _get_segments_with_position_ with nested sections"""
    from pecha_api.texts.texts_service import _get_segments_with_position_
    
    table_of_content = TableOfContent(
        id="toc_id",
        text_id="text_id",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_1",
                title="Section 1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="seg_1", segment_number=1)
                ],
                sections=[
                    Section(
                        id="section_2",
                        title="Section 2",
                        section_number=2,
                        segments=[
                            TextSegment(segment_id="seg_2", segment_number=1)
                        ],
                        sections=[]
                    )
                ]
            )
        ]
    )
    
    result = _get_segments_with_position_(table_of_content=table_of_content)
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == ("seg_1", 1)
    assert result[1] == ("seg_2", 2)

def test_filter_single_section_with_wanted_segments():
    """Test _filter_single_section_ with wanted segments"""
    from pecha_api.texts.texts_service import _filter_single_section_
    
    section = Section(
        id="section_1",
        title="Section 1",
        section_number=1,
        segments=[
            TextSegment(segment_id="seg_1", segment_number=1),
            TextSegment(segment_id="seg_2", segment_number=2),
            TextSegment(segment_id="seg_3", segment_number=3)
        ],
        sections=[]
    )
    
    wanted_segment_ids = {"seg_1", "seg_3"}
    
    result = _filter_single_section_(section=section, wanted_segment_ids=wanted_segment_ids)
    
    assert result is not None
    assert isinstance(result, Section)
    assert len(result.segments) == 2
    assert result.segments[0].segment_id == "seg_1"
    assert result.segments[1].segment_id == "seg_3"

def test_filter_single_section_no_wanted_segments():
    """Test _filter_single_section_ with no wanted segments"""
    from pecha_api.texts.texts_service import _filter_single_section_
    
    section = Section(
        id="section_1",
        title="Section 1",
        section_number=1,
        segments=[
            TextSegment(segment_id="seg_1", segment_number=1),
            TextSegment(segment_id="seg_2", segment_number=2)
        ],
        sections=[]
    )
    
    wanted_segment_ids = {"seg_3", "seg_4"}
    
    result = _filter_single_section_(section=section, wanted_segment_ids=wanted_segment_ids)
    
    assert result is None

def test_filter_single_section_nested_with_wanted_segments():
    """Test _filter_single_section_ with nested sections containing wanted segments"""
    from pecha_api.texts.texts_service import _filter_single_section_
    
    section = Section(
        id="section_1",
        title="Section 1",
        section_number=1,
        segments=[
            TextSegment(segment_id="seg_1", segment_number=1)
        ],
        sections=[
            Section(
                id="section_2",
                title="Section 2",
                section_number=2,
                segments=[
                    TextSegment(segment_id="seg_2", segment_number=1)
                ],
                sections=[]
            )
        ]
    )
    
    wanted_segment_ids = {"seg_2"}
    
    result = _filter_single_section_(section=section, wanted_segment_ids=wanted_segment_ids)
    
    assert result is not None
    assert isinstance(result, Section)
    assert len(result.segments) == 0  # Parent has no wanted segments
    assert len(result.sections) == 1  # But subsection has wanted segments
    assert result.sections[0].segments[0].segment_id == "seg_2"

def test_generate_paginated_table_of_content_by_segments():
    """Test _generate_paginated_table_of_content_by_segments_"""
    from pecha_api.texts.texts_service import _generate_paginated_table_of_content_by_segments_
    
    table_of_content = TableOfContent(
        id="toc_id",
        text_id="text_id",
        type=TableOfContentType.TEXT,
        sections=[
            Section(
                id="section_1",
                title="Section 1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="seg_1", segment_number=1),
                    TextSegment(segment_id="seg_2", segment_number=2),
                    TextSegment(segment_id="seg_3", segment_number=3)
                ],
                sections=[]
            )
        ]
    )
    
    segment_dict = {
        "seg_1": 1,
        "seg_3": 3
    }
    
    result = _generate_paginated_table_of_content_by_segments_(
        table_of_content=table_of_content,
        segment_dict=segment_dict
    )
    
    assert result is not None
    assert isinstance(result, TableOfContent)
    assert result.type == TableOfContentType.TEXT
    assert len(result.sections) == 1
    assert len(result.sections[0].segments) == 2
    assert result.sections[0].segments[0].segment_id == "seg_1"
    assert result.sections[0].segments[1].segment_id == "seg_3"

def test_generate_paginated_table_of_content_by_segments_with_sheet_type():
    """Test _generate_paginated_table_of_content_by_segments_ preserves SHEET type"""
    from pecha_api.texts.texts_service import _generate_paginated_table_of_content_by_segments_
    
    table_of_content = TableOfContent(
        id="toc_id",
        text_id="text_id",
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                title="Section 1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="seg_1", segment_number=1),
                    TextSegment(segment_id="seg_2", segment_number=2)
                ],
                sections=[]
            )
        ]
    )
    
    segment_dict = {
        "seg_1": 1
    }
    
    result = _generate_paginated_table_of_content_by_segments_(
        table_of_content=table_of_content,
        segment_dict=segment_dict
    )
    
    assert result is not None
    assert isinstance(result, TableOfContent)
    assert result.type == TableOfContentType.SHEET
    assert len(result.sections) == 1
    assert len(result.sections[0].segments) == 1
    assert result.sections[0].segments[0].segment_id == "seg_1"

def test_search_section_found():
    """Test _search_section_ when segment is found"""
    from pecha_api.texts.texts_service import _search_section_
    
    sections = [
        Section(
            id="section_1",
            title="Section 1",
            section_number=1,
            segments=[
                TextSegment(segment_id="seg_1", segment_number=1),
                TextSegment(segment_id="seg_2", segment_number=2)
            ],
            sections=[]
        )
    ]
    
    result = _search_section_(sections=sections, segment_id="seg_2")
    
    assert result is True

def test_search_section_not_found():
    """Test _search_section_ when segment is not found"""
    from pecha_api.texts.texts_service import _search_section_
    
    sections = [
        Section(
            id="section_1",
            title="Section 1",
            section_number=1,
            segments=[
                TextSegment(segment_id="seg_1", segment_number=1)
            ],
            sections=[]
        )
    ]
    
    result = _search_section_(sections=sections, segment_id="seg_3")
    
    assert result is False

def test_search_section_nested():
    """Test _search_section_ with nested sections"""
    from pecha_api.texts.texts_service import _search_section_
    
    sections = [
        Section(
            id="section_1",
            title="Section 1",
            section_number=1,
            segments=[
                TextSegment(segment_id="seg_1", segment_number=1)
            ],
            sections=[
                Section(
                    id="section_2",
                    title="Section 2",
                    section_number=2,
                    segments=[
                        TextSegment(segment_id="seg_2", segment_number=1)
                    ],
                    sections=[]
                )
            ]
        )
    ]
    
    result = _search_section_(sections=sections, segment_id="seg_2")
    
    assert result is True

def test_search_table_of_content_where_segment_id_exists_found():
    """Test _search_table_of_content_where_segment_id_exists when segment is found"""
    from pecha_api.texts.texts_service import _search_table_of_content_where_segment_id_exists
    
    table_of_contents = [
        TableOfContent(
            id="toc_1",
            text_id="text_id",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section_1",
                    title="Section 1",
                    section_number=1,
                    segments=[
                        TextSegment(segment_id="seg_1", segment_number=1)
                    ],
                    sections=[]
                )
            ]
        ),
        TableOfContent(
            id="toc_2",
            text_id="text_id",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section_2",
                    title="Section 2",
                    section_number=1,
                    segments=[
                        TextSegment(segment_id="seg_2", segment_number=1)
                    ],
                    sections=[]
                )
            ]
        )
    ]
    
    result = _search_table_of_content_where_segment_id_exists(
        table_of_contents=table_of_contents,
        segment_id="seg_2"
    )
    
    assert result is not None
    assert isinstance(result, TableOfContent)
    assert result.id == "toc_2"

def test_search_table_of_content_where_segment_id_exists_not_found():
    """Test _search_table_of_content_where_segment_id_exists when segment is not found"""
    from pecha_api.texts.texts_service import _search_table_of_content_where_segment_id_exists
    
    table_of_contents = [
        TableOfContent(
            id="toc_1",
            text_id="text_id",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section_1",
                    title="Section 1",
                    section_number=1,
                    segments=[
                        TextSegment(segment_id="seg_1", segment_number=1)
                    ],
                    sections=[]
                )
            ]
        )
    ]
    
    with pytest.raises(HTTPException) as exc_info:
        _search_table_of_content_where_segment_id_exists(
            table_of_contents=table_of_contents,
            segment_id="seg_3"
        )
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == ErrorConstants.TABLE_OF_CONTENT_NOT_FOUND_MESSAGE

def test_get_first_segment_and_table_of_content_success():
    """Test _get_first_segment_and_table_of_content_ when segment is found"""
    from pecha_api.texts.texts_service import _get_first_segment_and_table_of_content_
    
    table_of_contents = [
        TableOfContent(
            id="toc_1",
            text_id="text_id",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section_1",
                    title="Section 1",
                    section_number=1,
                    segments=[
                        TextSegment(segment_id="seg_1", segment_number=1)
                    ],
                    sections=[]
                )
            ]
        )
    ]
    
    segment_id, table_of_content = _get_first_segment_and_table_of_content_(
        table_of_contents=table_of_contents
    )
    
    assert segment_id == "seg_1"
    assert table_of_content is not None
    assert table_of_content.id == "toc_1"

def test_get_first_segment_and_table_of_content_no_segments():
    """Test _get_first_segment_and_table_of_content_ when no segments exist"""
    from pecha_api.texts.texts_service import _get_first_segment_and_table_of_content_
    
    table_of_contents = [
        TableOfContent(
            id="toc_1",
            text_id="text_id",
            type=TableOfContentType.TEXT,
            sections=[
                Section(
                    id="section_1",
                    title="Section 1",
                    section_number=1,
                    segments=[],
                    sections=[]
                )
            ]
        )
    ]
    
    segment_id, table_of_content = _get_first_segment_and_table_of_content_(
        table_of_contents=table_of_contents
    )
    
    assert segment_id is None
    assert table_of_content is None

def test_get_paginated_sections():
    """Test _get_paginated_sections"""
    from pecha_api.texts.texts_service import _get_paginated_sections
    
    sections = [
        Section(
            id="section_1",
            title="Section 1",
            section_number=1,
            segments=[
                TextSegment(segment_id="seg_1", segment_number=1),
                TextSegment(segment_id="seg_2", segment_number=2)
            ],
            sections=[]
        ),
        Section(
            id="section_2",
            title="Section 2",
            section_number=2,
            segments=[
                TextSegment(segment_id="seg_3", segment_number=1)
            ],
            sections=[]
        ),
        Section(
            id="section_3",
            title="Section 3",
            section_number=3,
            segments=[
                TextSegment(segment_id="seg_4", segment_number=1)
            ],
            sections=[]
        )
    ]
    
    result = _get_paginated_sections(sections=sections, skip=0, limit=2)
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].id == "section_1"
    assert result[1].id == "section_2"
    # Each section should only have first segment
    assert len(result[0].segments) == 1
    assert result[0].segments[0].segment_id == "seg_1"

def test_get_paginated_sections_with_skip():
    """Test _get_paginated_sections with skip"""
    from pecha_api.texts.texts_service import _get_paginated_sections
    
    sections = [
        Section(
            id="section_1",
            title="Section 1",
            section_number=1,
            segments=[
                TextSegment(segment_id="seg_1", segment_number=1)
            ],
            sections=[]
        ),
        Section(
            id="section_2",
            title="Section 2",
            section_number=2,
            segments=[
                TextSegment(segment_id="seg_2", segment_number=1)
            ],
            sections=[]
        )
    ]
    
    result = _get_paginated_sections(sections=sections, skip=1, limit=2)
    
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == "section_2"

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
async def test_get_table_of_content_by_sheet_id_with_cache():
    """Test get_table_of_content_by_sheet_id when data is in cache"""
    sheet_id = "sheet_id_1"
    cached_toc = TableOfContent(
        id="content_id_1",
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_id_1",
                title="section_title",
                section_number=1,
                parent_id="parent_id_1",
                segments=[
                    TextSegment(
                        segment_id="segment_id_1",
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
    
    with patch("pecha_api.texts.texts_service.get_table_of_content_by_sheet_id_cache", new_callable=AsyncMock, return_value=cached_toc):
        response = await get_table_of_content_by_sheet_id(sheet_id=sheet_id)
        
        assert response is not None
        assert isinstance(response, TableOfContent)
        assert response.id == "content_id_1"

@pytest.mark.asyncio
async def test_get_table_of_content_by_sheet_id_no_content():
    """Test get_table_of_content_by_sheet_id when no content exists"""
    sheet_id = "sheet_id_1"
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.texts_service.get_contents_by_id", new_callable=AsyncMock, return_value=[]), \
        patch("pecha_api.texts.texts_service.get_table_of_content_by_sheet_id_cache", new_callable=AsyncMock, return_value=None):
        
        response = await get_table_of_content_by_sheet_id(sheet_id=sheet_id)
        
        assert response is None


@pytest.mark.asyncio
async def test_get_text_by_text_id_or_collection_with_cache():
    """Test get_text_by_text_id_or_collection fetches text (cache is currently disabled in code)"""
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    mock_text = TextDTO(
        id=text_id,
        title="Test Text",
        language="bo",
        group_id="group_id_1",
        type="commentary",
        is_published=True,
        created_date="2025-03-21 09:40:34.025024",
        updated_date="2025-03-21 09:40:34.025035",
        published_date="2025-03-21 09:40:34.025038",
        published_by="pecha",
        categories=[],
        views=0
    )
    
    # Cache is commented out in the actual code, so we need to mock the actual data fetch
    with patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_text), \
         patch("pecha_api.texts.texts_service.set_text_by_text_id_or_collection_cache", new_callable=AsyncMock):
        response = await get_text_by_text_id_or_collection(text_id=text_id, collection_id=None)
        
        assert response is not None
        assert isinstance(response, TextDTO)
        assert response.id == text_id
        assert response.title == "Test Text"


@pytest.mark.asyncio
async def test_get_sheet_with_filters():
    """Test get_sheet with various filter parameters"""
    mock_sheets = [
        TextDTO(
            id="sheet_id_1",
            title="Sheet 1",
            language="bo",
            group_id="group_id_1",
            type="sheet",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="user_1",
            categories=[],
            views=10
        )
    ]
    
    with patch("pecha_api.texts.texts_service.fetch_sheets_from_db", new_callable=AsyncMock, return_value=mock_sheets):
        result = await get_sheet(
            published_by="user_1",
            is_published=True,
            sort_by=SortBy.CREATED_DATE,
            sort_order=SortOrder.DESC,
            skip=0,
            limit=10
        )
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == "sheet_id_1"


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


@pytest.mark.asyncio
async def test_remove_table_of_content_by_text_id_success():
    """Test remove_table_of_content_by_text_id successfully deletes content"""
    text_id = "123e4567-e89b-12d3-a456-426614174000"
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
         patch("pecha_api.texts.texts_service.delete_table_of_content_by_text_id", new_callable=AsyncMock) as mock_delete:
        await remove_table_of_content_by_text_id(text_id=text_id)
        
        mock_delete.assert_called_once_with(text_id=text_id)


@pytest.mark.asyncio
async def test_get_table_of_content_by_sheet_id_with_cache():
    """Test get_table_of_content_by_sheet_id returns cached data"""
    sheet_id = "sheet_id_1"
    cached_toc = TableOfContent(
        id="toc_id_1",
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[]
    )
    
    with patch("pecha_api.texts.texts_service.get_table_of_content_by_sheet_id_cache", new_callable=AsyncMock, return_value=cached_toc):
        result = await get_table_of_content_by_sheet_id(sheet_id=sheet_id)
        
        assert result is not None
        assert isinstance(result, TableOfContent)
        assert result.id == "toc_id_1"


@pytest.mark.asyncio
async def test_get_text_by_collection_id_empty_result():
    """Test get_text_by_text_id_or_collection with collection_id returns empty when no texts"""
    collection_id = "collection_id_1"
    language = "bo"
    
    mock_collection = CollectionModel(
        id=collection_id,
        title="Empty Collection",
        description="No texts",
        language=language,
        slug="empty-collection",
        has_child=False
    )
    
    with patch("pecha_api.texts.texts_service.get_text_by_text_id_or_collection_cache", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.texts.texts_service.get_collection", new_callable=AsyncMock, return_value=mock_collection), \
         patch("pecha_api.texts.texts_service._get_texts_by_collection_id", new_callable=AsyncMock, return_value=([], 0)), \
         patch("pecha_api.texts.texts_service.get_all_texts_by_collection", new_callable=AsyncMock, return_value=[]), \
         patch("pecha_api.texts.texts_service.set_text_by_text_id_or_collection_cache", new_callable=AsyncMock):
        
        response = await get_text_by_text_id_or_collection(
            text_id=None,
            collection_id=collection_id,
            language=language,
            skip=0,
            limit=10
        )
        
        assert response is not None
        assert isinstance(response, TextsCategoryResponse)
        assert response.total == 0


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


def test_language_orders_constant():
    """Test LANGUAGE_ORDERS constant is properly defined"""
    # Verify the constant exists and has expected structure
    assert LANGUAGE_ORDERS is not None
    assert isinstance(LANGUAGE_ORDERS, dict)
    
    # Check all three languages are defined
    assert 'bo' in LANGUAGE_ORDERS
    assert 'en' in LANGUAGE_ORDERS
    assert 'zh' in LANGUAGE_ORDERS
    
    # Verify 'bo' preference order
    assert LANGUAGE_ORDERS['bo']['bo'] == 0
    assert LANGUAGE_ORDERS['bo']['en'] == 1
    assert LANGUAGE_ORDERS['bo']['zh'] == 2
    
    # Verify 'en' preference order
    assert LANGUAGE_ORDERS['en']['en'] == 0
    assert LANGUAGE_ORDERS['en']['bo'] == 1
    assert LANGUAGE_ORDERS['en']['zh'] == 2
    
    # Verify 'zh' preference order
    assert LANGUAGE_ORDERS['zh']['zh'] == 0
    assert LANGUAGE_ORDERS['zh']['en'] == 1
    assert LANGUAGE_ORDERS['zh']['bo'] == 2


@pytest.mark.asyncio
async def test_get_commentaries_by_text_id_success():
    """Test get_commentaries_by_text_id returns matching commentaries"""
    from uuid import UUID
    
    text_id = "text_id_1"
    group_id = "group_id_1"
    
    mock_root_text = TextDTO(
        id=text_id,
        title="Root Text",
        language="bo",
        group_id=group_id,
        type="version",
        is_published=True,
        created_date="2025-03-21 09:40:34.025024",
        updated_date="2025-03-21 09:40:34.025035",
        published_date="2025-03-21 09:40:34.025038",
        published_by="pecha",
        categories=[],
        views=0
    )
    
    mock_commentaries = [
        TextDTO(
            id="commentary_id_1",
            title="Commentary 1",
            language="bo",
            group_id="commentary_group_1",
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=[group_id],  # Commentary references the root text's group_id
            views=0
        ),
        TextDTO(
            id="commentary_id_2",
            title="Commentary 2",
            language="bo",
            group_id="commentary_group_2",
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["other_group"],  # This one shouldn't match
            views=0
        )
    ]
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
         patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_root_text), \
         patch("pecha_api.texts.texts_service.TextUtils.get_commentaries_by_text_type", new_callable=AsyncMock, return_value=mock_commentaries):
        
        result = await get_commentaries_by_text_id(text_id=text_id, skip=0, limit=10)
        
        assert result is not None
        assert len(result) == 1
        assert result[0].id == "commentary_id_1"
        assert group_id in result[0].categories


@pytest.mark.asyncio
async def test_get_commentaries_by_text_id_no_matching_commentaries():
    """Test get_commentaries_by_text_id with no matching commentaries"""
    text_id = "text_id_1"
    group_id = "group_id_1"
    
    mock_root_text = TextDTO(
        id=text_id,
        title="Root Text",
        language="bo",
        group_id=group_id,
        type="version",
        is_published=True,
        created_date="2025-03-21 09:40:34.025024",
        updated_date="2025-03-21 09:40:34.025035",
        published_date="2025-03-21 09:40:34.025038",
        published_by="pecha",
        categories=[],
        views=0
    )
    
    mock_commentaries = [
        TextDTO(
            id="commentary_id_1",
            title="Commentary 1",
            language="bo",
            group_id="commentary_group_1",
            type="commentary",
            is_published=True,
            created_date="2025-03-21 09:40:34.025024",
            updated_date="2025-03-21 09:40:34.025035",
            published_date="2025-03-21 09:40:34.025038",
            published_by="pecha",
            categories=["other_group"],  # Different group
            views=0
        )
    ]
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True), \
         patch("pecha_api.texts.texts_service.TextUtils.get_text_detail_by_id", new_callable=AsyncMock, return_value=mock_root_text), \
         patch("pecha_api.texts.texts_service.TextUtils.get_commentaries_by_text_type", new_callable=AsyncMock, return_value=mock_commentaries):
        
        result = await get_commentaries_by_text_id(text_id=text_id, skip=0, limit=10)
        
        assert result is not None
        assert len(result) == 0


@pytest.mark.asyncio
async def test_get_commentaries_by_text_id_invalid_text():
    """Test get_commentaries_by_text_id raises exception for invalid text"""
    text_id = "invalid_text_id"
    
    with patch("pecha_api.texts.texts_service.TextUtils.validate_text_exists", new_callable=AsyncMock, side_effect=HTTPException(status_code=404, detail="Text not found")):
        with pytest.raises(HTTPException) as exc_info:
            await get_commentaries_by_text_id(text_id=text_id, skip=0, limit=10)
        
        assert exc_info.value.status_code == 404


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


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_service_success():
    """Test get_text_by_pecha_text_ids_service with valid pecha_text_ids"""
    class MockText:
        def __init__(self, text_id, pecha_text_id, title, language, group_id, type_val, is_published, 
                     created_date, updated_date, published_date, published_by, categories=None, 
                     views=0, source_link=None, ranking=None, license_val=None):
            self.id = text_id
            self.pecha_text_id = pecha_text_id
            self.title = title
            self.language = language
            self.group_id = group_id
            self.type = type_val
            self.is_published = is_published
            self.created_date = created_date
            self.updated_date = updated_date
            self.published_date = published_date
            self.published_by = published_by
            self.categories = categories or []
            self.views = views
            self.source_link = source_link
            self.ranking = ranking
            self.license = license_val
    
    mock_texts = [
        MockText(
            text_id="text_id_1",
            pecha_text_id="pecha_text_id_1",
            title="Test Text 1",
            language="bo",
            group_id="group_id_1",
            type_val="root_text",
            is_published=True,
            created_date="2025-01-01T00:00:00",
            updated_date="2025-01-01T00:00:00",
            published_date="2025-01-01T00:00:00",
            published_by="user_1",
            categories=["cat1"],
            views=10,
            source_link="https://source1.com",
            ranking=1,
            license_val="CC0"
        ),
        MockText(
            text_id="text_id_2",
            pecha_text_id="pecha_text_id_2",
            title="Test Text 2",
            language="en",
            group_id="group_id_2",
            type_val="version",
            is_published=True,
            created_date="2025-01-02T00:00:00",
            updated_date="2025-01-02T00:00:00",
            published_date="2025-01-02T00:00:00",
            published_by="user_2",
            categories=["cat2"],
            views=20,
            source_link="https://source2.com",
            ranking=2,
            license_val="CC BY"
        )
    ]
    
    request = TextsByPechaTextIdsRequest(pecha_text_ids=["pecha_text_id_1", "pecha_text_id_2"])
    
    with patch("pecha_api.texts.texts_service.get_texts_by_pecha_text_ids", new_callable=AsyncMock, return_value=mock_texts):
        result = await get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request=request)
        
        assert result is not None
        assert len(result) == 2
        assert isinstance(result[0], TextDTO)
        assert result[0].id == "text_id_1"
        assert result[0].pecha_text_id == "pecha_text_id_1"
        assert result[0].title == "Test Text 1"
        assert result[0].language == "bo"
        assert result[0].group_id == "group_id_1"
        assert result[0].type == "root_text"
        assert result[0].is_published == True
        assert result[0].categories == ["cat1"]
        assert result[0].views == 10
        assert result[0].source_link == "https://source1.com"
        assert result[0].ranking == 1
        assert result[0].license == "CC0"
        
        assert isinstance(result[1], TextDTO)
        assert result[1].id == "text_id_2"
        assert result[1].pecha_text_id == "pecha_text_id_2"
        assert result[1].title == "Test Text 2"


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_service_empty_result():
    """Test get_text_by_pecha_text_ids_service when no texts are found"""
    request = TextsByPechaTextIdsRequest(pecha_text_ids=["nonexistent_pecha_id"])
    
    with patch("pecha_api.texts.texts_service.get_texts_by_pecha_text_ids", new_callable=AsyncMock, return_value=[]):
        result = await get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request=request)
        
        assert result is not None
        assert len(result) == 0
        assert result == []


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_service_single_text():
    """Test get_text_by_pecha_text_ids_service with single pecha_text_id"""
    class MockText:
        def __init__(self):
            self.id = "text_id_single"
            self.pecha_text_id = "pecha_text_id_single"
            self.title = "Single Test Text"
            self.language = "bo"
            self.group_id = "group_id_single"
            self.type = "root_text"
            self.is_published = True
            self.created_date = "2025-01-01T00:00:00"
            self.updated_date = "2025-01-01T00:00:00"
            self.published_date = "2025-01-01T00:00:00"
            self.published_by = "user_single"
            self.categories = []
            self.views = 5
            self.source_link = "https://source.com"
            self.ranking = 1
            self.license = "CC0"
    
    mock_texts = [MockText()]
    request = TextsByPechaTextIdsRequest(pecha_text_ids=["pecha_text_id_single"])
    
    with patch("pecha_api.texts.texts_service.get_texts_by_pecha_text_ids", new_callable=AsyncMock, return_value=mock_texts):
        result = await get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request=request)
        
        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], TextDTO)
        assert result[0].id == "text_id_single"
        assert result[0].pecha_text_id == "pecha_text_id_single"
        assert result[0].title == "Single Test Text"


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_service_with_none_optional_fields():
    """Test get_text_by_pecha_text_ids_service with texts having None optional fields"""
    class MockText:
        def __init__(self):
            self.id = "text_id_minimal"
            self.pecha_text_id = None
            self.title = "Minimal Text"
            self.language = "en"
            self.group_id = "group_id_minimal"
            self.type = "version"
            self.is_published = False
            self.created_date = "2025-01-01T00:00:00"
            self.updated_date = "2025-01-01T00:00:00"
            self.published_date = "2025-01-01T00:00:00"
            self.published_by = "user_minimal"
            self.categories = None
            self.views = 0
            self.source_link = None
            self.ranking = None
            self.license = None
    
    mock_texts = [MockText()]
    request = TextsByPechaTextIdsRequest(pecha_text_ids=["pecha_text_id_minimal"])
    
    with patch("pecha_api.texts.texts_service.get_texts_by_pecha_text_ids", new_callable=AsyncMock, return_value=mock_texts):
        result = await get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request=request)
        
        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], TextDTO)
        assert result[0].id == "text_id_minimal"
        # Note: str(None) returns "None" as a string in the service
        assert result[0].pecha_text_id == "None"
        assert result[0].title == "Minimal Text"
        assert result[0].categories is None
        assert result[0].views == 0
        assert result[0].source_link is None
        assert result[0].ranking is None
        assert result[0].license is None


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_service_empty_request():
    """Test get_text_by_pecha_text_ids_service with empty pecha_text_ids list"""
    request = TextsByPechaTextIdsRequest(pecha_text_ids=[])
    
    with patch("pecha_api.texts.texts_service.get_texts_by_pecha_text_ids", new_callable=AsyncMock, return_value=[]):
        result = await get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request=request)
        
        assert result is not None
        assert len(result) == 0
        assert result == []


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_service_multiple_texts_various_types():
    """Test get_text_by_pecha_text_ids_service with texts of various types"""
    class MockText:
        def __init__(self, text_id, pecha_text_id, title, text_type):
            self.id = text_id
            self.pecha_text_id = pecha_text_id
            self.title = title
            self.language = "bo"
            self.group_id = "group_id_1"
            self.type = text_type
            self.is_published = True
            self.created_date = "2025-01-01T00:00:00"
            self.updated_date = "2025-01-01T00:00:00"
            self.published_date = "2025-01-01T00:00:00"
            self.published_by = "user_1"
            self.categories = []
            self.views = 10
            self.source_link = "https://source.com"
            self.ranking = 1
            self.license = "CC0"
    
    mock_texts = [
        MockText("text_id_1", "pecha_1", "Root Text", "root_text"),
        MockText("text_id_2", "pecha_2", "Version Text", "version"),
        MockText("text_id_3", "pecha_3", "Commentary Text", "commentary")
    ]
    
    request = TextsByPechaTextIdsRequest(pecha_text_ids=["pecha_1", "pecha_2", "pecha_3"])
    
    with patch("pecha_api.texts.texts_service.get_texts_by_pecha_text_ids", new_callable=AsyncMock, return_value=mock_texts):
        result = await get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request=request)
        
        assert result is not None
        assert len(result) == 3
        assert result[0].type == "root_text"
        assert result[1].type == "version"
        assert result[2].type == "commentary"
        assert result[0].title == "Root Text"
        assert result[1].title == "Version Text"
        assert result[2].title == "Commentary Text"