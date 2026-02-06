import io
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import UploadFile, HTTPException
from starlette import status

from pecha_api.plans.media.media_response_models import PlanUploadResponse, ImageUrlModel, TextImageUploadResponse
from pecha_api.plans.response_message import (
    IMAGE_UPLOAD_SUCCESS,
    INVALID_FILE_FORMAT,
    FILE_TOO_LARGE,
    UNEXPECTED_ERROR_UPLOAD,
    AUTHOR_NOT_FOUND
)


# Test Data Constants
VALID_TOKEN = "valid_token"
INVALID_TOKEN = "invalid_token"
TEST_PLAN_ID = "plan123"
TEST_TEXT_ID = "text123"
TEST_UUID = "uuid123"
TEST_BUCKET_NAME = "test-bucket"
TEST_S3_KEY = "images/plan_images/uuid123/test_image.jpg"
TEST_PRESIGNED_URL = f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{TEST_S3_KEY}"

# Mock Path Constants
IMAGE_UTILS_PATH = "pecha_api.plans.media.media_services.ImageUtils"
IMAGE_OPEN_PATH = "pecha_api.plans.media.media_services.Image.open"
UPLOAD_BYTES_PATH = "pecha_api.plans.media.media_services.upload_bytes"
GENERATE_URL_PATH = "pecha_api.plans.media.media_services.generate_presigned_access_url"
VALIDATE_AUTHOR_PATH = "pecha_api.plans.media.media_services.validate_and_extract_author_details"
UUID_PATH = "pecha_api.plans.media.media_services.uuid.uuid4"
GET_CONFIG_PATH = "pecha_api.plans.media.media_services.get"
GET_INT_CONFIG_PATH = "pecha_api.plans.media.media_services.get_int"
TEXT_GET_PATH = "pecha_api.plans.media.media_services.Text.get_text"
CREATE_TEXT_IMAGE_PATH = "pecha_api.plans.media.media_services.create_text_image"
SESSION_LOCAL_PATH = "pecha_api.plans.media.media_services.SessionLocal"


class TestDataFactory:
    """Factory class for creating consistent test data objects"""
    
    @staticmethod
    def create_mock_author(
        author_id: int = 1,
        first_name: str = "Test",
        last_name: str = "Author",
        email: str = "test@example.com",
        image_url: str = "https://example.com/image.jpg"
    ):
        """Create a mock Author object with default or custom values"""
        class Author:
            def __init__(self, id, first_name, last_name, email, image_url):
                self.id = id
                self.first_name = first_name
                self.last_name = last_name
                self.email = email
                self.image_url = image_url
        
        return Author(author_id, first_name, last_name, email, image_url)
    
    @staticmethod
    def create_mock_upload_file(
        filename: str = "test_image.jpg",
        content_type: str = "image/jpeg",
        size: int = 1024 * 1024,  # 1MB
        content: bytes = b"fake image content"
    ) -> MagicMock:
        """Create a mock UploadFile with specified properties"""
        file = MagicMock(spec=UploadFile)
        file.filename = filename
        file.content_type = content_type
        file.size = size
        file.file = io.BytesIO(content)
        return file
    
    @staticmethod
    def get_test_config() -> dict:
        """Get test configuration values"""
        return {
            "ALLOWED_EXTENSIONS": [".jpg", ".jpeg", ".png", ".webp"],
            "AWS_BUCKET_NAME": TEST_BUCKET_NAME,
            "MAX_FILE_SIZE": 5 * 1024 * 1024  # 5MB
        }
    
    @staticmethod
    def create_upload_response(
        filename: str = "test_image.jpg",
        plan_id: str = None,
        uuid: str = TEST_UUID
    ) -> PlanUploadResponse:
        """Create a mock upload response with 3 image versions"""
        path_segment = f"images/plan_images/{plan_id}/{uuid}" if plan_id else f"images/plan_images/{uuid}"
        base_name = filename.rsplit('.', 1)[0]
        
        image_urls = ImageUrlModel(
            thumbnail=f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{path_segment}/thumbnail/{base_name}.jpg",
            medium=f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{path_segment}/medium/{base_name}.jpg",
            original=f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{path_segment}/original/{base_name}.jpg"
        )
        
        return PlanUploadResponse(
            image=image_urls,
            key=f"{path_segment}/original/{base_name}.jpg",
            path=path_segment,
            message=IMAGE_UPLOAD_SUCCESS
        )

    @staticmethod
    def create_text_upload_response(
        filename: str = "test_image.jpg",
        text_id: str = TEST_TEXT_ID,
        uuid: str = TEST_UUID
    ) -> TextImageUploadResponse:
        path_segment = f"images/text_images/{text_id}/{uuid}"
        base_name = filename.rsplit('.', 1)[0]

        image_urls = ImageUrlModel(
            thumbnail=f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{path_segment}/thumbnail/{base_name}.jpg",
            medium=f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{path_segment}/medium/{base_name}.jpg",
            original=f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{path_segment}/original/{base_name}.jpg"
        )

        return TextImageUploadResponse(
            id="text_image_id",
            text_id=text_id,
            image=image_urls,
            key=f"{path_segment}/original/{base_name}.jpg",
            path=path_segment,
            message=IMAGE_UPLOAD_SUCCESS
        )


