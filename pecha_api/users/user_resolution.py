from typing import Any, Dict
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from .users_models import Users
from .users_repository import get_user_by_email, get_user_by_id, get_user_by_phone


def resolve_user_from_payload(db, payload: Dict[str, Any], unauthorized_detail: str) -> Users:
    subject = payload.get("sub")
    if subject is not None:
        try:
            return get_user_by_id(db=db, user_id=UUID(str(subject)))
        except (TypeError, ValueError):
            pass

    phone_number = payload.get("phone_number")
    if isinstance(phone_number, str) and phone_number:
        user = get_user_by_phone(db=db, phone_number=phone_number)
        if user is not None:
            return user

    email = payload.get("email")
    if isinstance(email, str) and email:
        return get_user_by_email(db=db, email=email)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=unauthorized_detail,
    )
