from typing import List, Optional
from uuid import UUID, uuid4
from unittest.mock import MagicMock

from pecha_api.plans.tags.tag_response_models import TagSummaryDTO


def make_tag_summary(name: str, tag_id: Optional[UUID] = None) -> TagSummaryDTO:
    return TagSummaryDTO(id=tag_id or uuid4(), name=name)


def make_tag_summaries(names: List[str]) -> List[TagSummaryDTO]:
    return [make_tag_summary(name) for name in names]


def mock_tag_entity(name: str, tag_id: Optional[UUID] = None, language: str = "EN", description: Optional[str] = None) -> MagicMock:
    tag = MagicMock()
    tag.id = tag_id or uuid4()
    tag.name = name
    tag.image_key = None
    tag.description = description
    tag.deleted_at = None
    
    # Add metadata_entries for the new metadata-based structure
    meta = MagicMock()
    meta.id = uuid4()
    meta.name = name
    meta.description = description
    meta.language = MagicMock()
    meta.language.value = language
    tag.metadata_entries = [meta]
    
    return tag


def mock_tag_entities(names: List[str]) -> List[MagicMock]:
    return [mock_tag_entity(name) for name in names]