class MockManager:
    """Centralized mock management for consistent test setup"""
    
    def __init__(self):
        self.patches = {}
        self.mocks = {}
        self.config = TestDataFactory.get_test_config()
    
    def setup_patches(self):
        """Create all necessary patches"""
        self.patches = {
            'get_config': patch(GET_CONFIG_PATH),
            'get_int_config': patch(GET_INT_CONFIG_PATH),
            'image_open': patch(IMAGE_OPEN_PATH),
            'upload_bytes': patch(UPLOAD_BYTES_PATH),
            'presigned_url': patch(GENERATE_URL_PATH),
            'validate_author': patch(VALIDATE_AUTHOR_PATH),
            'uuid': patch(UUID_PATH)
        }
        return self
    
    def start_mocks(self):
        """Start all patches and configure mocks"""
        for name, patch_obj in self.patches.items():
            self.mocks[name] = patch_obj.start()
        
        # Configure mock behaviors
        self.mocks['get_config'].side_effect = lambda key: self.config.get(key)
        self.mocks['get_int_config'].side_effect = lambda key: self.config.get(key)
        
        # Mock PIL Image
        mock_image = MagicMock()
        mock_image.width = 1920
        mock_image.height = 1080
        mock_image.mode = 'RGB'
        mock_image.copy.return_value = mock_image
        self.mocks['image_open'].return_value = mock_image
        
        # Mock S3 operations - return different keys for different versions
        self.mocks['upload_bytes'].side_effect = lambda **kwargs: kwargs['s3_key']
        self.mocks['presigned_url'].side_effect = lambda **kwargs: f"https://s3.amazonaws.com/{TEST_BUCKET_NAME}/{kwargs['s3_key']}"
        self.mocks['validate_author'].return_value = TestDataFactory.create_mock_author()
        self.mocks['uuid'].return_value = TEST_UUID
        
        return self
    
    def cleanup(self):
        """Stop all patches"""
        for patch_obj in self.patches.values():
            patch_obj.stop()
    
    def __enter__(self):
        return self.setup_patches().start_mocks()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# Fixtures
@pytest.fixture
def mock_upload_file():
    """Provides a standard mock upload file"""
    return TestDataFactory.create_mock_upload_file()


@pytest.fixture
def mock_author():
    """Provides a mock author object"""
    return TestDataFactory.create_mock_author()


@pytest.fixture
def test_config():
    """Provides test configuration"""
    return TestDataFactory.get_test_config()


@pytest.fixture
def config_patches(test_config):
    """Provides configuration patches for tests that need them"""
    with patch(GET_CONFIG_PATH, side_effect=lambda key: test_config.get(key)), \
         patch(GET_INT_CONFIG_PATH, side_effect=lambda key: test_config.get(key)):
        yield


