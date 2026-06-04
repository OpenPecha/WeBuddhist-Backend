from pecha_api.error_contants import ErrorConstants
from fastapi import HTTPException, UploadFile, status
from PIL import Image
import io
from pecha_api.config import get_int

WEBP_FORMAT = 'WEBP'
WEBP_CONTENT_TYPE = 'image/webp'
WEBP_EXTENSION = '.webp'


class ImageUtils:
    def __init__(self):
        self.bit_size = 1024 * 1024
        self.rgba_mode = 'RGBA'
        self.rgb_mode = 'RGB'
        self.la_mode = 'LA'
        self.p_mode = 'P'
        self.webp_format = WEBP_FORMAT
        self.default_background_color = (255, 255, 255)
    
    def validate_and_compress_image(self, file: UploadFile, content_type: str) -> io.BytesIO:
        max_file_size = get_int("MAX_FILE_SIZE_MB")
        max_file_size_bytes = max_file_size * self.bit_size
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorConstants.IMAGE_ERROR_MESSAGE
            )
        file.file.seek(0, 2)  # Move to the end of the file to get its size
        file_size = file.file.tell()
        if file_size > max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=ErrorConstants.IMAGE_SIZE_ERROR_MESSAGE
            )
        file.file.seek(0)  # Reset file pointer
        # Read and compress the image
        try:
            image = Image.open(file.file)
            image = self._prepare_for_webp(image)

            compressed_image_io = io.BytesIO()
            image.save(compressed_image_io, format=self.webp_format, quality=get_int("COMPRESSED_QUALITY"))
            compressed_image_io.seek(0)
            return compressed_image_io
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorConstants.IMAGE_PROCESSING_ERROR_MESSAGE
            )

    def _prepare_for_webp(self, image: Image.Image) -> Image.Image:
        if image.mode in (self.rgba_mode, self.la_mode) or (image.mode == self.p_mode and 'transparency' in image.info):
            if image.mode == self.p_mode:
                return image.convert(self.rgba_mode)
            if image.mode == self.la_mode:
                return image.convert(self.rgba_mode)
            return image
        if image.mode != self.rgb_mode:
            return image.convert(self.rgb_mode)
        return image
