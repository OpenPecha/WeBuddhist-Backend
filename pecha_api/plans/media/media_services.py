import os, uuid
from fastapi import UploadFile, HTTPException, status
from typing import Optional
from PIL import Image
import io


from ...config import get, get_int
from ...image_utils import ImageUtils
from ...uploads.S3_utils import upload_bytes, generate_presigned_access_url
from ...plans.authors.plan_authors_service import validate_and_extract_author_details
from .media_response_models import PlanUploadResponse, ImageUrlModel, TextImageUploadResponse
from ...plans.response_message import (
    IMAGE_UPLOAD_SUCCESS,
    INVALID_FILE_FORMAT,
    FILE_TOO_LARGE
)
from ...texts.texts_models import Text
from .media_repository import create_text_image
from ...error_contants import ErrorConstants
from ...db.database import SessionLocal


def validate_file(file: UploadFile) -> None:
    file_extension = os.path.splitext(file.filename.lower())[1] if file.filename else ''
    if file_extension not in get("ALLOWED_EXTENSIONS"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_FILE_FORMAT)

    if hasattr(file, 'size') and file.size and file.size > get_int("MAX_FILE_SIZE"):
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=FILE_TOO_LARGE)


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """
    Convert image to RGB mode for JPEG compatibility.
    Handles transparency by adding white background.
    """
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else image.split()[1])
        return background
    elif image.mode != 'RGB':
        return image.convert('RGB')
    return image


def compress_image_to_size(image: Image.Image, max_width: int, quality: int = 85) -> io.BytesIO:
    """
    Resize and compress image to specified width while maintaining aspect ratio.
    
    Args:
        image: PIL Image object
        max_width: Maximum width in pixels
        quality: JPEG quality (1-100)
    
    Returns:
        BytesIO object containing compressed image
    """
    # Calculate new dimensions maintaining aspect ratio
    aspect_ratio = image.height / image.width
    new_width = min(image.width, max_width)
    new_height = int(new_width * aspect_ratio)
    
    # Resize image using high-quality LANCZOS resampling
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary
    resized_image = convert_to_rgb(resized_image)
    
    # Save to BytesIO with compression
    output = io.BytesIO()
    resized_image.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    return output


def compress_image_original_size(image: Image.Image, quality: int = 90) -> io.BytesIO:
    """
    Compress image at original dimensions without resizing.
    
    Args:
        image: PIL Image object
        quality: JPEG quality (1-100)
    
    Returns:
        BytesIO object containing compressed image
    """
    # Convert to RGB if necessary
    rgb_image = convert_to_rgb(image)
    
    # Save to BytesIO with compression
    output = io.BytesIO()
    rgb_image.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    return output


def read_image_from_upload(file: UploadFile) -> Image.Image:
    file.file.seek(0)
    try:
        return Image.open(file.file)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")


def build_image_versions(original_image: Image.Image) -> list[tuple[str, io.BytesIO]]:
    thumbnail_image = compress_image_to_size(original_image.copy(), 200, quality=80)
    medium_image = compress_image_to_size(original_image.copy(), 800, quality=85)
    original_compressed = compress_image_original_size(original_image.copy(), quality=90)
    return [
        ("thumbnail", thumbnail_image),
        ("medium", medium_image),
        ("original", original_compressed),
    ]


def upload_image_versions(
    *,
    image_path_full: str,
    file_name: str,
    image_versions: list[tuple[str, io.BytesIO]],
) -> tuple[ImageUrlModel, list[str]]:
    image_urls = {}
    upload_keys = []

    for version_name, compressed_image in image_versions:
        s3_key = f"{image_path_full}/{version_name}/{file_name}.jpg"
        upload_key = upload_bytes(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
            file=compressed_image,
            content_type="image/jpeg",
        )
        upload_keys.append(upload_key)

        presigned_url = generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=upload_key,
        )

        image_urls[version_name] = presigned_url

    image_url_model = ImageUrlModel(
        thumbnail=image_urls["thumbnail"],
        medium=image_urls["medium"],
        original=image_urls["original"],
    )
    return image_url_model, upload_keys


def upload_plan_image(token: str, plan_id: Optional[str], file: UploadFile) -> PlanUploadResponse:

    validate_and_extract_author_details(token=token)
    validate_file(file)
    
    original_image = read_image_from_upload(file)
    
    file_name, _ = os.path.splitext(file.filename)
    unique_id = str(uuid.uuid4())
    path = "images/plan_images"
    image_path_full = f"{path}/{plan_id}/{unique_id}" if plan_id is not None else f"{path}/{unique_id}"
    
    image_versions = build_image_versions(original_image)
    image_url_model, upload_keys = upload_image_versions(
        image_path_full=image_path_full,
        file_name=file_name,
        image_versions=image_versions,
    )
    
    return PlanUploadResponse(
        image=image_url_model,
        key=upload_keys[2],  # Use original image key as primary key
        path=image_path_full,
        message=IMAGE_UPLOAD_SUCCESS
    )


async def upload_text_image(token: str, text_id: str, file: UploadFile) -> TextImageUploadResponse:

    validate_and_extract_author_details(token=token)
    validate_file(file)

    text_details = await Text.get_text(text_id=text_id)
    if not text_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)

    original_image = read_image_from_upload(file)

    file_name, _ = os.path.splitext(file.filename)
    unique_id = str(uuid.uuid4())
    path = "images/text_images"
    image_path_full = f"{path}/{text_id}/{unique_id}"

    image_versions = build_image_versions(original_image)
    image_url_model, upload_keys = upload_image_versions(
        image_path_full=image_path_full,
        file_name=file_name,
        image_versions=image_versions,
    )

    with SessionLocal() as db_session:
        text_image = create_text_image(db=db_session, text_id=text_id, image_url=upload_keys[2])

    return TextImageUploadResponse(
        id=str(text_image.id),
        text_id=text_id,
        image=image_url_model,
        key=upload_keys[2],
        path=image_path_full,
        message=IMAGE_UPLOAD_SUCCESS
    )
