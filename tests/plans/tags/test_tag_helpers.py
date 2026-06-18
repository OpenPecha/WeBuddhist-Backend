import uuid
from unittest.mock import MagicMock, patch

from pecha_api.plans.tags.tag_helpers import generate_tag_image_url, tags_to_summary_dtos


def _tag_entity(name: str, image_key=None, deleted_at=None, display_order=None, language="EN", description="desc"):
    tag = MagicMock()
    tag.id = uuid.uuid4()
    tag.name = name
    tag.image_key = image_key
    tag.description = description
    tag.featured = False
    tag.display_order = display_order
    tag.deleted_at = deleted_at
    
    # Add metadata_entries for the new metadata-based structure
    meta = MagicMock()
    meta.id = uuid.uuid4()
    meta.name = name
    meta.description = description
    meta.language = MagicMock()
    meta.language.value = language
    tag.metadata_entries = [meta]
    
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


def test_tags_to_summary_dtos_sorts_by_display_order_then_name():
    with patch("pecha_api.plans.tags.tag_helpers.generate_tag_image_url", return_value=None):
        result = tags_to_summary_dtos(
            [
                _tag_entity("Zebra", display_order=2),
                _tag_entity("alpha", display_order=1),
                _tag_entity("middle", display_order=None),
            ]
        )

    assert [item.name for item in result] == ["alpha", "Zebra", "middle"]


def test_tags_to_summary_dtos_includes_image_when_key_present():
    with patch("pecha_api.plans.tags.tag_helpers.generate_tag_image_url", return_value="https://signed"):
        result = tags_to_summary_dtos([_tag_entity("Meditation", image_key="images/tags/x")])

    assert result[0].image == "https://signed"
    assert result[0].image_key == "images/tags/x"


def test_tags_to_summary_dtos_with_language_fallback():
    tag = _tag_entity("Meditation", language="EN")
    with patch("pecha_api.plans.tags.tag_helpers.generate_tag_image_url", return_value=None):
        result = tags_to_summary_dtos([tag], language="BO")

    assert len(result) == 1
    assert result[0].name == "Meditation"


def test_tags_to_summary_dtos_with_specific_language():
    tag = MagicMock()
    tag.id = uuid.uuid4()
    tag.image_key = None
    tag.featured = False
    tag.display_order = None
    tag.deleted_at = None
    
    meta_en = MagicMock()
    meta_en.name = "Meditation"
    meta_en.description = "English desc"
    meta_en.language = MagicMock()
    meta_en.language.value = "EN"
    
    meta_bo = MagicMock()
    meta_bo.name = "བསམ་གཏན"
    meta_bo.description = "Tibetan desc"
    meta_bo.language = MagicMock()
    meta_bo.language.value = "BO"
    
    tag.metadata_entries = [meta_en, meta_bo]
    
    with patch("pecha_api.plans.tags.tag_helpers.generate_tag_image_url", return_value=None):
        result = tags_to_summary_dtos([tag], language="BO")

    assert len(result) == 1
    assert result[0].name == "བསམ་གཏན"
    assert result[0].description == "Tibetan desc"
