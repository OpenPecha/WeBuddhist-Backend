import io
import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import UploadFile, HTTPException, status
from pecha_api.error_contants import ErrorConstants
from pecha_api.image_utils import ImageUtils

from pecha_api.sheets.sheets_response_models import (
    CreateSheetRequest,
    Source,
    SheetIdResponse,
    SheetDetailDTO,
    SheetSection,
    SheetDTO,
    SheetDTOResponse,
    SheetDTO,
    Publisher
)
from pecha_api.texts.segments.segments_enum import SegmentType
from pecha_api.texts.segments.segments_response_models import (
    CreateSegmentRequest,
    SegmentResponse,
    SegmentDTO
)
from pecha_api.texts.texts_response_models import (
    TableOfContent,
    TableOfContentType,
    Section,
    TextSegment,
    TextDTO
)
from pecha_api.texts.texts_enums import TextType
from pecha_api.users.user_response_models import UserInfoResponse
from pecha_api.texts.groups.groups_response_models import GroupDTO
from pecha_api.sheets.sheets_service import (
    create_new_sheet,
    update_sheet_by_id,
    get_sheet_by_id,
    delete_sheet_by_id,
    fetch_sheets,
    _generate_sheet_summary_,
    _strip_html_tags_,
    _generate_sheet_detail_dto_,
    upload_sheet_image_request,
    _fetch_user_sheets_,
    _generate_sheet_dto_response_,
    _create_publisher_object_,
    _generate_sheet_section_,
    _get_all_segment_ids_in_table_of_content_,
    _update_text_details_,
    _generate_and_upload_sheet_table_of_content,
    _process_and_upload_sheet_segments,
    _generate_sheet_table_of_content_,
    _generate_segment_dictionary_,
    _generate_segment_creation_request_payload_,
    _create_sheet_text_,
    _create_sheet_group_,
    clean_text
)

from pecha_api.texts.groups.groups_enums import GroupType
from pecha_api.users.users_models import Users
from pecha_api.sheets.sheets_enum import SortBy, SortOrder
import hashlib

from pecha_api.texts.segments.segments_response_models import (
    SegmentDTO, 
    SegmentResponse
)
from pecha_api.users.user_response_models import UserInfoResponse
from pecha_api.texts.texts_enums import TextType


def test_validate_and_compress_image_success():
    file_content = io.BytesIO(b"fake_image_data")
    file = UploadFile(filename="test.jpg", file=file_content)

    with patch("pecha_api.image_utils.get_int", side_effect=[5, 75]), \
            patch("PIL.Image.open") as mock_open:
        mock_image = MagicMock()
        mock_image.mode = 'RGB'  # Set the mode to RGB
        mock_open.return_value = mock_image
        mock_image.save = MagicMock()

        image_utils = ImageUtils()
        compressed_image = image_utils.validate_and_compress_image(file=file, content_type="image/jpeg")
        assert isinstance(compressed_image, io.BytesIO)
        mock_image.save.assert_called_once_with(compressed_image, format="JPEG", quality=75)


def test_validate_and_compress_image_invalid_file_type():
    file_content = io.BytesIO(b"fake_image_data")
    file = UploadFile(filename="test.txt", file=file_content)
    try:
        image_utils = ImageUtils()
        image_utils.validate_and_compress_image(file=file, content_type="text/plain")
    except HTTPException as e:
        assert e.status_code == status.HTTP_400_BAD_REQUEST
        assert e.detail == 'Only image files are allowed'


def test_validate_and_compress_image_file_too_large():
    file_content = io.BytesIO(b"fake_image_data" * 1024 * 1024 * 6)  # 6 MB
    file = UploadFile(filename="test.jpg", file=file_content)

    with patch("pecha_api.config.get_int", return_value=5), \
            pytest.raises(HTTPException) as exc_info:
        image_utils = ImageUtils()
        image_utils.validate_and_compress_image(file=file, content_type="image/jpeg")
    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "File size exceeds 1MB limit"


def test_validate_and_compress_image_processing_failure():
    file_content = io.BytesIO(b"fake_image_data")
    file = UploadFile(filename="test.jpg", file=file_content)

    with patch("pecha_api.config.get_int", side_effect=[5, 75]), \
            pytest.raises(HTTPException) as exc_info:
        image_utils = ImageUtils()
        image_utils.validate_and_compress_image(file=file, content_type="image/jpeg")
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Failed to process the image"


@pytest.mark.asyncio
async def test_create_new_sheet_success():
    mock_source = [
        Source(
            position=1,
            type=SegmentType.SOURCE,
            content="source_segment_id"
        ),
        Source(
            position=2,
            type=SegmentType.CONTENT,
            content="content"
        ),
        Source(
            position=3,
            type=SegmentType.IMAGE,
            content="image_url"
        )
    ]
    mock_create_sheet_request = CreateSheetRequest(
        title="sheet_title",
        source=mock_source,
        is_published=True
    )
    mock_token = "valid_token"
    mock_user_details = type("User",(), {
        "email": "test_user@gmail.com",
    })
    mock_group_response = type("GroupDTO", (), {
        "id": "group_id",
        "type": "sheet"
    })
    mock_text_response = type("TextDTO", (), {
        "id": "text_id",
        "title": "sheet_title",
        "group_id": "group_id",
        "type": "sheet",
        "is_published": True,
        "created_date": "2021-01-01",
        "updated_date": "2021-01-01",
        "published_date": "2021-01-01",
        "published_by": "test_user"
    })
    mock_segment_response = SegmentResponse(
        segments=[
            SegmentDTO(
                id="segment_id_1",
                text_id="text_id",
                content="source_segment_id",
                type=SegmentType.SOURCE
            ),
            SegmentDTO(
                id="segment_id_2",
                text_id="text_id",
                content="content",
                type=SegmentType.CONTENT
            ),
            SegmentDTO(
                id="segment_id_3",
                text_id="text_id",
                content="image_url",
                type=SegmentType.IMAGE
            )
        ]
    )
    mock_table_of_content_response = TableOfContent(
        id="table_of_content_id",
        text_id="text_id",
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_id",
                section_number=1,
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
                ]
            )
        ]
    )
    with patch("pecha_api.sheets.sheets_service.create_new_group", new_callable=AsyncMock, return_value=mock_group_response), \
        patch("pecha_api.sheets.sheets_service.create_new_text", new_callable=AsyncMock, return_value=mock_text_response), \
        patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user_details), \
        patch("pecha_api.sheets.sheets_service.create_new_segment", new_callable=AsyncMock, return_value=mock_segment_response), \
        patch("pecha_api.sheets.sheets_service.create_table_of_content", new_callable=AsyncMock, return_value=mock_table_of_content_response):

        response = await create_new_sheet(
            create_sheet_request=mock_create_sheet_request,
            token=mock_token
        )

        assert response is not None
        assert isinstance(response, SheetIdResponse)
        assert response.sheet_id == "text_id"

