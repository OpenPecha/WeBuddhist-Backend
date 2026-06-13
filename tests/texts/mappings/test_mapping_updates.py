import uuid
import pytest
from typing import Dict, List
from unittest.mock import AsyncMock, Mock, patch

from pecha_api.texts.mappings.mappings_service import (
    _merge_segment_mappings,
    _get_existing_mappings,
    _process_new_mappings,
    _construct_update_segments
)
from pecha_api.texts.segments.segments_models import Mapping, Segment

@pytest.fixture
def mock_segment():
    """Create a mock segment that doesn't require database initialization"""
    def _create_segment(id_str: str, text_id: str, content: str, mapping: List[Mapping] = None):
        segment = Mock(spec=Segment)
        segment.id = uuid.UUID(id_str) if isinstance(id_str, str) else id_str
        segment.text_id = text_id
        segment.content = content
        segment.mapping = mapping or []
        return segment
    return _create_segment


def test_merge_segment_mappings():
    """Test merging of two segment mappings"""
    # Arrange
    existing_mapping = Mapping(text_id="text1", segments=["seg1", "seg2"])
    new_mapping = Mapping(text_id="text1", segments=["seg2", "seg3"])

    # Act
    result = _merge_segment_mappings(existing_mapping, new_mapping)

    # Assert
    assert result.text_id == "text1"
    assert set(result.segments) == {"seg1", "seg2", "seg3"}
    assert result is existing_mapping  # Should modify existing mapping


def test_get_existing_mappings(mock_segment):
    """Test getting dictionary of existing mappings"""
    # Arrange
    mappings = [
        Mapping(text_id="text1", segments=["seg1"]),
        Mapping(text_id="text2", segments=["seg2"])
    ]
    segment = mock_segment(
        id_str="12345678-1234-5678-1234-567812345678",
        text_id="source",
        content="content",
        mapping=mappings
    )

    # Act
    result = _get_existing_mappings(segment)

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 2
    assert "text1" in result
    assert "text2" in result
    assert result["text1"].segments == ["seg1"]
    assert result["text2"].segments == ["seg2"]


def test_get_existing_mappings_empty(mock_segment):
    """Test getting mappings from segment with no mappings"""
    # Arrange
    segment = mock_segment(
        id_str="12345678-1234-5678-1234-567812345678",
        text_id="source",
        content="content",
        mapping=[]
    )

    # Act
    result = _get_existing_mappings(segment)

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 0


def test_process_new_mappings_all_new():
    """Test processing entirely new mappings"""
    # Arrange
    new_mappings = [
        Mapping(text_id="text1", segments=["seg1"]),
        Mapping(text_id="text2", segments=["seg2"])
    ]
    existing_mappings: Dict[str, Mapping] = {}

    # Act
    result = _process_new_mappings(new_mappings, existing_mappings)

    # Assert
    assert len(result) == 2
    assert result == new_mappings


def test_process_new_mappings_merge():
    """Test processing mappings that need merging"""
    # Arrange
    existing_mappings = {
        "text1": Mapping(text_id="text1", segments=["seg1", "seg2"]),
        "text2": Mapping(text_id="text2", segments=["seg3"])
    }
    new_mappings = [
        Mapping(text_id="text1", segments=["seg2", "seg4"]),
        Mapping(text_id="text3", segments=["seg5"])
    ]

    # Act
    result = _process_new_mappings(new_mappings, existing_mappings)

    # Assert
    assert len(result) == 3
    text1_mapping = next(m for m in result if m.text_id == "text1")
    assert set(text1_mapping.segments) == {"seg1", "seg2", "seg4"}
    assert any(m.text_id == "text2" and m.segments == ["seg3"] for m in result)
    assert any(m.text_id == "text3" and m.segments == ["seg5"] for m in result)


def test_construct_update_segments(mock_segment):
    """Test construction of updated segments"""
    # Arrange
    segments = [
        mock_segment(
            id_str="12345678-1234-5678-1234-567812345678",
            text_id="source1",
            content="content1",
            mapping=[Mapping(text_id="text1", segments=["a", "b"])]
        ),
        mock_segment(
            id_str="87654321-4321-8765-4321-876543210987",
            text_id="source2",
            content="content2",
            mapping=[Mapping(text_id="text2", segments=["c"])]
        )
    ]
    update_dict = {
        "12345678-1234-5678-1234-567812345678": [
            Mapping(text_id="text1", segments=["b", "d"]),
            Mapping(text_id="text3", segments=["e"])
        ]
    }

    # Act
    result = _construct_update_segments(segments, update_dict)

    # Assert
    assert len(result) == 1
    updated_segment = result[0]
    assert str(updated_segment.id) == "12345678-1234-5678-1234-567812345678"
    assert len(updated_segment.mapping) == 2

    text1_mapping = next(m for m in updated_segment.mapping if m.text_id == "text1")
    assert set(text1_mapping.segments) == {"a", "b", "d"}

    text3_mapping = next(m for m in updated_segment.mapping if m.text_id == "text3")
    assert text3_mapping.segments == ["e"]
