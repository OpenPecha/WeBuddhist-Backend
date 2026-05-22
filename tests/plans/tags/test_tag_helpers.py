import uuid
from unittest.mock import MagicMock, patch

from pecha_api.plans.tags.tag_helpers import generate_tag_image_url, tags_to_summary_dtos


def _tag_entity(name: str, image_key=None, deleted_at=None):
    tag = MagicMock()
    tag.id = uuid.uuid4()
    tag.name = name
    tag.image_key = image_key
    tag.description = "desc"
    tag.deleted_at = deleted_at
    return tag


def test_generate_tag_image_url_returns_none_when_empty():
    assert generate_tag_image_url(None) is None
    assert generate_tag_image_url("") is None


def test_generate_tag_image_url_returns_presigned_url():
    with patch("pecha_api.plans.tags.tag_helpers.get", return_value="bucket"), patch(
        "pecha_api.plans.tags.tag_helpers.generate_presigned_access_url",
        return_value="https://signed/tag.jpg",
    ) as mock_presign:
        result = generate_tag_image_url("images/tags/key.jpg")

    assert result == "https://signed/tag.jpg"
    mock_presign.assert_called_once_with(bucket_name="bucket", s3_key="images/tags/key.jpg")


def test_tags_to_summary_dtos_empty():
    assert tags_to_summary_dtos(None) == []
    assert tags_to_summary_dtos([]) == []


def test_tags_to_summary_dtos_sorts_and_maps_active_tags():
    with patch("pecha_api.plans.tags.tag_helpers.generate_tag_image_url", return_value=None):
        result = tags_to_summary_dtos(
            [
                _tag_entity("Zebra"),
                _tag_entity("alpha"),
                _tag_entity("deleted", deleted_at="2020-01-01"),
            ]
        )

    assert len(result) == 2
    assert result[0].name == "alpha"
    assert result[1].name == "Zebra"


def test_tags_to_summary_dtos_includes_image_when_key_present():
    with patch("pecha_api.plans.tags.tag_helpers.generate_tag_image_url", return_value="https://signed"):
        result = tags_to_summary_dtos([_tag_entity("Meditation", image_key="images/tags/x")])

    assert result[0].image == "https://signed"
    assert result[0].image_key == "images/tags/x"