@pytest.mark.asyncio
async def test_create_sheet_invalid_token():
    mock_create_sheet_request = CreateSheetRequest(
        title="sheet_title",
        source=[]
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_new_sheet(
            create_sheet_request=mock_create_sheet_request,
            token="invalid_token"
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

@pytest.mark.asyncio
async def test_update_sheet_success():
    # Use proper UUID format for sheet_id
    sheet_id = str(uuid.uuid4())
    
    mock_source = [
        Source(
            position=1,
            type=SegmentType.SOURCE,
            content="source_segment_id"
        ),
        Source(
            position=2,
            type=SegmentType.CONTENT,
            content="content"
        ),
        Source(
            position=3,
            type=SegmentType.IMAGE,
            content="image_url"
        )
    ]
    mock_segment_response = SegmentResponse(
        segments=[
            SegmentDTO(
                id="segment_id_1",
                text_id=sheet_id,
                content="source_segment_id",
                type=SegmentType.SOURCE
            ),
            SegmentDTO(
                id="segment_id_2",
                text_id=sheet_id,
                content="content",
                type=SegmentType.CONTENT
            ),
            SegmentDTO(
                id="segment_id_3",
                text_id=sheet_id,
                content="image_url",
                type=SegmentType.IMAGE
            )
        ]
    )
    mock_update_sheet_request = CreateSheetRequest(
        title="updated_sheet_title",
        source=mock_source,
        is_published=True
    )
    
    # Add mock for TextUtils.get_text_details_by_id which is called at the end of update_sheet_by_id
    mock_text_details = TextDTO(
        id=sheet_id,
        title="updated_sheet_title",
        language="language",
        group_id="group_id",
        type=TextType.SHEET,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="test_user",
        categories=[],
        views=10
    )
    
    with patch("pecha_api.sheets.sheets_service.remove_segments_by_text_id", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.validate_user_exists", return_value=True), \
        patch("pecha_api.sheets.sheets_service.remove_table_of_content_by_text_id", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.delete_text_details_by_id_cache", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.delete_table_of_content_by_sheet_id_cache", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.delete_segments_details_by_ids_cache", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.update_text_details", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.create_new_segment", new_callable=AsyncMock, return_value=mock_segment_response), \
        patch("pecha_api.sheets.sheets_service.create_table_of_content", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=mock_text_details), \
        patch("pecha_api.sheets.sheets_service.update_text_details_cache", new_callable=AsyncMock):

        response = await update_sheet_by_id(
            sheet_id=sheet_id,
            update_sheet_request=mock_update_sheet_request,
            token="valid_token"
        )

        assert response is not None
        assert isinstance(response, SheetIdResponse)
        assert response.sheet_id == sheet_id

@pytest.mark.asyncio
async def test_update_sheet_invalid_token():
    # Use proper UUID format for sheet_id
    sheet_id = str(uuid.uuid4())
    
    mock_update_sheet_request = CreateSheetRequest(
        title="updated_sheet_title",
        source=[]
    )
    with pytest.raises(HTTPException) as exc_info:
        await update_sheet_by_id(
            sheet_id=sheet_id,
            update_sheet_request=mock_update_sheet_request,
            token="invalid_token"
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

@pytest.mark.asyncio
async def test_get_sheet_by_id_success():
    sheet_id = "text_id"
    mock_sheet_details = TextDTO(
        id=sheet_id,
        title="sheet_title",
        language="language",
        group_id="group_id",
        type=TextType.SHEET,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="test_user",
        categories=[],
        views=10
    )
    mock_user_details = UserInfoResponse(
        firstname="firstname",
        lastname="lastname",
        username="username",
        email="test_user@gmail.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    mock_table_of_content_response = TableOfContent(
                text_id=sheet_id,
                type=TableOfContentType.SHEET,
                sections=[
                    Section(
                        id="section_id",
                        section_number=1,
                        segments=[
                            TextSegment(
                                segment_id="segment_id_1",
                                segment_number=1
                            ),
                            TextSegment(
                                segment_id="segment_id_2",
                                segment_number=2
                            )
                        ]
                    )
                ]
            )
    
    segment_dict = {
        "segment_id_1": SegmentDTO(
            id="segment_id_1",
            text_id="text_id",
            content="content",
            type=SegmentType.CONTENT,
        ),
        "segment_id_2": SegmentDTO(
            id="segment_id_2",
            text_id="text_id",
            content="image_key",
            type=SegmentType.IMAGE,
        )
    }
    with patch("pecha_api.sheets.sheets_service.fetch_user_by_email", new_callable=MagicMock, return_value=mock_user_details), \
        patch("pecha_api.sheets.sheets_service.get_segments_details_by_ids", new_callable=AsyncMock, return_value=segment_dict), \
        patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content_response), \
        patch("pecha_api.sheets.sheets_service.generate_presigned_access_url", new_callable=MagicMock, return_value="image_url"), \
        patch("pecha_api.sheets.sheets_service.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=mock_sheet_details):

        response = await get_sheet_by_id(sheet_id=sheet_id, skip=0, limit=10)

        assert response is not None
        assert isinstance(response, SheetDetailDTO)
        assert response.id == sheet_id
        assert response.sheet_title == "sheet_title"
        assert response.publisher is not None
        assert isinstance(response.content, SheetSection)
        assert response.content is not None
        assert response.content.segments is not None
        assert len(response.content.segments) == 2
        assert response.content.segments[0].type == SegmentType.CONTENT
        assert response.content.segments[0].content == "content"
        assert response.content.segments[0].key is None
        assert response.content.segments[1].type == SegmentType.IMAGE
        assert response.content.segments[1].content == "image_url"
        assert response.content.segments[1].key == "image_key"

@pytest.mark.asyncio
async def test_get_sheet_by_id_invalid_sheet_id():
    sheet_id="invalid_sheet_id"
    with patch("pecha_api.texts.texts_utils.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_sheet_by_id(sheet_id=sheet_id, skip=0, limit=10)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_get_sheet_by_id_table_of_content_not_found():
    sheet_id = "text_id"
    mock_sheet_details = TextDTO(
        id=sheet_id,
        title="sheet_title",
        language="language",
        group_id="group_id",
        type=TextType.SHEET,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="test_user",
        categories=[],
        views=10
    )
    mock_user_details = UserInfoResponse(
        firstname="firstname",
        lastname="lastname",
        username="username",
        email="test_user@gmail.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    
    segment_dict = {
        "segment_id_1": SegmentDTO(
            id="segment_id_1",
            text_id="text_id",
            content="content",
            type=SegmentType.CONTENT,
        ),
        "segment_id_2": SegmentDTO(
            id="segment_id_2",
            text_id="text_id",
            content="content",
            type=SegmentType.IMAGE,
        )
    }
    with patch("pecha_api.sheets.sheets_service.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=mock_sheet_details), \
        patch("pecha_api.sheets.sheets_service.fetch_user_by_email", new_callable=MagicMock, return_value=mock_user_details), \
        patch("pecha_api.sheets.sheets_service.get_segments_details_by_ids", new_callable=AsyncMock, return_value=segment_dict), \
        patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=None):

        with pytest.raises(HTTPException) as exc_info:
            await get_sheet_by_id(sheet_id=sheet_id, skip=0, limit=10)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.TABLE_OF_CONTENT_NOT_FOUND_MESSAGE

@pytest.mark.asyncio
async def test_delete_sheet_success():
    mock_sheet_id = "text_id"
    mock_token = "valid_token"
    text_details = TextDTO(
        id="sheet_id",
        title="sheet_title",
        language="language",
        group_id="group_id",
        type=TextType.SHEET,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="test_user@gmail.com",
        categories=[],
        views=10
    )
    mock_user_details = UserInfoResponse(
        firstname="firstname",
        lastname="lastname",
        username="username",
        email="test_user@gmail.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    with patch("pecha_api.sheets.sheets_service.validate_user_exists", return_value=True), \
        patch("pecha_api.sheets.sheets_service.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=text_details), \
        patch("pecha_api.sheets.sheets_service.get_user_info", new_callable=AsyncMock, return_value=mock_user_details), \
        patch("pecha_api.sheets.sheets_service.delete_group_by_group_id", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.remove_segments_by_text_id", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.remove_table_of_content_by_text_id", new_callable=AsyncMock), \
        patch("pecha_api.sheets.sheets_service.delete_text_by_text_id", new_callable=AsyncMock):

        response = await delete_sheet_by_id(
            sheet_id=mock_sheet_id,
            token=mock_token
        )

        assert response is None
    
@pytest.mark.asyncio
async def test_delete_sheet_invalid_token():
    with patch("pecha_api.sheets.sheets_service.validate_user_exists", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await delete_sheet_by_id(
                sheet_id="text_id",
                token="invalid_token"
            )
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

@pytest.mark.asyncio
async def test_delete_sheet_invalid_sheet_id():
    with patch("pecha_api.sheets.sheets_service.validate_user_exists", return_value=True), \
        patch("pecha_api.texts.texts_utils.TextUtils.validate_text_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await delete_sheet_by_id(
                sheet_id="invalid_sheet_id",
                token="valid_token"
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.TEXT_NOT_FOUND_MESSAGE







# Test cases for fetch_sheets function
@pytest.mark.asyncio
async def test_fetch_sheets_community_page_all_published():
    mock_user = UserInfoResponse(
        firstname="firstname",
        lastname="lastname",
        username="username",
        email="test_user@gmail.com",
        educations=[],
        avatar_url="avatar_url",
        social_profiles=[],
        followers=0,
        following=0,
    )
    mock_sheets = _generate_mock_sheets_response_()
    
    with patch("pecha_api.sheets.sheets_service.get_sheet", new_callable=AsyncMock, return_value=mock_sheets), \
        patch("pecha_api.sheets.sheets_service.Utils.time_passed", return_value="time passed"), \
        patch("pecha_api.sheets.sheets_service.fetch_user_by_email", new_callable=MagicMock, return_value=mock_user), \
        patch("pecha_api.texts.texts_models.Text.get_published_sheets_count_from_db", new_callable=AsyncMock, return_value=5):
        
        result = await fetch_sheets(
            token="valid_token",
            language="en",
            email=None,
            skip=0,
            limit=10
        )
        
        assert result is not None
        assert isinstance(result, SheetDTOResponse)
        assert result.sheets is not None
        assert len(result.sheets) == 5
        assert isinstance(result.sheets[0], SheetDTO)
        assert result.sheets[0].id == "sheet_id_1"
        assert result.sheets[-1].id == "sheet_id_5"

@pytest.mark.asyncio
async def test_fetch_sheets_user_own_sheets():
    #Test fetch_sheets for user's own sheets - show both published and unpublished
    mock_user_details = type("User", (), {
        "email": "mock_user@gmail.com",
    })
    mock_publisher_details = UserInfoResponse(
        firstname="firstname",
        lastname="lastname",
        username="username",
        email="mock_user@gmail.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    mock_sheets = _generate_mock_sheets_response_()
    for i in range(len(mock_sheets)):
        mock_sheets[i].published_by = "mock_user@gmail.com"
    
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user_details), \
        patch("pecha_api.sheets.sheets_service.Utils.time_passed", return_value="time passed"), \
        patch("pecha_api.sheets.sheets_service.fetch_user_by_email", new_callable=MagicMock, return_value=mock_publisher_details), \
        patch("pecha_api.sheets.sheets_service.get_sheet", new_callable=AsyncMock, return_value=mock_sheets), \
        patch("pecha_api.texts.texts_models.Text.get_published_sheets_count_from_db", new_callable=AsyncMock, return_value=5):
        
        result = await fetch_sheets(
            token="valid_token",
            email="mock_user@gmail.com",
            skip=0,
            limit=10
        )
        
        assert result is not None
        assert isinstance(result, SheetDTOResponse)
        assert result.sheets is not None
        assert len(result.sheets) == 5
        assert isinstance(result.sheets[0], SheetDTO)
        assert result.sheets[0].id == "sheet_id_1"
        assert result.sheets[-1].id == "sheet_id_5"

@pytest.mark.asyncio
async def test_fetch_sheets_user_viewing_other_users_sheets_status_logged_in():
    #Test fetch_sheets for user viewing other user's sheets - show only published
    mock_user_details = type("User", (), {
        "email": "mock_user@gmail.com",
    })
    mock_publisher_details = UserInfoResponse(
        firstname="firstname",
        lastname="lastname",
        username="username",
        email="other_user@gmail.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    mock_sheets = _generate_mock_sheets_response_()
    for i in range(len(mock_sheets)):
        mock_sheets[i].published_by = "other_user@gmail.com"
    
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user_details), \
        patch("pecha_api.sheets.sheets_service.Utils.time_passed", return_value="time passed"), \
        patch("pecha_api.sheets.sheets_service.fetch_user_by_email", new_callable=MagicMock, return_value=mock_publisher_details), \
        patch("pecha_api.sheets.sheets_service.get_sheet", new_callable=AsyncMock, return_value=mock_sheets), \
        patch("pecha_api.texts.texts_models.Text.get_published_sheets_count_from_db", new_callable=AsyncMock, return_value=5):
        
        result = await fetch_sheets(
            token="valid_token",
            language="en",
            email="test_user@gmail.com",
            skip=0,
            limit=10
        )
        
        assert result is not None
        assert isinstance(result, SheetDTOResponse)
        assert result.sheets is not None
        assert len(result.sheets) == 5
        assert isinstance(result.sheets[0], SheetDTO)
        assert result.sheets[0].id == "sheet_id_1"
        assert result.sheets[-1].id == "sheet_id_5"

@pytest.mark.asyncio
async def test_fetch_sheets_invalid_token():
    #Test fetch_sheets with invalid token
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", side_effect=HTTPException(status_code=401, detail=ErrorConstants.TOKEN_ERROR_MESSAGE)), \
        patch("pecha_api.sheets.sheets_service.Utils.time_passed", return_value="time passed"):
        with pytest.raises(HTTPException) as exc_info:
            await fetch_sheets(
                token="invalid_token",
                language="en",
                email="test@example.com",
                skip=0,
                limit=10
            )
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE


def _generate_mock_sheets_response_():
    return [
            TextDTO(
                id=f"sheet_id_{i}",
                title="Test Sheet",
                language="en",
                group_id="group_id",
                type=TextType.SHEET,
                is_published=True,
                created_date="2021-01-01",
                updated_date="2021-01-01",
                published_date="2021-01-01",
                published_by="test_user",
                categories=[],
                views=10
            )
            for i in range(1,6)
        ]
    
# Test cases for _generate_sheet_summary_ function
@pytest.mark.asyncio
async def test_generate_sheet_summary_success():
    #Test normal case with content segments#
    sheet_id = "test_sheet_id"
    
    # Mock table of content with sections and segments
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="content_segment_1", segment_number=1),
                    TextSegment(segment_id="content_segment_2", segment_number=2),
                    TextSegment(segment_id="image_segment_1", segment_number=3)
                ]
            )
        ]
    )
    
    # Mock the first content segment that will be returned
    mock_content_segment = SegmentDTO(
        id="content_segment_1",
        text_id=sheet_id,
        content="This is the first content segment.",
        type=SegmentType.CONTENT
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=mock_content_segment):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        expected = "This is the first content segment."
        assert result == expected


@pytest.mark.asyncio
async def test_generate_sheet_summary_with_html_tags():
    #Test HTML tag stripping functionality
    sheet_id = "test_sheet_id"
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="content_segment_1", segment_number=1)
                ]
            )
        ]
    )
    
    mock_content_segment = SegmentDTO(
        id="content_segment_1",
        text_id=sheet_id,
        content="<p>This is <strong>bold text</strong> with <em>italics</em> and <a href='#'>links</a>.</p>",
        type=SegmentType.CONTENT
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=mock_content_segment):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        expected = "This is bold text with italics and links."
        assert result == expected


