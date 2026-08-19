"""Shared utility functions for group post services."""
import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.plans.groups.groups_repository import get_group_by_id
from pecha_api.plans.response_message import NOT_FOUND

logger = logging.getLogger(__name__)


def isoformat(value: Any) -> Optional[str]:
    """Convert a value to ISO format string if it has isoformat method."""
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def validate_group_is_public(db: Session, group_id: UUID) -> None:
    """Validate that group exists and is public."""
    group = get_group_by_id(db=db, group_id=group_id)
    if not group or not group.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )
