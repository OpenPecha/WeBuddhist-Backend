from typing import Optional

from sqlalchemy.orm import Session

from pecha_api.plans.groups.groups_models import AuthorGroup, AuthorGroupMetadata
from pecha_api.users.users_models import Users


def get_group_notification_title(db: Session, group_id) -> str:
    entries = (
        db.query(AuthorGroupMetadata)
        .filter(AuthorGroupMetadata.group_id == group_id)
        .all()
    )
    for entry in entries:
        language = entry.language
        lang_value = language.value if hasattr(language, "value") else str(language)
        if lang_value.upper() == "EN":
            return entry.title
    if entries:
        return entries[0].title

    group = db.query(AuthorGroup).filter(AuthorGroup.id == group_id).first()
    if group and group.slug:
        return group.slug
    return "Group"


def get_user_by_email(db: Session, email: str) -> Optional[Users]:
    return db.query(Users).filter(Users.email == email).first()
