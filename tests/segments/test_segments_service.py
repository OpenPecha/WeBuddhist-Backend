import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
import pytest
from pecha_api.texts.segments.segments_service import (
    create_new_segment,
    get_translations_by_segment_id,
    get_segment_details_by_id,
    get_commentaries_by_segment_id,
    get_info_by_segment_id,
    get_root_text_mapping_by_segment_id,
    remove_segments_by_text_id,
    fetch_segments_by_text_id,
    get_segments_details_by_ids,
    update_segments_service
)
from pecha_api.texts.segments.segments_utils import SegmentUtils
from pecha_api.texts.segments.segments_response_models import (
    CreateSegmentRequest,
    SegmentResponse,
    CreateSegment,
    ParentSegment,
    SegmentTranslationsResponse,
    SegmentTranslation,
    SegmentDTO,
    MappingResponse,
    SegmentCommentariesResponse,
    SegmentCommentry,
    SegmentInfoResponse,
    SegmentInfo,
    RelatedText,
    Resources,
    SegmentRootMappingResponse,
    SegmentRootMapping,
    MappedSegmentResponseDTO,
    MappedSegmentDTO,
    SegmentUpdateRequest,
    SegmentUpdate
)

from pecha_api.texts.segments.segments_enum import SegmentType


from pecha_api.texts.texts_response_models import TextDTO

from pecha_api.error_contants import ErrorConstants
from pecha_api.cache.cache_enums import CacheType
from pecha_api.plans.videos.plan_video_response_models import PlanVideoDTO, PlanVideoListResponse


def _mock_source_segment(*, segment_id="seg_1", text_id="text_id_1", content="content"):
    return type("Segment", (), {
        "id": segment_id,
        "text_id": text_id,
        "content": content,
        "mapping": [],
        "type": SegmentType.SOURCE,
    })()


def _text_dto(text_id="text_id_1", **overrides) -> TextDTO:
    defaults = {
        "id": text_id,
        "title": "title",
        "language": "bo",
        "type": "root_text",
        "group_id": "group_id_1",
        "is_published": True,
        "created_date": "2021-01-01",
        "updated_date": "2021-01-01",
        "published_date": "2021-01-01",
        "published_by": "admin",
        "categories": [],
        "views": 0,
    }
    defaults.update(overrides)
    return TextDTO(**defaults)


@pytest.mark.asyncio
async def test_get_translations_by_segment_id_success():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    segment = SegmentDTO(
        id=segment_id,
        text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        content="To the buddhas: Vipaśyin,<br> Śikhin, Viśvabhū,<br>   Krakucchanda, Kanakamuni,<br> and Kāśyapa,<br>   And Śākyamuni—Gautama,<br> deity of all deities,   <br>To the seven warrior-like buddhas, I pay homage!",
        mapping=[],
        type=SegmentType.SOURCE
    )
    translations = [
        SegmentTranslation(
            segment_id=f"efb26a06-f373-450b-ba57-e7a8d4dd5b64_{i}",
            text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            title = f"Title {i}",
            source = f"source {i}",
            language = "en",
            content="To the buddhas: Vipaśyin,<br> Śikhin, Viśvabhū,<br>   Krakucchanda, Kanakamuni,<br> and Kāśyapa,<br>   And Śākyamuni—Gautama,<br> deity of all deities,   <br>To the seven warrior-like buddhas, I pay homage!",
        )
        for i in range(1, 4)
    ]
    with patch("pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.segments.segments_service.get_segment_by_id", new_callable=AsyncMock) as mock_segment, \
        patch("pecha_api.texts.segments.segments_service.SegmentUtils.filter_segment_mapping_by_type_or_text_id", new_callable=AsyncMock) as mock_filter, \
        patch("pecha_api.texts.segments.segments_service.get_related_mapped_segments", new_callable=AsyncMock) as mock_translations:
        mock_segment.return_value = segment
        mock_translations.return_value = translations
        mock_filter.return_value = translations

        response = await get_translations_by_segment_id(segment_id=segment_id)
        
        assert response == SegmentTranslationsResponse(
            parent_segment=ParentSegment(
                segment_id=segment_id,
                content="To the buddhas: Vipaśyin,<br> Śikhin, Viśvabhū,<br>   Krakucchanda, Kanakamuni,<br> and Kāśyapa,<br>   And Śākyamuni—Gautama,<br> deity of all deities,   <br>To the seven warrior-like buddhas, I pay homage!"
            ),
            translations=translations
        )