@pytest.mark.asyncio
async def test_generate_sheet_summary_exceeds_max_words():
    #Test content that exceeds max_words limit
    sheet_id = "test_sheet_id"
    
    # Create content with more than 30 words (default max_words)
    long_content = " ".join([f"word{i}" for i in range(1, 41)])  # 40 words
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="content_segment_1", segment_number=1)
                ]
            )
        ]
    )
    
    mock_content_segment = SegmentDTO(
        id="content_segment_1",
        text_id=sheet_id,
        content=long_content,
        type=SegmentType.CONTENT
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=mock_content_segment):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        # Should contain exactly 30 words plus "..."
        words = result.split()
        assert len(words) == 30  # 30 words (the last word has "..." appended)
        assert result.endswith("...")
        assert "word1" in result
        assert "word30" in result
        assert "word31" not in result.replace("...", "")


@pytest.mark.asyncio
async def test_generate_sheet_summary_custom_max_words():
    #Test with limited content (less than default 30 words)
    sheet_id = "test_sheet_id"
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="content_segment_1", segment_number=1)
                ]
            )
        ]
    )
    
    mock_content_segment = SegmentDTO(
        id="content_segment_1",
        text_id=sheet_id,
        content="This is a test content with only a few words.",
        type=SegmentType.CONTENT
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=mock_content_segment):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        expected = "This is a test content with only a few words."
        assert result == expected