# Test Classes
class TestFileValidation:
    """Test cases for file validation functionality"""
    
    def test_valid_file_passes_validation(self, mock_upload_file, config_patches):
        """Test that a valid file passes validation without raising exceptions"""
        from pecha_api.plans.media.media_services import validate_file
        validate_file(mock_upload_file)  # Should not raise exception
    
    def test_invalid_file_extension_rejected(self, mock_upload_file, config_patches):
        """Test that files with invalid extensions are rejected"""
        mock_upload_file.filename = "test_document.pdf"
        
        from pecha_api.plans.media.media_services import validate_file
        with pytest.raises(HTTPException) as exc_info:
            validate_file(mock_upload_file)
            
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == INVALID_FILE_FORMAT
    
    def test_file_too_large_rejected(self, mock_upload_file, config_patches):
        """Test that files exceeding size limit are rejected"""
        mock_upload_file.size = 6 * 1024 * 1024  # 6MB
        
        from pecha_api.plans.media.media_services import validate_file
        with pytest.raises(HTTPException) as exc_info:
            validate_file(mock_upload_file)
            
        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert exc_info.value.detail == FILE_TOO_LARGE
    
    def test_file_without_filename_rejected(self, mock_upload_file, config_patches):
        """Test that files without filename are rejected"""
        mock_upload_file.filename = None
        
        from pecha_api.plans.media.media_services import validate_file
        with pytest.raises(HTTPException) as exc_info:
            validate_file(mock_upload_file)
            
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == INVALID_FILE_FORMAT
    
    @pytest.mark.parametrize("extension", [".jpg", ".jpeg", ".png", ".webp"])
    def test_supported_image_formats_accepted(self, mock_upload_file, config_patches, extension):
        """Test that all supported image formats are accepted"""
        mock_upload_file.filename = f"test_image{extension}"
        
        from pecha_api.plans.media.media_services import validate_file
        validate_file(mock_upload_file)  # Should not raise exception
    
    def test_case_insensitive_extension_validation(self, mock_upload_file, config_patches):
        """Test that file extension validation is case insensitive"""
        mock_upload_file.filename = "test_image.JPG"
        
        from pecha_api.plans.media.media_services import validate_file
        validate_file(mock_upload_file)  # Should not raise exception
    
    def test_file_at_size_limit_accepted(self, mock_upload_file, config_patches):
        """Test that files exactly at the size limit are accepted"""
        mock_upload_file.size = 5 * 1024 * 1024  # Exactly 5MB
        
        from pecha_api.plans.media.media_services import validate_file
        validate_file(mock_upload_file)  # Should not raise exception


