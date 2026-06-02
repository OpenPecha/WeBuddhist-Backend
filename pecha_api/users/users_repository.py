import logging
from typing import List
from sqlalchemy.exc import InvalidRequestError, IntegrityError
from sqlalchemy.orm import Session
from .users_models import Users, SocialMediaAccount
from fastapi import HTTPException
from starlette import status
from pecha_api.error_contants import ErrorConstants


def save_user(db: Session, user: Users) -> Users:
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ErrorConstants.USER_ALREADY_EXISTS)

def update_user(db: Session, user: Users) -> Users:
    try:
        updated_user = db.merge(user)
        db.commit()
        db.refresh(updated_user)
        return updated_user
    except IntegrityError as e:
        db.rollback()
        print(f"Integrity error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorConstants.USER_UPDATE_ISSUE)
    except InvalidRequestError as e:
        db.rollback()
        print(f"InvalidRequestError error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorConstants.INVALID_UPDATE_REQUEST)


def get_user_by_email(db: Session, email: str) -> Users:
    user = db.query(Users).filter(Users.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.USER_NOT_FOUND)
    return user


def get_user_by_username(db: Session, username: str) -> Users:
    user = db.query(Users).filter(Users.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.USER_NOT_FOUND)
    return user

def get_user_social_account(db: Session, user_id: str) -> List[SocialMediaAccount]:
    social_accounts = db.query(SocialMediaAccount).filter(SocialMediaAccount.user_id == user_id).all()
    return social_accounts


def delete_user(db: Session, user: Users) -> None:
    try:
        from pecha_api.plans.users.recitation.user_recitations_models import UserRecitations
        db.query(UserRecitations).filter(UserRecitations.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.exception(f"Failed to delete user {user.id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=ErrorConstants.USER_DELETE_FAILED)