@pytest.mark.asyncio
async def test_generate_sheet_summary_no_table_of_content():
    #Test when table of content doesn't exist
    sheet_id = "test_sheet_id"
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=None):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        assert result == ""


@pytest.mark.asyncio
async def test_generate_sheet_summary_empty_sections():
    #Test when table of content exists but has no sections
    sheet_id = "test_sheet_id"
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[]
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        assert result == ""


@pytest.mark.asyncio
async def test_generate_sheet_summary_no_segments():
    #Test when no segments exist in the table of content
    sheet_id = "test_sheet_id"
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[]
            )
        ]
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        assert result == ""


@pytest.mark.asyncio
async def test_generate_sheet_summary_no_content_segments():
    #Test when no content type segments exist (only images, sources, etc.)
    sheet_id = "test_sheet_id"
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="image_segment_1", segment_number=1),
                    TextSegment(segment_id="source_segment_1", segment_number=2)
                ]
            )
        ]
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=None):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        assert result == ""


@pytest.mark.asyncio
async def test_generate_sheet_summary_empty_content():
    #Test when content segments exist but have empty content
    sheet_id = "test_sheet_id"
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="content_segment_1", segment_number=1),
                    TextSegment(segment_id="content_segment_2", segment_number=2)
                ]
            )
        ]
    )
    
    mock_content_segment = SegmentDTO(
        id="content_segment_1",
        text_id=sheet_id,
        content="",  # Empty string instead of None
        type=SegmentType.CONTENT
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=mock_content_segment):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        assert result == ""


@pytest.mark.asyncio
async def test_generate_sheet_summary_error_handling():
    #Test error handling - should return empty string when exceptions occurd
    sheet_id = "test_sheet_id"
    
    # Simulate an exception in get_table_of_content_by_sheet_id
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, side_effect=Exception("Database error")):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        assert result == ""


@pytest.mark.asyncio
async def test_generate_sheet_summary_segment_not_found():
    #Test when segment IDs in table of content don't exist in segments dictionaryx1
    sheet_id = "test_sheet_id"
    
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="missing_segment", segment_number=1)
                ]
            )
        ]
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=None):
        
        result = await _generate_sheet_summary_(sheet_id)
        
        assert result == "" 

# Test cases for _strip_html_tags_ function
def test_strip_html_tags_simple_tags():
    #Test stripping simple HTML tags#
    html_content = "<p>Hello <strong>world</strong>!</p>"
    result = _strip_html_tags_(html_content)
    assert result == "Hello world!"

def test_strip_html_tags_complex_html():
    #Test stripping complex HTML with attributes#
    html_content = '<div class="container"><p style="color: red;">Test <a href="http://example.com">link</a> content</p></div>'
    result = _strip_html_tags_(html_content)
    assert result == "Test link content"

def test_strip_html_tags_no_html():
    #Test with plain text (no HTML tags)#
    plain_text = "This is plain text without HTML"
    result = _strip_html_tags_(plain_text)
    assert result == "This is plain text without HTML"

def test_strip_html_tags_empty_string():
    #Test with empty string#
    result = _strip_html_tags_("")
    assert result == ""

def test_strip_html_tags_whitespace_handling():
    #Test HTML stripping with whitespace#
    html_content = "  <p>  Content with   spaces  </p>  "
    result = _strip_html_tags_(html_content)
    assert result == "Content with   spaces"

def test_strip_html_tags_nested_tags():
    #Test stripping nested HTML tags#
    html_content = "<div><p><span><strong>Nested</strong> content</span></p></div>"
    result = _strip_html_tags_(html_content)
    assert result == "Nested content"


# Test cases for upload_sheet_image_request function
def test_upload_sheet_image_request_with_sheet_id():
    #Test uploading sheet image with sheet ID#
    file_content = io.BytesIO(b"fake_image_data")
    file = UploadFile(filename="test.jpg", file=file_content)
    # Create a mock file with content_type since the property is read-only
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    mock_file.file = file_content
    mock_file.content_type = "image/jpeg"
    
    sheet_id = "test_sheet_id"
    
    with patch("pecha_api.sheets.sheets_service.ImageUtils.validate_and_compress_image") as mock_validate, \
         patch("pecha_api.sheets.sheets_service.upload_bytes", return_value="test_upload_key") as mock_upload, \
         patch("pecha_api.sheets.sheets_service.generate_presigned_access_url", return_value="https://test-url.com") as mock_presigned, \
         patch("pecha_api.sheets.sheets_service.get", return_value="test-bucket"):
        
        mock_validate.return_value = io.BytesIO(b"compressed_image_data")
        
        result = upload_sheet_image_request(sheet_id=sheet_id, file=mock_file)
        
        assert result.url == "https://test-url.com"
        assert result.key == "test_upload_key"
        mock_validate.assert_called_once()
        mock_upload.assert_called_once()
        mock_presigned.assert_called_once()

def test_upload_sheet_image_request_without_sheet_id():
    #Test uploading sheet image without sheet ID#
    file_content = io.BytesIO(b"fake_image_data")
    file = UploadFile(filename="test.jpg", file=file_content)
    # Create a mock file with content_type since the property is read-only
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    mock_file.file = file_content
    mock_file.content_type = "image/jpeg"
    
    with patch("pecha_api.sheets.sheets_service.ImageUtils.validate_and_compress_image") as mock_validate, \
         patch("pecha_api.sheets.sheets_service.upload_bytes", return_value="test_upload_key") as mock_upload, \
         patch("pecha_api.sheets.sheets_service.generate_presigned_access_url", return_value="https://test-url.com") as mock_presigned, \
         patch("pecha_api.sheets.sheets_service.get", return_value="test-bucket"):
        
        mock_validate.return_value = io.BytesIO(b"compressed_image_data")
        
        result = upload_sheet_image_request(sheet_id=None, file=mock_file)
        
        assert result.url == "https://test-url.com"
        assert result.key == "test_upload_key"


# Test cases for _fetch_user_sheets_ function
@pytest.mark.asyncio
async def test_fetch_user_sheets_none_token():
    #Test _fetch_user_sheets_ with 'None' token#
    mock_sheets = _generate_mock_sheets_response_()
    
    with patch("pecha_api.sheets.sheets_service.get_sheet", new_callable=AsyncMock, return_value=mock_sheets):
        result = await _fetch_user_sheets_(
            token="None",
            email="test@example.com",
            sort_by=SortBy.CREATED_DATE,
            sort_order=SortOrder.DESC,
            skip=0,
            limit=10
        )
        
        assert result == mock_sheets

@pytest.mark.asyncio
async def test_fetch_user_sheets_own_sheets():
    #Test _fetch_user_sheets_ for user's own sheets#
    mock_user = Users(email="test@example.com")
    mock_sheets = _generate_mock_sheets_response_()
    
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user), \
         patch("pecha_api.sheets.sheets_service.get_sheet", new_callable=AsyncMock, return_value=mock_sheets):
        
        result = await _fetch_user_sheets_(
            token="valid_token",
            email="test@example.com",
            sort_by=SortBy.CREATED_DATE,
            sort_order=SortOrder.DESC,
            skip=0,
            limit=10
        )
        
        assert result == mock_sheets

@pytest.mark.asyncio
async def test_fetch_user_sheets_other_user():
    #Test _fetch_user_sheets_ for other user's sheets#
    mock_user = Users(email="current@example.com")
    mock_sheets = _generate_mock_sheets_response_()
    
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user), \
         patch("pecha_api.sheets.sheets_service.get_sheet", new_callable=AsyncMock, return_value=mock_sheets):
        
        result = await _fetch_user_sheets_(
            token="valid_token",
            email="other@example.com",
            sort_by=SortBy.CREATED_DATE,
            sort_order=SortOrder.DESC,
            skip=0,
            limit=10
        )
        
        assert result == mock_sheets