class TestImageUploadSuccess:
    """Test cases for successful image upload scenarios"""
    
    def _assert_successful_response(self, result: PlanUploadResponse, expected_path_fragment: str):
        """Helper method to assert successful upload response"""
        assert isinstance(result, PlanUploadResponse)
        assert isinstance(result.image, ImageUrlModel)
        assert result.image.thumbnail is not None
        assert result.image.medium is not None
        assert result.image.original is not None
        assert expected_path_fragment in result.path
        assert result.message == IMAGE_UPLOAD_SUCCESS
    
    def _assert_upload_dependencies_called(self, mocks: dict, token: str = VALID_TOKEN):
        """Helper method to assert that all upload dependencies were called"""
        mocks['validate_author'].assert_called_once_with(token=token)
        mocks['image_open'].assert_called_once()
        # Should be called 3 times (thumbnail, medium, original)
        assert mocks['upload_bytes'].call_count == 3
        assert mocks['presigned_url'].call_count == 3
    
    def test_successful_upload_without_plan_id(self, mock_upload_file):
        """Test successful upload without plan_id"""
        with MockManager() as mock_manager:
            from pecha_api.plans.media.media_services import upload_plan_image
            
            result = upload_plan_image(
                token=VALID_TOKEN,
                plan_id=None,
                file=mock_upload_file
            )
            
            self._assert_upload_dependencies_called(mock_manager.mocks)
            
            # Check that all 3 versions were uploaded
            upload_calls = mock_manager.mocks['upload_bytes'].call_args_list
            assert len(upload_calls) == 3
            
            # Verify thumbnail, medium, and original uploads
            s3_keys = [call[1]['s3_key'] for call in upload_calls]
            assert any('thumbnail' in key for key in s3_keys)
            assert any('medium' in key for key in s3_keys)
            assert any('original' in key for key in s3_keys)
            
            self._assert_successful_response(result, f"images/plan_images/{TEST_UUID}")
    
    def test_successful_upload_with_plan_id(self, mock_upload_file):
        """Test successful upload with plan_id"""
        with MockManager() as mock_manager:
            from pecha_api.plans.media.media_services import upload_plan_image
            
            result = upload_plan_image(
                token=VALID_TOKEN,
                plan_id=TEST_PLAN_ID,
                file=mock_upload_file
            )
            
            # Check all upload calls contain plan_id
            upload_calls = mock_manager.mocks['upload_bytes'].call_args_list
            for call in upload_calls:
                s3_key = call[1]['s3_key']
                assert f"images/plan_images/{TEST_PLAN_ID}/{TEST_UUID}" in s3_key
            assert TEST_PLAN_ID in result.path
    
    def test_upload_with_different_content_types(self, mock_upload_file):
        """Test upload with different image content types"""
        content_types = ["image/jpeg", "image/png", "image/webp"]
        
        for content_type in content_types:
            with MockManager() as mock_manager:
                mock_upload_file.content_type = content_type
                
                from pecha_api.plans.media.media_services import upload_plan_image
                result = upload_plan_image(
                    token=VALID_TOKEN,
                    plan_id=None,
                    file=mock_upload_file
                )
                
                assert isinstance(result, PlanUploadResponse)
                assert result.message == IMAGE_UPLOAD_SUCCESS
    
    @pytest.mark.parametrize("filename,description", [
        ("test image with spaces & symbols!@#.jpg", "special characters"),
        ("test_file_with_very_long_name_that_exceeds_normal_limits_but_should_still_work.jpg", "long filename"),
        ("简体中文.jpg", "unicode characters"),
        ("file-with-dashes.png", "dashes in filename")
    ])
    def test_upload_with_edge_case_filenames(self, mock_upload_file, filename, description):
        """Test upload with various edge case filenames"""
        with MockManager() as mock_manager:
            mock_upload_file.filename = filename
            
            from pecha_api.plans.media.media_services import upload_plan_image
            result = upload_plan_image(
                token=VALID_TOKEN,
                plan_id=None,
                file=mock_upload_file
            )
            
            assert isinstance(result, PlanUploadResponse)
            assert result.message == IMAGE_UPLOAD_SUCCESS
    
    def test_upload_with_empty_file_content(self, mock_upload_file):
        """Test upload with empty file content"""
        with MockManager() as mock_manager:
            mock_upload_file.file = io.BytesIO(b"")
            
            from pecha_api.plans.media.media_services import upload_plan_image
            result = upload_plan_image(
                token=VALID_TOKEN,
                plan_id=None,
                file=mock_upload_file
            )
            
            assert isinstance(result, PlanUploadResponse)
            assert result.message == IMAGE_UPLOAD_SUCCESS


class TestImageUploadAuthentication:
    """Test cases for authentication-related upload scenarios"""
    
    def test_upload_with_invalid_token_fails(self, mock_upload_file):
        """Test that upload fails with invalid authentication token"""
        with patch(VALIDATE_AUTHOR_PATH) as mock_validate_author:
            mock_validate_author.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=AUTHOR_NOT_FOUND
            )
            
            from pecha_api.plans.media.media_services import upload_plan_image
            with pytest.raises(HTTPException) as exc_info:
                upload_plan_image(
                    token=INVALID_TOKEN,
                    plan_id=None,
                    file=mock_upload_file
                )
                
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert exc_info.value.detail == AUTHOR_NOT_FOUND
    
    def test_upload_with_expired_token_fails(self, mock_upload_file):
        """Test that upload fails with expired token"""
        with patch(VALIDATE_AUTHOR_PATH) as mock_validate_author:
            mock_validate_author.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
            
            from pecha_api.plans.media.media_services import upload_plan_image
            with pytest.raises(HTTPException) as exc_info:
                upload_plan_image(
                    token="expired_token",
                    plan_id=None,
                    file=mock_upload_file
                )
                
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.detail == "Token has expired"


