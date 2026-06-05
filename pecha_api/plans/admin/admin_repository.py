from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from pecha_api.plans.authors.plan_authors_model import Author
from pecha_api.plans.platform_enums import PlatformRole


def list_authors_admin(
    db: Session,
    *,
    skip: int,
    limit: int,
    is_verified: Optional[bool] = None,
    is_active: Optional[bool] = None,
    platform_role: Optional[PlatformRole] = None,
    search: Optional[str] = None,
) -> Tuple[List[Author], int]:
    query = db.query(Author).filter(Author.deleted_at.is_(None))
    if is_verified is not None:
        query = query.filter(Author.is_verified == is_verified)
    if is_active is not None:
        query = query.filter(Author.is_active == is_active)
    if platform_role is not None:
        query = query.filter(Author.platform_role == platform_role.value)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (Author.email.ilike(pattern))
            | (Author.first_name.ilike(pattern))
            | (Author.last_name.ilike(pattern))
        )
    total = query.with_entities(func.count(Author.id)).scalar() or 0
    rows = (
        query.order_by(Author.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, int(total)


def count_super_admins(db: Session) -> int:
    return (
        db.query(func.count(Author.id))
        .filter(
            Author.deleted_at.is_(None),
            Author.platform_role == PlatformRole.SUPER_ADMIN.value,
        )
        .scalar()
        or 0
    )


def save_author(db: Session, author: Author) -> Author:
    db.add(author)
    db.commit()
    db.refresh(author)
    return author
