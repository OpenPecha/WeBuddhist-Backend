import pytest
from unittest.mock import patch, MagicMock
from pecha_api.plans.public.plan_service import get_image_url
from pecha_api.plans.public.plan_response_models import ImageUrlModel


class TestGetImageUrl:
    """Test cases for get_image_url function"""
    
    @pytest.mark.asyncio
    async def test_get_image_url_with_valid_image_path(self):
        """Test that get_image_url generates presigned URLs for all three sizes"""
        image_url = "images/plan_images/plan-id/uuid/original/image.jpg"
        expected_presigned_url = "https://bucket.s3.amazonaws.com/presigned-url"
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.return_value = expected_presigned_url
            
            result = await get_image_url(image_url)
            
            # Verify result is ImageUrlModel
            assert isinstance(result, ImageUrlModel)
            assert result.thumbnail == expected_presigned_url
            assert result.medium == expected_presigned_url
            assert result.original == expected_presigned_url
            
            # Verify generate_presigned_access_url was called 3 times
            assert mock_presigned.call_count == 3
            
            # Verify the S3 keys passed to generate_presigned_access_url
            calls = mock_presigned.call_args_list
            assert calls[0][1]['s3_key'] == "images/plan_images/plan-id/uuid/thumbnail/image.jpg"
            assert calls[1][1]['s3_key'] == "images/plan_images/plan-id/uuid/medium/image.jpg"
            assert calls[2][1]['s3_key'] == "images/plan_images/plan-id/uuid/original/image.jpg"
    
    @pytest.mark.asyncio
    async def test_get_image_url_with_none_returns_none(self):
        """Test that get_image_url returns None when image_url is None"""
        result = await get_image_url(None)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_image_url_with_empty_string_returns_none(self):
        """Test that get_image_url returns None when image_url is empty string"""
        result = await get_image_url("")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_image_url_replaces_original_with_thumbnail(self):
        """Test that 'original' is correctly replaced with 'thumbnail' in the path"""
        image_url = "images/plan_images/plan-id/uuid/original/test.jpg"
        expected_thumbnail_key = "images/plan_images/plan-id/uuid/thumbnail/test.jpg"
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.return_value = "https://test-url.com"
            
            await get_image_url(image_url)
            
            # Check first call (thumbnail)
            first_call_key = mock_presigned.call_args_list[0][1]['s3_key']
            assert first_call_key == expected_thumbnail_key
    
    @pytest.mark.asyncio
    async def test_get_image_url_replaces_original_with_medium(self):
        """Test that 'original' is correctly replaced with 'medium' in the path"""
        image_url = "images/plan_images/plan-id/uuid/original/test.jpg"
        expected_medium_key = "images/plan_images/plan-id/uuid/medium/test.jpg"
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.return_value = "https://test-url.com"
            
            await get_image_url(image_url)
            
            # Check second call (medium)
            second_call_key = mock_presigned.call_args_list[1][1]['s3_key']
            assert second_call_key == expected_medium_key
    
    @pytest.mark.asyncio
    async def test_get_image_url_keeps_original_path(self):
        """Test that original path is preserved for the original image"""
        image_url = "images/plan_images/plan-id/uuid/original/test.jpg"
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.return_value = "https://test-url.com"
            
            await get_image_url(image_url)
            
            # Check third call (original)
            third_call_key = mock_presigned.call_args_list[2][1]['s3_key']
            assert third_call_key == image_url
    
    @pytest.mark.asyncio
    async def test_get_image_url_uses_correct_bucket_name(self):
        """Test that get_image_url uses the correct bucket name from config"""
        image_url = "images/plan_images/plan-id/uuid/original/test.jpg"
        expected_bucket = "my-test-bucket"
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = expected_bucket
            mock_presigned.return_value = "https://test-url.com"
            
            await get_image_url(image_url)
            
            # Verify bucket_name was retrieved from config
            mock_get.assert_called_with("AWS_BUCKET_NAME")
            
            # Verify all calls used the correct bucket name
            for call in mock_presigned.call_args_list:
                assert call[1]['bucket_name'] == expected_bucket
    
    @pytest.mark.asyncio
    async def test_get_image_url_with_different_filenames(self):
        """Test get_image_url with various filename formats"""
        test_cases = [
            "images/plan_images/plan-id/uuid/original/photo.jpg",
            "images/plan_images/plan-id/uuid/original/image_with_underscores.png",
            "images/plan_images/plan-id/uuid/original/file-with-dashes.jpeg",
            "images/plan_images/plan-id/uuid/original/123456.jpg",
        ]
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.return_value = "https://test-url.com"
            
            for image_url in test_cases:
                mock_presigned.reset_mock()
                
                result = await get_image_url(image_url)
                
                assert isinstance(result, ImageUrlModel)
                assert mock_presigned.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_image_url_returns_different_urls_for_each_size(self):
        """Test that different presigned URLs can be returned for each size"""
        image_url = "images/plan_images/plan-id/uuid/original/test.jpg"
        
        # Mock to return different URLs for each call
        url_responses = [
            "https://bucket.s3.amazonaws.com/thumbnail-url",
            "https://bucket.s3.amazonaws.com/medium-url",
            "https://bucket.s3.amazonaws.com/original-url"
        ]
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.side_effect = url_responses
            
            result = await get_image_url(image_url)
            
            assert result.thumbnail == url_responses[0]
            assert result.medium == url_responses[1]
            assert result.original == url_responses[2]
    
    @pytest.mark.asyncio
    async def test_get_image_url_with_complex_path(self):
        """Test get_image_url with complex nested path structure"""
        image_url = "images/plan_images/plan-123/uuid-456/original/subfolder/image.jpg"
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.return_value = "https://test-url.com"
            
            result = await get_image_url(image_url)
            
            # Verify the paths were correctly transformed
            calls = mock_presigned.call_args_list
            assert "thumbnail" in calls[0][1]['s3_key']
            assert "medium" in calls[1][1]['s3_key']
            assert "original" in calls[2][1]['s3_key']
            assert isinstance(result, ImageUrlModel)
    
    @pytest.mark.asyncio
    async def test_get_image_url_preserves_file_extension(self):
        """Test that file extensions are preserved in all generated URLs"""
        test_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
        
        with patch("pecha_api.plans.public.plan_service.generate_presigned_access_url") as mock_presigned, \
             patch("pecha_api.plans.public.plan_service.get") as mock_get:
            
            mock_get.return_value = "test-bucket"
            mock_presigned.return_value = "https://test-url.com"
            
            for ext in test_extensions:
                mock_presigned.reset_mock()
                image_url = f"images/plan_images/plan-id/uuid/original/image{ext}"
                
                await get_image_url(image_url)
                
                # Verify all calls preserve the extension
                for call in mock_presigned.call_args_list:
                    s3_key = call[1]['s3_key']
                    assert s3_key.endswith(ext), f"Extension {ext} not preserved in {s3_key}"