class TestImageUploadValidation:
    """Test cases for file validation during upload"""
    
    def test_upload_with_invalid_file_format_fails(self, mock_upload_file, test_config):
        """Test that upload fails with invalid file format"""
        mock_upload_file.filename = "test_document.pdf"
        
        with patch(GET_CONFIG_PATH, side_effect=lambda key: test_config.get(key)), \
             patch(GET_INT_CONFIG_PATH, side_effect=lambda key: test_config.get(key)), \
             patch(VALIDATE_AUTHOR_PATH):
            from pecha_api.plans.media.media_services import upload_plan_image
            with pytest.raises(HTTPException) as exc_info:
                upload_plan_image(
                    token=VALID_TOKEN,
                    plan_id=None,
                    file=mock_upload_file
                )
                
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == INVALID_FILE_FORMAT
    
    def test_upload_with_oversized_file_fails(self, mock_upload_file, test_config):
        """Test that upload fails with oversized file"""
        mock_upload_file.size = 6 * 1024 * 1024  # 6MB
        
        with patch(GET_CONFIG_PATH, side_effect=lambda key: test_config.get(key)), \
             patch(GET_INT_CONFIG_PATH, side_effect=lambda key: test_config.get(key)), \
             patch(VALIDATE_AUTHOR_PATH):
            from pecha_api.plans.media.media_services import upload_plan_image
            with pytest.raises(HTTPException) as exc_info:
                upload_plan_image(
                    token=VALID_TOKEN,
                    plan_id=None,
                    file=mock_upload_file
                )
                
            assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            assert exc_info.value.detail == FILE_TOO_LARGE


class TestImageUploadErrorHandling:
    """Test cases for error handling during upload process"""
    
    def test_image_open_failure(self, mock_upload_file, test_config):
        """Test handling of image open failures"""
        with patch(GET_CONFIG_PATH, side_effect=lambda key: test_config.get(key)), \
             patch(GET_INT_CONFIG_PATH, side_effect=lambda key: test_config.get(key)), \
             patch(VALIDATE_AUTHOR_PATH), \
             patch(IMAGE_OPEN_PATH) as mock_image_open:
            mock_image_open.side_effect = Exception("Cannot identify image file")
            
            from pecha_api.plans.media.media_services import upload_plan_image
            with pytest.raises(HTTPException) as exc_info:
                upload_plan_image(
                    token=VALID_TOKEN,
                    plan_id=None,
                    file=mock_upload_file
                )
                
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == "Invalid image file"
    
    def test_s3_upload_failure(self, mock_upload_file):
        """Test handling of S3 upload failures"""
        with MockManager() as mock_manager:
            mock_manager.mocks['upload_bytes'].side_effect = Exception("S3 upload failed")
            
            from pecha_api.plans.media.media_services import upload_plan_image
            with pytest.raises(Exception) as exc_info:
                upload_plan_image(
                    token=VALID_TOKEN,
                    plan_id=None,
                    file=mock_upload_file
                )
                
            assert "S3 upload failed" in str(exc_info.value)
    
    def test_presigned_url_generation_failure(self, mock_upload_file):
        """Test handling of presigned URL generation failures"""
        with MockManager() as mock_manager:
            mock_manager.mocks['presigned_url'].side_effect = Exception("Failed to generate presigned URL")
            
            from pecha_api.plans.media.media_services import upload_plan_image
            with pytest.raises(Exception) as exc_info:
                upload_plan_image(
                    token=VALID_TOKEN,
                    plan_id=None,
                    file=mock_upload_file
                )
                
            assert "Failed to generate presigned URL" in str(exc_info.value)