@pytest.mark.asyncio
async def test_get_translations_by_segment_id_segment_not_found():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"

    with patch("pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as excinfo:
            await get_translations_by_segment_id(segment_id=segment_id)
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE


@pytest.mark.asyncio
async def test_get_translations_by_segment_id_cache_hit():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    cached_response = SegmentTranslationsResponse(
        parent_segment=ParentSegment(segment_id=segment_id, content="cached content"),
        translations=[],
    )

    with patch(
        "pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_translations_by_id_cache",
        new_callable=AsyncMock,
        return_value=cached_response,
    ) as mock_get_cache, patch(
        "pecha_api.texts.segments.segments_service.get_segment_by_id",
        new_callable=AsyncMock,
    ) as mock_get_segment:
        response = await get_translations_by_segment_id(segment_id=segment_id)

        assert response == cached_response
        mock_get_cache.assert_awaited_once()
        mock_get_segment.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_translations_by_segment_id_cache_miss_sets_cache():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    segment = SegmentDTO(
        id=segment_id,
        text_id=segment_id,
        content="parent content",
        mapping=[],
        type=SegmentType.SOURCE,
    )
    translations = [
        SegmentTranslation(
            segment_id=f"{segment_id}_1",
            text_id=segment_id,
            title="Title 1",
            source="source 1",
            language="en",
            content="translation content",
        )
    ]

    with patch(
        "pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_translations_by_id_cache",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_by_id",
        new_callable=AsyncMock,
        return_value=segment,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_related_mapped_segments",
        new_callable=AsyncMock,
        return_value=translations,
    ), patch(
        "pecha_api.texts.segments.segments_service.SegmentUtils.filter_segment_mapping_by_type_or_text_id",
        new_callable=AsyncMock,
        return_value=translations,
    ), patch(
        "pecha_api.texts.segments.segments_service.set_segment_translations_by_id_cache",
        new_callable=AsyncMock,
    ) as mock_set_cache:
        response = await get_translations_by_segment_id(segment_id=segment_id)

        assert response.parent_segment.segment_id == segment_id
        assert response.translations == translations
        mock_set_cache.assert_awaited_once()
        assert mock_set_cache.await_args.kwargs["segment_id"] == segment_id


@pytest.mark.asyncio
async def test_create_new_segment():
    """
    Test case for the create_new_segment function from the segments_service file
    """
    create_segment_request = CreateSegmentRequest(
        text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        segments=[
            CreateSegment(
                content="content", 
                mapping=[],
                type=SegmentType.SOURCE
            )
        ]
    )

    with patch('pecha_api.texts.segments.segments_service.validate_user_exists', return_value=True), \
        patch('pecha_api.texts.segments.segments_service.TextUtils.validate_text_exists', new_callable=AsyncMock, return_value=True), \
        patch('pecha_api.texts.segments.segments_service.create_segment', new_callable=AsyncMock) as mock_create_segment:
        mock_segment = type('Segment', (), {
            'id': uuid.UUID("efb26a06-f373-450b-ba57-e7a8d4dd5b64"),
            'pecha_segment_id': "pecha_efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            'text_id': "efb26a06-f373-450b-ba57-e7a8d4dd5b64",
            'content': "content",
            'mapping': [],
            'type': SegmentType.SOURCE,
            'model_dump': lambda self: {
                'id': self.id,
                'pecha_segment_id': self.pecha_segment_id,
                'text_id': self.text_id,
                'content': self.content,
                'mapping': self.mapping,
                'type': self.type
            }
        })()
        mock_create_segment.return_value = [mock_segment]
        
        response = await create_new_segment(
            create_segment_request=create_segment_request,
            token="admin"
        )
        
        expected_response = SegmentResponse(
            segments=[
                SegmentDTO(
                    id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
                    pecha_segment_id="pecha_efb26a06-f373-450b-ba57-e7a8d4dd5b64",
                    text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
                    content="content",
                    mapping=[],
                    type=SegmentType.SOURCE
                )
            ]
        )
        assert response == expected_response


@pytest.mark.asyncio
async def test_create_new_segment_invalid_user():
    """
    Test case for the create_new_segment function fails due to admin
    """
    create_segment_request = CreateSegmentRequest(
        text_id="efb26a06-f373-450b-ba57-e7a8d4dd5b64",
        segments=[
            CreateSegment(
                content="content", 
                mapping=[],
                type=SegmentType.SOURCE
            )
        ]
    )

    with patch('pecha_api.texts.segments.segments_service.validate_user_exists', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await create_new_segment(
                create_segment_request=create_segment_request,
                token="no_admin"
            )
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

@pytest.mark.asyncio
async def test_validate_segment_exists_success():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch('pecha_api.texts.segments.segments_utils.check_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        result = await SegmentUtils.validate_segment_exists(segment_id)
        assert result is True

@pytest.mark.asyncio
async def test_validate_segment_exists_not_found():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch('pecha_api.texts.segments.segments_utils.check_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segment_exists(segment_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_validate_segments_exists_success():
    segment_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch('pecha_api.texts.segments.segments_utils.check_all_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        result = await SegmentUtils.validate_segments_exists(segment_ids)
        assert result is True

@pytest.mark.asyncio
async def test_validate_segments_exists_not_found():
    segment_ids = ["efb26a06-f373-450b-ba57-e7a8d4dd5b64", "efb26a06-f373-450b-ba57-e7a8d4dd5b65"]
    with patch('pecha_api.texts.segments.segments_utils.check_all_segment_exists', new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await SegmentUtils.validate_segments_exists(segment_ids)
        assert exc_info.value.status_code == 404
        # The error message includes the segment IDs in the format: "Segment not found {segment_ids}"
        assert ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE in exc_info.value.detail
        assert str(segment_ids) in exc_info.value.detail

@pytest.mark.asyncio
async def test_get_segment_details_by_id_without_text_details_success():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"

    with patch('pecha_api.texts.segments.segments_service.fetch_segment_details', new_callable=AsyncMock) as mock_details, \
        patch('pecha_api.texts.segments.segments_service.fetch_segment_content', new_callable=AsyncMock) as mock_content, \
        patch('pecha_api.texts.segments.segments_service.fetch_related_segments', new_callable=AsyncMock) as mock_related:
        mock_details.return_value = {
            "text_id": "text123",
            "pecha_segment_id": f"pecha_{segment_id}",
            "type": "source",
        }
        mock_content.return_value = "test content"
        mock_related.return_value = {"items": [], "has_more": False}

        response = await get_segment_details_by_id(segment_id)
        assert isinstance(response, SegmentDTO)
        assert str(response.id) == segment_id
        assert response.text_id == "text123"
        assert response.content == "test content"
        assert response.mapping == []
        assert response.type == SegmentType.SOURCE

@pytest.mark.asyncio
async def test_get_segment_details_by_id_not_found():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch('pecha_api.texts.segments.segments_service.fetch_segment_details', new_callable=AsyncMock) as mock_details:
        mock_details.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await get_segment_details_by_id(segment_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_get_segment_details_by_id_with_text_details_success():
    segment_id = str(uuid.uuid4())
    text_id = str(uuid.uuid4())
    group_id = str(uuid.uuid4())
    text_payload = {
        "pecha_text_id": "pecha_text_1",
        "title": {"en": "title"},
        "language": "en",
        "group_id": group_id,
        "type": "text",
        "summary": "",
        "is_published": True,
        "created_date": "2021-01-01",
        "updated_date": "2021-01-01",
        "published_date": "2021-01-01",
        "published_by": "admin",
        "categories": ["category1", "category2"],
        "views": 0,
    }
    with patch("pecha_api.texts.segments.segments_service.fetch_segment_details", new_callable=AsyncMock, return_value={"text_id": text_id, "type": "source"}), \
        patch("pecha_api.texts.segments.segments_service.fetch_segment_content", new_callable=AsyncMock, return_value="test content"), \
        patch("pecha_api.texts.segments.segments_service.fetch_related_segments", new_callable=AsyncMock, return_value={"items": [], "has_more": False}), \
        patch("pecha_api.texts.segments.segments_service.fetch_text_by_id", new_callable=AsyncMock, return_value=text_payload):

        response = await get_segment_details_by_id(segment_id=segment_id, text_details=True)
    
        assert response is not None
        assert response.text_id == text_id
        assert response.id == segment_id
        assert response.text is not None
        


@pytest.mark.asyncio
async def test_get_commentaries_by_segment_id_success():
    parent_segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    # repository segment object with id and content attributes
    repo_parent_segment = type('Segment', (), {
        'id': parent_segment_id,
        'content': "parent_segment_content"
    })()
    commentaries = [
        SegmentDTO(
            id=f"id_{i}",
            text_id=f"text_id_{i}",
            content=f"content_{i}",
            mapping=[
                MappingResponse(
                    text_id="parent_text_id",
                    segments=[
                        parent_segment_id
                    ]
                )
            ],
            type=SegmentType.SOURCE
        )
        for i in range(1,6)
    ]
    filtered_commentaries = [
        SegmentCommentry(
            text_id=f"text_id_{i}",
            title=f"title_{i}",
            segments=[
                MappedSegmentDTO(
                    segment_id=f"id_{i}",
                    content=f"content_{i}"
                )
            ],
            language="en",
            count=1
        )
        for i in range(1,6)
    ]
    with patch("pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=True), \
        patch("pecha_api.texts.segments.segments_service.get_segment_by_id", new_callable=AsyncMock) as mock_parent_segment, \
        patch("pecha_api.texts.segments.segments_service.get_related_mapped_segments", new_callable=AsyncMock) as mock_get_related_mapped_segment, \
        patch("pecha_api.texts.segments.segments_service.SegmentUtils.filter_segment_mapping_by_type_or_text_id", new_callable=AsyncMock) as mock_filtered_segment_mapping:
        mock_parent_segment.return_value = repo_parent_segment
        mock_get_related_mapped_segment.return_value = commentaries
        mock_filtered_segment_mapping.return_value = filtered_commentaries
        response = await get_commentaries_by_segment_id(segment_id=parent_segment_id)
        assert isinstance(response, SegmentCommentariesResponse)
        assert response.parent_segment.segment_id == parent_segment_id
        assert response.parent_segment.content == "parent_segment_content"
        assert response.commentaries[0].text_id == "text_id_1"
        assert len(response.commentaries[0].segments) == 1
        assert response.commentaries[0].segments[0].segment_id == "id_1"
        assert response.commentaries[0].segments[0].content == "content_1"
        assert response.commentaries[0].language == "en"
        assert response.commentaries[0].count == 1


@pytest.mark.asyncio
async def test_get_commentaries_by_segment_id_not_found():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_commentaries_by_segment_id(segment_id=segment_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE


@pytest.mark.asyncio
async def test_get_commentaries_by_segment_id_cache_hit():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    cached_response = SegmentCommentariesResponse(
        parent_segment=ParentSegment(segment_id=segment_id, content="cached content"),
        commentaries=[],
    )

    with patch(
        "pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_commentaries_by_id_cache",
        new_callable=AsyncMock,
        return_value=cached_response,
    ) as mock_get_cache, patch(
        "pecha_api.texts.segments.segments_service.get_segment_by_id",
        new_callable=AsyncMock,
    ) as mock_get_segment:
        response = await get_commentaries_by_segment_id(segment_id=segment_id)

        assert response == cached_response
        mock_get_cache.assert_awaited_once()
        mock_get_segment.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_commentaries_by_segment_id_cache_miss_sets_cache():
    parent_segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    repo_parent_segment = type("Segment", (), {
        "id": parent_segment_id,
        "content": "parent_segment_content",
    })()
    filtered_commentaries = [
        SegmentCommentry(
            text_id="text_id_1",
            title="title_1",
            segments=[
                MappedSegmentDTO(segment_id="id_1", content="content_1"),
            ],
            language="en",
            count=1,
        )
    ]

    with patch(
        "pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_commentaries_by_id_cache",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_by_id",
        new_callable=AsyncMock,
        return_value=repo_parent_segment,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_related_mapped_segments",
        new_callable=AsyncMock,
        return_value=[],
    ), patch(
        "pecha_api.texts.segments.segments_service.SegmentUtils.filter_segment_mapping_by_type_or_text_id",
        new_callable=AsyncMock,
        return_value=filtered_commentaries,
    ), patch(
        "pecha_api.texts.segments.segments_service.set_segment_commentaries_by_id_cache",
        new_callable=AsyncMock,
    ) as mock_set_cache:
        response = await get_commentaries_by_segment_id(segment_id=parent_segment_id)

        assert response.commentaries == filtered_commentaries
        mock_set_cache.assert_awaited_once()
        assert mock_set_cache.await_args.kwargs["segment_id"] == parent_segment_id

@pytest.mark.asyncio
async def test_get_infos_by_segment_id_success():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    text_id = "text_id_1"
    text_payload = {
        "translations": ["t1"],
        "commentaries": ["c1", "c2"],
        "commentary_of": None,
        "translation_of": "root-text",
    }

    with patch("pecha_api.texts.segments.segments_service.get_segment_info_by_id_cache", new_callable=AsyncMock, return_value=None), \
        patch("pecha_api.texts.segments.segments_service.fetch_segment_details", new_callable=AsyncMock, return_value={"text_id": text_id}), \
        patch("pecha_api.texts.segments.segments_service.fetch_text_by_id", new_callable=AsyncMock, return_value=text_payload), \
        patch("pecha_api.texts.segments.segments_service.set_segment_info_by_id_cache", new_callable=AsyncMock), \
        patch("pecha_api.texts.segments.segments_service.get_public_plan_videos_by_segment_id", return_value=PlanVideoListResponse(videos=[])):

        response = await get_info_by_segment_id(segment_id=segment_id)
        assert isinstance(response, SegmentInfoResponse)
        assert isinstance(response.segment_info, SegmentInfo)
        assert isinstance(response.segment_info.related_text, RelatedText)
        assert isinstance(response.segment_info.resources, Resources)
        assert response.segment_info.segment_id == segment_id
        assert response.segment_info.text_id == text_id
        assert response.segment_info.translations == 1
        assert response.segment_info.related_text.commentaries == 2
        assert response.segment_info.related_text.root_text == 1
        assert response.segment_info.videos == []


@pytest.mark.asyncio
async def test_get_info_by_segment_id_includes_plan_videos():
    from pecha_api.plans.videos.plan_video_response_models import PlanVideoDTO, PlanVideoListResponse

    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    plan_id = "11111111-1111-1111-1111-111111111111"
    text_id = "22222222-2222-2222-2222-222222222222"

    text_payload = {
        "translations": [],
        "commentaries": [],
        "commentary_of": None,
        "translation_of": None,
    }
    plan_videos = PlanVideoListResponse(videos=[
        PlanVideoDTO(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            plan_id=uuid.UUID(plan_id),
            url="https://youtu.be/abc",
            video_id="abc",
            title="Intro",
            display_order=0,
        )
    ])

    with patch("pecha_api.texts.segments.segments_service.get_segment_info_by_id_cache", new_callable=AsyncMock, return_value=None), \
        patch("pecha_api.texts.segments.segments_service.fetch_segment_details", new_callable=AsyncMock, return_value={"text_id": text_id}), \
        patch("pecha_api.texts.segments.segments_service.fetch_text_by_id", new_callable=AsyncMock, return_value=text_payload), \
        patch("pecha_api.texts.segments.segments_service.set_segment_info_by_id_cache", new_callable=AsyncMock), \
        patch("pecha_api.texts.segments.segments_service.get_public_plan_videos_by_segment_id", return_value=plan_videos) as mock_get_videos:

        response = await get_info_by_segment_id(segment_id=segment_id)

        mock_get_videos.assert_called_once_with(segment_id=segment_id)
        assert len(response.segment_info.videos) == 1
        assert response.segment_info.videos[0].title == "Intro"


@pytest.mark.asyncio
async def test_get_infos_by_segment_id_invalid_segment_id():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_info_by_segment_id(segment_id=segment_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE


@pytest.mark.asyncio
async def test_get_root_text_mapping_by_segment_id_success():
    segment_id = "seg_1"
    text_id = "text_id_1"
    root_text_id = "root_text_1"

    async def text_side_effect(tid):
        if tid == text_id:
            return {"translation_of": None, "commentary_of": root_text_id}
        if tid == root_text_id:
            return {"title": {"en": "Mapped Root"}, "language": "bo"}
        return None

    async def content_side_effect(sid):
        return {
            segment_id: "root segment content",
            "mapped-seg-1": "mapped content",
        }.get(sid)

    with patch(
        "pecha_api.texts.segments.segments_service.get_segment_root_mapping_by_id_cache",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.texts.segments.segments_service.fetch_segment_details",
        new_callable=AsyncMock,
        return_value={"text_id": text_id},
    ), patch(
        "pecha_api.texts.segments.segments_service.fetch_segment_content",
        new_callable=AsyncMock,
        side_effect=content_side_effect,
    ), patch(
        "pecha_api.texts.segments.segments_service.fetch_text_by_id",
        new_callable=AsyncMock,
        side_effect=text_side_effect,
    ), patch(
        "pecha_api.texts.segments.segments_service.fetch_related_segments",
        new_callable=AsyncMock,
        return_value={"items": [{"id": "mapped-seg-1"}], "has_more": False},
    ), patch(
        "pecha_api.texts.segments.segments_service.set_segment_root_mapping_by_id_cache",
        new_callable=AsyncMock,
    ):
        result = await get_root_text_mapping_by_segment_id(segment_id=segment_id)

    assert isinstance(result, SegmentRootMappingResponse)
    assert result.parent_segment.segment_id == segment_id
    assert result.parent_segment.content == "root segment content"
    assert len(result.segment_root_mapping) == 1
    assert result.segment_root_mapping[0].text_id == root_text_id
    assert result.segment_root_mapping[0].title == "Mapped Root"
    assert result.segment_root_mapping[0].language == "bo"
    assert result.segment_root_mapping[0].segments[0].segment_id == "mapped-seg-1"
    assert result.segment_root_mapping[0].segments[0].content == "mapped content"


@pytest.mark.asyncio
async def test_get_root_text_mapping_by_segment_id_invalid_segment_id():
    segment_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_root_text_mapping_by_segment_id(segment_id=segment_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE
        

@pytest.mark.asyncio
async def test_remove_segments_by_text_id_success():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_service.delete_segments_by_text_id", new_callable=AsyncMock, return_value=True),\
        patch("pecha_api.texts.segments.segments_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=True):
        
        response = await remove_segments_by_text_id(text_id=text_id)
        
        assert response is not None
    
@pytest.mark.asyncio
async def test_remove_segments_by_text_id_invalid_text_id():
    text_id = "efb26a06-f373-450b-ba57-e7a8d4dd5b64"
    with patch("pecha_api.texts.segments.segments_service.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await remove_segments_by_text_id(text_id=text_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_fetch_segments_by_text_id_success():
    text_id = "text_id"
    mock_segments = [
        SegmentDTO(
            id=f"id_{i}",
            text_id=f"{text_id}_{i}",
            content=f"content_{i}",
            mapping=[],
            type=SegmentType.SOURCE
        )
        for i in range(1,6)
    ]
    with patch("pecha_api.texts.segments.segments_service.get_segments_by_text_id", new_callable=AsyncMock, return_value=mock_segments):
        response = await fetch_segments_by_text_id(text_id=text_id)

        assert response is not None
        assert len(response) == 5
        assert response[0].id == "id_1"
        assert response[0].text_id == f"{text_id}_1"
        assert response[0].type == SegmentType.SOURCE


@pytest.mark.asyncio
async def test_get_segments_details_by_ids_cache_hit():
    segment_ids = ["id_1", "id_2"]
    cached = {
        "id_1": SegmentDTO(
            id="id_1", text_id="t1", content="c1", mapping=[], type=SegmentType.SOURCE
        ),
        "id_2": SegmentDTO(
            id="id_2", text_id="t2", content="c2", mapping=[], type=SegmentType.SOURCE
        ),
    }

    with patch(
        "pecha_api.texts.segments.segments_service.get_segments_details_by_ids_cache",
        new_callable=AsyncMock,
        return_value=cached,
    ) as mock_cache, patch(
        "pecha_api.texts.segments.segments_service.get_segments_by_ids",
        new_callable=AsyncMock,
    ) as mock_repo:
        result = await get_segments_details_by_ids(segment_ids)
        assert result == cached
        mock_cache.assert_awaited_once()
        mock_repo.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_segments_details_by_ids_cache_miss_sets_cache():
    segment_ids = ["id_1", "id_2"]
    repo_result = {
        "id_1": SegmentDTO(
            id="id_1", text_id="t1", content="c1", mapping=[], type=SegmentType.SOURCE
        ),
        "id_2": SegmentDTO(
            id="id_2", text_id="t2", content="c2", mapping=[], type=SegmentType.SOURCE
        ),
    }

    with patch(
        "pecha_api.texts.segments.segments_service.get_segments_details_by_ids_cache",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_cache, patch(
        "pecha_api.texts.segments.segments_service.get_segments_by_ids",
        new_callable=AsyncMock,
        return_value=repo_result,
    ) as mock_repo, patch(
        "pecha_api.texts.segments.segments_service.set_segments_details_by_ids_cache",
        new_callable=AsyncMock,
    ) as mock_set:
        result = await get_segments_details_by_ids(segment_ids)
        assert result == repo_result
        mock_cache.assert_awaited_once()
        mock_repo.assert_awaited_once_with(segment_ids=segment_ids)
        # ensure cache set called with expected segment_ids
        assert mock_set.await_count == 1
        called_kwargs = mock_set.await_args.kwargs
        assert called_kwargs["segment_ids"] == segment_ids


@pytest.mark.asyncio
async def test_get_info_by_segment_id_cache_hit():
    segment_id = "seg_1"
    cached_response = SegmentInfoResponse(
        segment_info=SegmentInfo(
            segment_id=segment_id,
            text_id="text_id_1",
            translations=0,
            related_text=RelatedText(commentaries=0, root_text=0),
            resources=Resources(sheets=0),
        )
    )

    live_videos = PlanVideoListResponse(videos=[
        PlanVideoDTO(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            plan_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            url="https://youtu.be/fresh",
            video_id="fresh",
            title="Fresh",
            display_order=0,
        )
    ])

    with patch(
        "pecha_api.texts.segments.segments_service.SegmentUtils.validate_segment_exists",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_info_by_id_cache",
        new_callable=AsyncMock,
        return_value=cached_response,
    ), patch(
        "pecha_api.texts.segments.segments_service.get_segment_by_id",
        new_callable=AsyncMock,
    ) as mock_get_segment, patch(
        "pecha_api.texts.segments.segments_service.get_public_plan_videos_by_segment_id",
        return_value=live_videos,
    ) as mock_get_videos:
        result = await get_info_by_segment_id(segment_id)
        assert result == cached_response
        mock_get_segment.assert_not_awaited()
        # videos are attached live even on a cache hit (not served from cache)
        mock_get_videos.assert_called_once_with(segment_id=segment_id)
        assert result.segment_info.videos[0].title == "Fresh"


@pytest.mark.asyncio
async def test_get_info_by_segment_id_sets_cache_on_miss():
    segment_id = "seg_1"
    text_id = "text_id_1"
    text_payload = {
        "translations": [],
        "commentaries": [],
        "commentary_of": None,
        "translation_of": None,
    }

    with patch(
        "pecha_api.texts.segments.segments_service.get_segment_info_by_id_cache",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "pecha_api.texts.segments.segments_service.fetch_segment_details",
        new_callable=AsyncMock,
        return_value={"text_id": text_id},
    ), patch(
        "pecha_api.texts.segments.segments_service.fetch_text_by_id",
        new_callable=AsyncMock,
        return_value=text_payload,
    ), patch(
        "pecha_api.texts.segments.segments_service.set_segment_info_by_id_cache",
        new_callable=AsyncMock,
    ) as mock_set, patch(
        "pecha_api.texts.segments.segments_service.get_public_plan_videos_by_segment_id",
        return_value=PlanVideoListResponse(videos=[
            PlanVideoDTO(
                id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                plan_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                url="https://youtu.be/x",
                video_id="x",
                title="X",
                display_order=0,
            )
        ]),
    ):
        # Real set_cache serializes immediately; capture videos at call time so the
        # later in-place attach on the same object can't leak into this snapshot.
        videos_at_cache_time = {}

        async def _capture(**kwargs):
            videos_at_cache_time["count"] = len(kwargs["data"].segment_info.videos)
        mock_set.side_effect = _capture

        result = await get_info_by_segment_id(segment_id)
        assert isinstance(result, SegmentInfoResponse)
        # ensure cache set was called with the built response
        assert mock_set.await_count == 1
        called_kwargs = mock_set.await_args.kwargs
        assert called_kwargs["segment_id"] == segment_id
        assert called_kwargs["cache_type"] == CacheType.SEGMENT_INFO
        # core option-2 guarantee: videos are NOT in the cached object, but ARE on the response
        assert videos_at_cache_time["count"] == 0
        assert len(result.segment_info.videos) == 1


@pytest.mark.asyncio
async def test_update_segments_service_success():
    """
    Test case for successful segment update with admin access
    """
    segment_update_request = SegmentUpdateRequest(
        pecha_text_id="pecha_text_123",
        segments=[
            SegmentUpdate(
                pecha_segment_id="pecha_segment_123",
                content="Updated content"
            )
        ]
    )
    
    mock_text = type('Text', (), {
        'id': "text_123",
        'pecha_text_id': "pecha_text_123",
        'title': "Test Text"
    })()
    
    mock_updated_segment = type('Segment', (), {
        'id': "segment_id_123",
        'pecha_segment_id': "pecha_segment_123",
        'text_id': "text_123",
        'content': "Updated content",
        'mapping': [],
        'type': SegmentType.SOURCE
    })()
    
    with patch('pecha_api.texts.segments.segments_service.verify_admin_access', return_value=True), \
        patch('pecha_api.texts.segments.segments_service.get_text_by_pecha_text_id', new_callable=AsyncMock, return_value=mock_text), \
        patch('pecha_api.texts.segments.segments_service.update_segment_by_id', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = mock_updated_segment
        
        result = await update_segments_service(
            token="admin_token",
            segment_update_request=segment_update_request
        )
        
        assert result is not None
        mock_update.assert_awaited_once_with(segment_update_request=segment_update_request)


@pytest.mark.asyncio
async def test_update_segments_service_forbidden():
    """
    Test case for segment update with non-admin access
    """
    segment_update_request = SegmentUpdateRequest(
        pecha_text_id="pecha_text_123",
        segments=[
            SegmentUpdate(
                pecha_segment_id="pecha_segment_123",
                content="Updated content"
            )
        ]
    )
    
    with patch('pecha_api.texts.segments.segments_service.verify_admin_access', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await update_segments_service(
                token="user_token",
                segment_update_request=segment_update_request
            )
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == ErrorConstants.ADMIN_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_update_segments_service_text_not_found():
    """
    Test case for segment update with invalid text
    """
    segment_update_request = SegmentUpdateRequest(
        pecha_text_id="invalid_pecha_text_id",
        segments=[
            SegmentUpdate(
                pecha_segment_id="pecha_segment_123",
                content="Updated content"
            )
        ]
    )
    
    with patch('pecha_api.texts.segments.segments_service.verify_admin_access', return_value=True), \
        patch('pecha_api.texts.segments.segments_service.get_text_by_pecha_text_id', new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            await update_segments_service(
                token="admin_token",
                segment_update_request=segment_update_request
            )
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE
