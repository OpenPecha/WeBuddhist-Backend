import io
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import UploadFile

from pecha_api.plans.platform_enums import PlatformRole
from pecha_api.plans.shareable_images.day_shareable_image_enums import DayShareableImageType
from pecha_api.plans.shareable_images.day_shareable_image_service import (
    delete_plan_day_shareable_image,
    upload_plan_day_shareable_image,
)


@patch(
    "pecha_api.plans.shareable_images.day_shareable_image_service.generate_presigned_access_url",
    return_value="https://image.url",
)
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.upsert_day_shareable_image")
@patch(
    "pecha_api.plans.shareable_images.day_shareable_image_service.get_day_shareable_image_by_plan_item_id",
    return_value=None,
)
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.upload_bytes")
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.ImageUtils")
@patch("pecha_api.plans.shareable_images.day_shareable_image_service._get_author_plan_item_by_day_id")
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.validate_cms_author_details")
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.SessionLocal")
def test_upload_plan_day_shareable_image_success(
    mock_session,
    mock_validate,
    mock_get_item,
    mock_image_utils_cls,
    mock_upload_bytes,
    mock_get_existing,
    mock_upsert,
    mock_presign,
):
    day_id = uuid4()
    plan_id = uuid4()

    author = MagicMock()
    author.email = "author@test.com"
    author.platform_role = PlatformRole.SUPER_ADMIN
    mock_validate.return_value = author

    plan_item = MagicMock()
    plan_item.id = day_id
    plan_item.plan_id = plan_id
    mock_get_item.return_value = plan_item

    mock_image_utils = MagicMock()
    mock_image_utils.validate_and_compress_image.return_value = io.BytesIO(b"webp")
    mock_image_utils_cls.return_value = mock_image_utils

    image_row = MagicMock()
    image_row.thumbnail_key = "images/day_shareable/key.webp"
    mock_upsert.return_value = image_row

    mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    file = MagicMock(spec=UploadFile)
    file.filename = "day.jpg"
    file.content_type = "image/jpeg"
    file.file = io.BytesIO(b"image")

    response = upload_plan_day_shareable_image(
        token="token",
        day_id=day_id,
        image_type=DayShareableImageType.THUMBNAIL,
        file=file,
    )

    assert response.image_type == "thumbnail"
    assert response.image_key == "images/day_shareable/key.webp"
    assert response.image_url == "https://image.url"
    mock_upload_bytes.assert_called_once()


@patch("pecha_api.plans.shareable_images.day_shareable_image_service.delete_file")
@patch(
    "pecha_api.plans.shareable_images.day_shareable_image_service.clear_day_shareable_image_key"
)
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.get_day_shareable_image_by_plan_item_id")
@patch("pecha_api.plans.shareable_images.day_shareable_image_service._get_author_plan_item_by_day_id")
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.validate_cms_author_details")
@patch("pecha_api.plans.shareable_images.day_shareable_image_service.SessionLocal")
def test_delete_plan_day_shareable_image_success(
    mock_session,
    mock_validate,
    mock_get_item,
    mock_get_existing,
    mock_clear,
    mock_delete_file,
):
    day_id = uuid4()

    author = MagicMock()
    author.email = "author@test.com"
    mock_validate.return_value = author

    plan_item = MagicMock()
    plan_item.id = day_id
    mock_get_item.return_value = plan_item

    existing = MagicMock()
    existing.thumbnail_key = "images/day_shareable/thumb.webp"
    mock_get_existing.return_value = existing

    mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_session.return_value.__exit__ = MagicMock(return_value=False)

    delete_plan_day_shareable_image(
        token="token",
        day_id=day_id,
        image_type=DayShareableImageType.THUMBNAIL,
    )

    mock_delete_file.assert_called_once_with("images/day_shareable/thumb.webp")
    mock_clear.assert_called_once()