class TestImageUploadIntegration:
    """Integration test cases for complete upload workflow"""
    
    def test_complete_upload_workflow(self, mock_upload_file):
        """Test the complete upload workflow from start to finish"""
        with MockManager() as mock_manager:
            from pecha_api.plans.media.media_services import upload_plan_image
            
            result = upload_plan_image(
                token=VALID_TOKEN,
                plan_id=TEST_PLAN_ID,
                file=mock_upload_file
            )
            
            # Verify all components were called in correct order
            mock_manager.mocks['validate_author'].assert_called_once_with(token=VALID_TOKEN)
            mock_manager.mocks['image_open'].assert_called_once()
            assert mock_manager.mocks['upload_bytes'].call_count == 3
            assert mock_manager.mocks['presigned_url'].call_count == 3
            
            # Verify response structure
            assert isinstance(result, PlanUploadResponse)


class TestTextImageUploadSuccess:
    """Test cases for successful text image upload scenarios"""

    @pytest.mark.asyncio
    async def test_successful_text_upload(self, mock_upload_file):
        with MockManager() as mock_manager:
            with patch(TEXT_GET_PATH, new_callable=AsyncMock) as mock_get_text, \
                 patch(CREATE_TEXT_IMAGE_PATH) as mock_create_text_image, \
                 patch(SESSION_LOCAL_PATH) as mock_session_local:
                mock_get_text.return_value = {"id": TEST_TEXT_ID}
                mock_create_text_image.return_value = MagicMock(id="text_image_id")
                mock_session_local.return_value.__enter__.return_value = MagicMock()

                from pecha_api.plans.media.media_services import upload_text_image

                result = await upload_text_image(
                    token=VALID_TOKEN,
                    text_id=TEST_TEXT_ID,
                    file=mock_upload_file
                )

                mock_manager.mocks['validate_author'].assert_called_once_with(token=VALID_TOKEN)
                mock_get_text.assert_awaited_once_with(text_id=TEST_TEXT_ID)
                mock_create_text_image.assert_called_once()

                assert isinstance(result, TextImageUploadResponse)
                assert result.text_id == TEST_TEXT_ID
                assert result.message == IMAGE_UPLOAD_SUCCESS
                assert result.image.original is not None


class TestTextImageUploadValidation:
    """Test cases for text image upload validation"""

    @pytest.mark.asyncio
    async def test_text_not_found_raises(self, mock_upload_file):
        with patch(TEXT_GET_PATH, new_callable=AsyncMock) as mock_get_text, \
             patch(VALIDATE_AUTHOR_PATH):
            mock_get_text.return_value = None

            from pecha_api.plans.media.media_services import upload_text_image
            with pytest.raises(HTTPException) as exc_info:
                await upload_text_image(
                    token=VALID_TOKEN,
                    text_id=TEST_TEXT_ID,
                    file=mock_upload_file
                )

            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    def test_upload_with_all_parameters(self, mock_upload_file):
        """Test upload with all possible parameters specified"""
        with MockManager() as mock_manager:
            mock_upload_file.filename = "custom_image.png"
            mock_upload_file.content_type = "image/png"
            
            from pecha_api.plans.media.media_services import upload_plan_image
            
            result = upload_plan_image(
                token=VALID_TOKEN,
                plan_id=TEST_PLAN_ID,
                file=mock_upload_file
            )
            
            # Verify upload_bytes was called 3 times with correct parameters
            upload_calls = mock_manager.mocks['upload_bytes'].call_args_list
            assert len(upload_calls) == 3
            
            for call in upload_calls:
                upload_args = call[1]
                assert upload_args['bucket_name'] == TEST_BUCKET_NAME
                assert upload_args['content_type'] == "image/jpeg"  # All converted to JPEG
                assert TEST_PLAN_ID in upload_args['s3_key']
                assert "custom_image" in upload_args['s3_key']
            
            assert isinstance(result, PlanUploadResponse)