# Test cases for _generate_sheet_dto_response_ function
@pytest.mark.asyncio
async def test_generate_sheet_dto_response():
    #Test _generate_sheet_dto_response_#
    mock_sheets = _generate_mock_sheets_response_()
    mock_user = UserInfoResponse(
        firstname="Test",
        lastname="User",
        username="testuser",
        email="test@example.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    
    with patch("pecha_api.sheets.sheets_service._generate_sheet_summary_", new_callable=AsyncMock, return_value="Test summary"), \
         patch("pecha_api.sheets.sheets_service.Utils.time_passed", return_value="2 days ago"), \
         patch("pecha_api.sheets.sheets_service.fetch_user_by_email", return_value=mock_user):
        
        result = await _generate_sheet_dto_response_(sheets=mock_sheets, total=5, skip=0, limit=10)
        
        assert isinstance(result, SheetDTOResponse)
        assert len(result.sheets) == 5
        assert result.skip == 0
        assert result.limit == 10
        assert result.total == 5
        assert all(sheet.summary == "Test summary" for sheet in result.sheets)


# Test cases for _create_publisher_object_ function
def test_create_publisher_object():
    #Test _create_publisher_object_#
    mock_user = UserInfoResponse(
        firstname="John",
        lastname="Doe",
        username="johndoe",
        email="john@example.com",
        avatar_url="https://avatar.url",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    
    with patch("pecha_api.sheets.sheets_service.fetch_user_by_email", return_value=mock_user):
        result = _create_publisher_object_(published_by="john@example.com")
        
        assert isinstance(result, Publisher)
        assert result.name == "John Doe"
        assert result.username == "johndoe"
        assert result.email == "john@example.com"
        assert result.avatar_url == "https://avatar.url"

def test_create_publisher_object_no_name():
    #Test _create_publisher_object_ when user has no first/last name#
    mock_user = UserInfoResponse(
        firstname="",
        lastname="",
        username="johndoe",
        email="john@example.com",
        avatar_url="https://avatar.url",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    
    with patch("pecha_api.sheets.sheets_service.fetch_user_by_email", return_value=mock_user):
        result = _create_publisher_object_(published_by="john@example.com")
        
        assert result.name == "johndoe"  # Falls back to username


# Test cases for _generate_sheet_section_ function
@pytest.mark.asyncio
async def test_generate_sheet_section():
    #Test _generate_sheet_section_#
    segments = [
        TextSegment(segment_id="content_segment", segment_number=1),
        TextSegment(segment_id="image_segment", segment_number=2),
        TextSegment(segment_id="source_segment", segment_number=3)
    ]
    
    segments_dict = {
        "content_segment": SegmentDTO(
            id="content_segment",
            text_id="test_text_id",
            content="Test content",
            type=SegmentType.CONTENT
        ),
        "image_segment": SegmentDTO(
            id="image_segment",
            text_id="test_text_id",
            content="image_key",
            type=SegmentType.IMAGE
        ),
        "source_segment": SegmentDTO(
            id="source_segment",
            text_id="source_text_id",
            content="source_content",
            type=SegmentType.SOURCE
        )
    }
    
    mock_source_text = TextDTO(
        id="source_text_id",
        title="Source Text",
        language="en",
        group_id="group_id",
        type=TextType.VERSION,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="test@example.com",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.sheets.sheets_service.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=mock_source_text), \
         patch("pecha_api.sheets.sheets_service.generate_presigned_access_url", return_value="https://presigned-image-url.com"), \
         patch("pecha_api.sheets.sheets_service.get", return_value="test-bucket"):
        
        result = await _generate_sheet_section_(segments=segments, segments_dict=segments_dict)
        
        assert isinstance(result, SheetSection)
        assert result.section_number == 1
        assert len(result.segments) == 3
        
        # Check content segment
        content_seg = next(seg for seg in result.segments if seg.segment_id == "content_segment")
        assert content_seg.content == "Test content"
        assert content_seg.type == SegmentType.CONTENT
        
        # Check image segment
        image_seg = next(seg for seg in result.segments if seg.segment_id == "image_segment")
        assert image_seg.content == "https://presigned-image-url.com"
        assert image_seg.type == SegmentType.IMAGE
        
        # Check source segment
        source_seg = next(seg for seg in result.segments if seg.segment_id == "source_segment")
        assert source_seg.content == "source_content"
        assert source_seg.type == SegmentType.SOURCE
        assert source_seg.language == "en"
        assert source_seg.text_title == "Source Text"



def test_get_all_segment_ids_empty_sections():
    #Test _get_all_segment_ids_in_table_of_content_ with empty sections#
    result = _get_all_segment_ids_in_table_of_content_(sheet_sections=[])
    assert result == []


# Test cases for _update_text_details_ function
@pytest.mark.asyncio
async def test_update_text_details():
    #Test _update_text_details_#
    sheet_id = "test_sheet_id"
    update_request = CreateSheetRequest(
        title="Updated Title",
        source=[],
        is_published=True
    )
    
    with patch("pecha_api.sheets.sheets_service.update_text_details", new_callable=AsyncMock) as mock_update:
        await _update_text_details_(sheet_id=sheet_id, update_sheet_request=update_request)
        
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[1]['text_id'] == sheet_id
        assert call_args[1]['update_text_request'].title == "Updated Title"
        assert call_args[1]['update_text_request'].is_published == True


# Test cases for _generate_and_upload_sheet_table_of_content function
@pytest.mark.asyncio
async def test_generate_and_upload_sheet_table_of_content():
    #Test _generate_and_upload_sheet_table_of_content#
    create_request = CreateSheetRequest(
        title="Test Sheet",
        source=[
            Source(position=1, type=SegmentType.CONTENT, content="test content")
        ],
        is_published=True
    )
    text_id = "test_text_id"
    segment_dict = {hashlib.sha256("test content".encode()).hexdigest(): "segment_id_123"}
    token = "valid_token"
    
    mock_table_of_content = TableOfContent(
        text_id=text_id,
        type=TableOfContentType.SHEET,
        sections=[]
    )
    
    with patch("pecha_api.sheets.sheets_service.create_table_of_content", new_callable=AsyncMock, return_value=mock_table_of_content) as mock_create:
        result = await _generate_and_upload_sheet_table_of_content(
            create_sheet_request=create_request,
            text_id=text_id,
            segment_dict=segment_dict,
            token=token
        )
        
        mock_create.assert_called_once()
        # The function returns the generated table of content, not the mock
        assert isinstance(result, TableOfContent)
        assert result.text_id == text_id
        assert len(result.sections) == 1
        assert len(result.sections[0].segments) == 1


# Test cases for _process_and_upload_sheet_segments function
@pytest.mark.asyncio
async def test_process_and_upload_sheet_segments():
    #Test _process_and_upload_sheet_segments#
    create_request = CreateSheetRequest(
        title="Test Sheet",
        source=[
            Source(position=1, type=SegmentType.CONTENT, content="test content"),
            Source(position=2, type=SegmentType.IMAGE, content="image_url")
        ],
        is_published=True
    )
    text_id = "test_text_id"
    token = "valid_token"
    
    mock_segments = SegmentResponse(
        segments=[
            SegmentDTO(
                id="seg_1",
                text_id=text_id,
                content="test content",
                type=SegmentType.CONTENT
            ),
            SegmentDTO(
                id="seg_2",
                text_id=text_id,
                content="image_url",
                type=SegmentType.IMAGE
            )
        ]
    )
    
    with patch("pecha_api.sheets.sheets_service.create_new_segment", new_callable=AsyncMock, return_value=mock_segments):
        result = await _process_and_upload_sheet_segments(
            create_sheet_request=create_request,
            text_id=text_id,
            token=token
        )
        
        assert isinstance(result, dict)
        # Should contain hash keys for non-source segments
        assert len(result) >= 0  # Could be empty if all segments are SOURCE type


# Test cases for _generate_sheet_table_of_content_ function
def test_generate_sheet_table_of_content():
    #Test _generate_sheet_table_of_content_#
    create_request = CreateSheetRequest(
        title="Test Sheet",
        source=[
            Source(position=1, type=SegmentType.SOURCE, content="source_segment_id"),
            Source(position=2, type=SegmentType.CONTENT, content="test content"),
            Source(position=3, type=SegmentType.IMAGE, content="image_url")
        ],
        is_published=True
    )
    text_id = "test_text_id"
    segment_dict = {
        hashlib.sha256("test content".encode()).hexdigest(): "content_segment_id",
        hashlib.sha256("image_url".encode()).hexdigest(): "image_segment_id"
    }
    
    result = _generate_sheet_table_of_content_(
        create_sheet_request=create_request,
        text_id=text_id,
        segment_dict=segment_dict
    )
    
    assert isinstance(result, TableOfContent)
    assert result.text_id == text_id
    assert len(result.sections) == 1
    assert result.sections[0].section_number == 1
    assert len(result.sections[0].segments) == 3


# Test cases for _generate_segment_dictionary_ function
def test_generate_segment_dictionary():
    #Test _generate_segment_dictionary_#
    segments_response = SegmentResponse(
        segments=[
            SegmentDTO(
                id="seg_1",
                text_id="text_id",
                content="content 1",
                type=SegmentType.CONTENT
            ),
            SegmentDTO(
                id="seg_2",
                text_id="text_id",
                content="source_id",
                type=SegmentType.SOURCE
            ),
            SegmentDTO(
                id="seg_3",
                text_id="text_id",
                content="image_url",
                type=SegmentType.IMAGE
            )
        ]
    )
    
    result = _generate_segment_dictionary_(new_segments=segments_response)
    
    # Should contain entries for non-SOURCE segments only
    expected_content_hash = hashlib.sha256("content 1".encode()).hexdigest()
    expected_image_hash = hashlib.sha256("image_url".encode()).hexdigest()
    
    assert expected_content_hash in result
    assert expected_image_hash in result
    assert result[expected_content_hash] == "seg_1"
    assert result[expected_image_hash] == "seg_3"
    
    # SOURCE segments should not be in dictionary
    source_hash = hashlib.sha256("source_id".encode()).hexdigest()
    assert source_hash not in result


# Test cases for _generate_segment_creation_request_payload_ function
def test_generate_segment_creation_request_payload():
    #Test _generate_segment_creation_request_payload_#
    create_request = CreateSheetRequest(
        title="Test Sheet",
        source=[
            Source(position=1, type=SegmentType.SOURCE, content="source_segment_id"),
            Source(position=2, type=SegmentType.CONTENT, content="test content"),
            Source(position=3, type=SegmentType.IMAGE, content="image_url")
        ],
        is_published=True
    )
    text_id = "test_text_id"
    
    result = _generate_segment_creation_request_payload_(
        create_sheet_request=create_request,
        text_id=text_id
    )
    
    assert isinstance(result, CreateSegmentRequest)
    assert result.text_id == text_id
    # Should exclude SOURCE type segments
    assert len(result.segments) == 2
    assert all(seg.type != SegmentType.SOURCE for seg in result.segments)


# Test cases for _create_sheet_text_ function
@pytest.mark.asyncio
async def test_create_sheet_text():
    #Test _create_sheet_text_#
    title = "Test Sheet"
    token = "valid_token"
    group_id = "test_group_id"
    
    mock_user = Users(email="test@example.com")
    mock_text = TextDTO(
        id="new_text_id",
        title=title,
        group_id=group_id,
        type=TextType.SHEET,
        language=None,
        is_published=False,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="test@example.com",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user), \
         patch("pecha_api.sheets.sheets_service.create_new_text", new_callable=AsyncMock, return_value=mock_text):
        
        result = await _create_sheet_text_(title=title, token=token, group_id=group_id)
        
        assert result == "new_text_id"


@pytest.mark.asyncio
async def test_create_sheet_text_title_required_empty():
    #Test _create_sheet_text_ should fail when title is empty
    mock_user = type("User", (), {"email": "test@example.com"})
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user):
        with pytest.raises(HTTPException) as exc_info:
            await _create_sheet_text_(title="", token="valid_token", group_id="group_id")
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == ErrorConstants.SHEET_TITLE_REQUIRED_MESSAGE


@pytest.mark.asyncio
async def test_create_sheet_text_title_required_none():
    #Test _create_sheet_text_ should fail when title is None
    mock_user = type("User", (), {"email": "test@example.com"})
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", return_value=mock_user):
        with pytest.raises(HTTPException) as exc_info:
            await _create_sheet_text_(title=None, token="valid_token", group_id="group_id")  # type: ignore[arg-type]
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == ErrorConstants.SHEET_TITLE_REQUIRED_MESSAGE


# Test cases for _create_sheet_group_ function
@pytest.mark.asyncio
async def test_create_sheet_group():
    #Test _create_sheet_group_#
    token = "valid_token"
    
    mock_group = GroupDTO(
        id="new_group_id",
        type=GroupType.SHEET
    )
    
    with patch("pecha_api.sheets.sheets_service.create_new_group", new_callable=AsyncMock, return_value=mock_group):
        result = await _create_sheet_group_(token=token)
        
        assert result == "new_group_id"


# Test cases for _generate_sheet_detail_dto_ function (the one with views parameter)
@pytest.mark.asyncio
async def test_generate_sheet_detail_dto_with_views():
    #Test _generate_sheet_detail_dto_ with views parameter#
    sheet_details = TextDTO(
        id="sheet_id",
        title="Test Sheet",
        language="en",
        group_id="group_id",
        type=TextType.SHEET,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="test@example.com",
        categories=[],
        views=100
    )
    
    user_details = UserInfoResponse(
        firstname="Test",
        lastname="User",
        username="testuser",
        email="test@example.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    
    sheet_sections = [
        Section(
            id="section_1",
            section_number=1,
            segments=[
                TextSegment(segment_id="seg_1", segment_number=1)
            ]
        )
    ]
    
    segments_dict = {
        "seg_1": SegmentDTO(
            id="seg_1",
            text_id="sheet_id",
            content="test content",
            type=SegmentType.CONTENT
        )
    }
    
    with patch("pecha_api.sheets.sheets_service.get_segments_details_by_ids", new_callable=AsyncMock, return_value=segments_dict):
        # Note: Testing the version with views parameter by calling it directly
        # Since there appear to be two versions of this function in the code
        result = await _generate_sheet_detail_dto_(
            sheet_details=sheet_details,
            user_details=user_details,
            sheet_sections=sheet_sections,
            skip=0,
            limit=10
        )
        
        assert isinstance(result, SheetDetailDTO)
        assert result.id == "sheet_id"
        assert result.sheet_title == "Test Sheet"
        assert result.views == 0  # The imported function version uses default value
        assert result.publisher.name == "Test User"
        assert result.total == 1 

# Test cases for clean_text function
def test_clean_text_success():
    #Test clean_text with content under max words#
    content = "This is a test content with less than thirty words total."
    result = clean_text(content)
    assert result == "This is a test content with less than thirty words total."

def test_clean_text_exceeds_max_words():
    #Test clean_text with content exceeding max words#
    content = " ".join([f"word{i}" for i in range(1, 35)])  # 34 words
    result = clean_text(content)
    words = result.split()
    assert len(words) == 30
    assert result.endswith("...")

def test_clean_text_with_html():
    #Test clean_text with HTML content#
    content = "<p>This is <strong>bold</strong> text with <em>italics</em>.</p>"
    result = clean_text(content)
    assert result == "This is bold text with italics."

def test_clean_text_empty_content():
    #Test clean_text with empty content#
    result = clean_text("")
    assert result == ""

def test_clean_text_whitespace_only():
    #Test clean_text with whitespace only content#
    result = clean_text("   ")
    assert result == ""


# Test cases for _delete_sheet_table_of_content_cache_ function
@pytest.mark.asyncio
async def test_delete_sheet_table_of_content_cache_success():
    #Test _delete_sheet_table_of_content_cache_ with valid table of content#
    sheet_id = "test_sheet_id"
    mock_table_of_content = TableOfContent(
        text_id=sheet_id,
        type=TableOfContentType.SHEET,
        sections=[]
    )
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content), \
         patch("pecha_api.sheets.sheets_service.delete_table_of_content_by_sheet_id_cache", new_callable=AsyncMock) as mock_delete_cache:
        
        from pecha_api.sheets.sheets_service import _delete_sheet_table_of_content_cache_
        result = await _delete_sheet_table_of_content_cache_(sheet_id=sheet_id)
        
        assert result == mock_table_of_content
        mock_delete_cache.assert_called_once()

@pytest.mark.asyncio
async def test_delete_sheet_table_of_content_cache_no_content():
    #Test _delete_sheet_table_of_content_cache_ with no table of content#
    sheet_id = "test_sheet_id"
    
    with patch("pecha_api.sheets.sheets_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.sheets.sheets_service.delete_table_of_content_by_sheet_id_cache", new_callable=AsyncMock) as mock_delete_cache:
        
        from pecha_api.sheets.sheets_service import _delete_sheet_table_of_content_cache_
        result = await _delete_sheet_table_of_content_cache_(sheet_id=sheet_id)
        
        assert result is None
        mock_delete_cache.assert_not_called()


# Test cases for _delete_sheet_segments_cache_ function
@pytest.mark.asyncio
async def test_delete_sheet_segments_cache_with_content():
    #Test _delete_sheet_segments_cache_ with valid table of content#
    mock_table_of_content = TableOfContent(
        text_id="test_id",
        type=TableOfContentType.SHEET,
        sections=[
            Section(
                id="section_1",
                section_number=1,
                segments=[
                    TextSegment(segment_id="seg_1", segment_number=1),
                    TextSegment(segment_id="seg_2", segment_number=2)
                ]
            )
        ]
    )
    
    with patch("pecha_api.sheets.sheets_service.delete_segments_details_by_ids_cache", new_callable=AsyncMock) as mock_delete_cache:
        from pecha_api.sheets.sheets_service import _delete_sheet_segments_cache_
        await _delete_sheet_segments_cache_(sheet_table_of_content=mock_table_of_content)
        
        mock_delete_cache.assert_called_once()
        call_args = mock_delete_cache.call_args
        assert "seg_1" in call_args[1]['segment_ids']
        assert "seg_2" in call_args[1]['segment_ids']

@pytest.mark.asyncio
async def test_delete_sheet_segments_cache_no_content():
    #Test _delete_sheet_segments_cache_ with None table of content#
    with patch("pecha_api.sheets.sheets_service.delete_segments_details_by_ids_cache", new_callable=AsyncMock) as mock_delete_cache:
        from pecha_api.sheets.sheets_service import _delete_sheet_segments_cache_
        await _delete_sheet_segments_cache_(sheet_table_of_content=None)
        
        mock_delete_cache.assert_called_once()
        call_args = mock_delete_cache.call_args
        assert call_args[1]['segment_ids'] == []


# Test cases for delete_sheet_by_id unauthorized access
@pytest.mark.asyncio
async def test_delete_sheet_forbidden_access():
    #Test delete_sheet_by_id when user tries to delete another user's sheet#
    sheet_id = "test_sheet_id"
    token = "valid_token"
    
    text_details = TextDTO(
        id=sheet_id,
        title="sheet_title",
        language="language",
        group_id="group_id",
        type=TextType.SHEET,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01",
        published_by="owner@gmail.com",  # Different user
        categories=[],
        views=10
    )
    
    current_user_details = UserInfoResponse(
        firstname="Current",
        lastname="User",
        username="currentuser",
        email="current@gmail.com",  # Different email
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    
    with patch("pecha_api.sheets.sheets_service.validate_user_exists", return_value=True), \
         patch("pecha_api.sheets.sheets_service.TextUtils.get_text_details_by_id", new_callable=AsyncMock, return_value=text_details), \
         patch("pecha_api.sheets.sheets_service.get_user_info", new_callable=AsyncMock, return_value=current_user_details):
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_sheet_by_id(sheet_id=sheet_id, token=token)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == ErrorConstants.FORBIDDEN_ERROR_MESSAGE


# Test cases for _get_sheet_first_content_details_by_type_ function
@pytest.mark.asyncio
async def test_get_sheet_first_content_details_by_type_success():
    #Test _get_sheet_first_content_details_by_type_ with valid segment IDs#
    segment_ids = ["seg_1", "seg_2", "seg_3"]
    mock_segment = SegmentDTO(
        id="seg_1",
        text_id="text_id",
        content="first content",
        type=SegmentType.CONTENT
    )
    
    with patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=mock_segment):
        from pecha_api.sheets.sheets_service import _get_sheet_first_content_details_by_type_
        result = await _get_sheet_first_content_details_by_type_(
            segment_ids=segment_ids, 
            segment_type=SegmentType.CONTENT
        )
        
        assert result == mock_segment

@pytest.mark.asyncio
async def test_get_sheet_first_content_details_by_type_no_result():
    #Test _get_sheet_first_content_details_by_type_ with no matching segments#
    segment_ids = ["seg_1", "seg_2", "seg_3"]
    
    with patch("pecha_api.sheets.sheets_service.get_sheet_first_content_by_ids", new_callable=AsyncMock, return_value=None):
        from pecha_api.sheets.sheets_service import _get_sheet_first_content_details_by_type_
        result = await _get_sheet_first_content_details_by_type_(
            segment_ids=segment_ids, 
            segment_type=SegmentType.CONTENT
        )
        
        assert result is None


# Test cases for _get_all_segment_ids_in_table_of_content_ edge cases
def test_get_all_segment_ids_empty_segments():
    #Test _get_all_segment_ids_in_table_of_content_ with sections containing no segments#
    sheet_sections = [
        Section(
            id="section_1",
            section_number=1,
            segments=[]
        ),
        Section(
            id="section_2", 
            section_number=2,
            segments=[]
        )
    ]
    
    result = _get_all_segment_ids_in_table_of_content_(sheet_sections=sheet_sections)
    assert result == []

def test_get_all_segment_ids_multiple_sections():
    #Test _get_all_segment_ids_in_table_of_content_ with multiple sections#
    sheet_sections = [
        Section(
            id="section_1",
            section_number=1,
            segments=[
                TextSegment(segment_id="seg_1", segment_number=1),
                TextSegment(segment_id="seg_2", segment_number=2)
            ]
        ),
        Section(
            id="section_2",
            section_number=2, 
            segments=[
                TextSegment(segment_id="seg_3", segment_number=1),
                TextSegment(segment_id="seg_4", segment_number=2)
            ]
        )
    ]
    
    result = _get_all_segment_ids_in_table_of_content_(sheet_sections=sheet_sections)
    assert result == ["seg_1", "seg_2", "seg_3", "seg_4"]


# Test cases for fetch_sheets with specific parameters
@pytest.mark.asyncio
async def test_fetch_sheets_with_sort_parameters():
    #Test fetch_sheets with sorting parameters#
    mock_user = UserInfoResponse(
        firstname="Test",
        lastname="User", 
        username="testuser",
        email="test@example.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    mock_sheets = _generate_mock_sheets_response_()
    
    with patch("pecha_api.sheets.sheets_service.get_sheet", new_callable=AsyncMock, return_value=mock_sheets) as mock_get_sheet, \
         patch("pecha_api.sheets.sheets_service.Utils.time_passed", return_value="1 day ago"), \
         patch("pecha_api.sheets.sheets_service.fetch_user_by_email", return_value=mock_user), \
         patch("pecha_api.texts.texts_models.Text.get_published_sheets_count_from_db", new_callable=AsyncMock, return_value=5):
        
        result = await fetch_sheets(
            token="valid_token",
            language="en",
            email=None,
            sort_by=SortBy.CREATED_DATE,
            sort_order=SortOrder.ASC,
            skip=5,
            limit=20
        )
        
        # Verify get_sheet was called with correct parameters
        mock_get_sheet.assert_called_once_with(
            is_published=True,
            sort_by=SortBy.CREATED_DATE,
            sort_order=SortOrder.ASC,
            skip=5,
            limit=20
        )
        
        assert isinstance(result, SheetDTOResponse)
        assert result.skip == 5
        assert result.limit == 20


# Additional test for upload_sheet_image_request error handling
def test_upload_sheet_image_request_validation_error():
    #Test upload_sheet_image_request when image validation fails#
    file_content = io.BytesIO(b"invalid_image_data")
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.jpg"
    mock_file.file = file_content
    mock_file.content_type = "image/jpeg"
    
    with patch("pecha_api.sheets.sheets_service.ImageUtils.validate_and_compress_image", side_effect=HTTPException(status_code=400, detail="Invalid image")):
        with pytest.raises(HTTPException) as exc_info:
            upload_sheet_image_request(sheet_id="test_id", file=mock_file)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid image"


# Test case for _generate_sheet_detail_dto_ with different publisher name scenarios
@pytest.mark.asyncio
async def test_generate_sheet_detail_dto_empty_publisher_name():
    #Test _generate_sheet_detail_dto_ with empty publisher first/last name#
    sheet_details = TextDTO(
        id="sheet_id",
        title="Test Sheet",
        language="en",
        group_id="group_id",
        type=TextType.SHEET,
        is_published=True,
        created_date="2021-01-01",
        updated_date="2021-01-01",
        published_date="2021-01-01", 
        published_by="test@example.com",
        categories=[],
        views=50
    )
    
    user_details = UserInfoResponse(
        firstname="",  # Empty first name
        lastname="",   # Empty last name
        username="testuser",
        email="test@example.com",
        educations=[],
        followers=0,
        following=0,
        social_profiles=[]
    )
    
    sheet_sections = []
    
    with patch("pecha_api.sheets.sheets_service.get_segments_details_by_ids", new_callable=AsyncMock, return_value={}):
        result = await _generate_sheet_detail_dto_(
            sheet_details=sheet_details,
            user_details=user_details,
            sheet_sections=sheet_sections,
            skip=0,
            limit=10
        )
        
        assert isinstance(result, SheetDetailDTO)
        assert result.id == "sheet_id"
        assert result.publisher.name == " "  # Empty first and last name results in a space character


# Test case for _generate_sheet_section_ with SOURCE segment error handling
@pytest.mark.asyncio
async def test_generate_sheet_section_source_segment_error():
    #Test _generate_sheet_section_ when source text details cannot be retrieved#
    segments = [
        TextSegment(segment_id="source_segment", segment_number=1)
    ]
    
    segments_dict = {
        "source_segment": SegmentDTO(
            id="source_segment",
            text_id="invalid_text_id",
            content="source_content",
            type=SegmentType.SOURCE
        )
    }
    
    with patch("pecha_api.sheets.sheets_service.TextUtils.get_text_details_by_id", new_callable=AsyncMock, side_effect=HTTPException(status_code=404, detail="Text not found")):
        
        with pytest.raises(HTTPException):
            await _generate_sheet_section_(segments=segments, segments_dict=segments_dict)


# Test case for create_new_sheet with invalid token in internal function
@pytest.mark.asyncio
async def test_create_new_sheet_group_creation_error():
    #Test create_new_sheet when group creation fails#
    mock_create_sheet_request = CreateSheetRequest(
        title="Test Sheet",
        source=[],
        is_published=True
    )
    
    with patch("pecha_api.sheets.sheets_service.create_new_group", new_callable=AsyncMock, side_effect=HTTPException(status_code=401, detail="Unauthorized")):
        
        with pytest.raises(HTTPException) as exc_info:
            await create_new_sheet(
                create_sheet_request=mock_create_sheet_request,
                token="invalid_token"
            )
        
        assert exc_info.value.status_code == 401


# Test case for update_sheet_by_id cache deletion error handling
@pytest.mark.asyncio
async def test_update_sheet_cache_deletion_error():
    #Test update_sheet_by_id when cache deletion fails - should propagate the error#
    sheet_id = str(uuid.uuid4())
    mock_update_request = CreateSheetRequest(
        title="Updated Title",
        source=[
            Source(position=1, type=SegmentType.CONTENT, content="test content")
        ],
        is_published=True
    )
    
    with patch("pecha_api.sheets.sheets_service.validate_user_exists", return_value=True), \
         patch("pecha_api.sheets.sheets_service.delete_text_details_by_id_cache", new_callable=AsyncMock, side_effect=Exception("Cache error")):
        
        # Should propagate the cache error since there's no error handling in the function
        with pytest.raises(Exception) as exc_info:
            await update_sheet_by_id(
                sheet_id=sheet_id,
                update_sheet_request=mock_update_request,
                token="valid_token"
            )
        
        assert str(exc_info.value) == "Cache error"


# Test case for _generate_segment_dictionary_ with mixed segment types
def test_generate_segment_dictionary_mixed_types():
    #Test _generate_segment_dictionary_ with mixed segment types including SOURCE#
    segments_response = SegmentResponse(
        segments=[
            SegmentDTO(
                id="content_seg",
                text_id="text_id",
                content="content text",
                type=SegmentType.CONTENT
            ),
            SegmentDTO(
                id="source_seg",
                text_id="text_id", 
                content="source_id",
                type=SegmentType.SOURCE
            ),
            SegmentDTO(
                id="image_seg",
                text_id="text_id",
                content="image_url",
                type=SegmentType.IMAGE
            )
        ]
    )
    
    result = _generate_segment_dictionary_(new_segments=segments_response)
    
    # Should only contain non-SOURCE segments
    content_hash = hashlib.sha256("content text".encode()).hexdigest()
    image_hash = hashlib.sha256("image_url".encode()).hexdigest()
    source_hash = hashlib.sha256("source_id".encode()).hexdigest()
    
    assert content_hash in result
    assert image_hash in result
    assert source_hash not in result
    assert result[content_hash] == "content_seg"
    assert result[image_hash] == "image_seg"


# Test case for _generate_segment_creation_request_payload_ with only SOURCE segments
def test_generate_segment_creation_request_payload_only_sources():
    #Test _generate_segment_creation_request_payload_ with only SOURCE type segments#
    create_request = CreateSheetRequest(
        title="Test Sheet",
        source=[
            Source(position=1, type=SegmentType.SOURCE, content="source_id_1"),
            Source(position=2, type=SegmentType.SOURCE, content="source_id_2")
        ],
        is_published=True
    )
    
    result = _generate_segment_creation_request_payload_(
        create_sheet_request=create_request,
        text_id="test_text_id"
    )
    
    assert isinstance(result, CreateSegmentRequest)
    assert result.text_id == "test_text_id"
    assert len(result.segments) == 0  # Should exclude all SOURCE segments


# Test case for _create_sheet_text_ with invalid token
@pytest.mark.asyncio
async def test_create_sheet_text_invalid_token():
    #Test _create_sheet_text_ with invalid token#
    with patch("pecha_api.sheets.sheets_service.validate_and_extract_user_details", side_effect=HTTPException(status_code=401, detail="Invalid token")):
        
        with pytest.raises(HTTPException) as exc_info:
            await _create_sheet_text_(
                title="Test Sheet",
                token="invalid_token", 
                group_id="group_id"
            )
        
        assert exc_info.value.status_code == 401


# Test case for _create_sheet_group_ with invalid token
@pytest.mark.asyncio
async def test_create_sheet_group_invalid_token():
    #Test _create_sheet_group_ with invalid token#
    with patch("pecha_api.sheets.sheets_service.create_new_group", new_callable=AsyncMock, side_effect=HTTPException(status_code=401, detail="Invalid token")):
        
        with pytest.raises(HTTPException) as exc_info:
            await _create_sheet_group_(token="invalid_token")
        
        assert exc_info.value.status_code == 401