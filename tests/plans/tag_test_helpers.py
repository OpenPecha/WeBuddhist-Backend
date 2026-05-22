from typing import List, Optional
from uuid import UUID, uuid4
from unittest.mock import MagicMock

from pecha_api.plans.tags.tag_response_models import TagSummaryDTO


def make_tag_summary(name: str, tag_id: Optional[UUID] = None) -> TagSummaryDTO:
    return TagSummaryDTO(id=tag_id or uuid4(), name=name)


def make_tag_summaries(names: List[str]) -> List[TagSummaryDTO]:
    return [make_tag_summary(name) for name in names]


def mock_tag_entity(name: str, tag_id: Optional[UUID] = None) -> MagicMock:
    tag = MagicMock()
    tag.id = tag_id or uuid4()
    tag.name = name
    tag.image_key = None
    tag.description = None
    tag.deleted_at = None
    return tag


def mock_tag_entities(names: List[str]) -> List[MagicMock]:
    return [mock_tag_entity(name) for name in names]
