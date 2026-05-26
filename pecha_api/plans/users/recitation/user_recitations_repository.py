from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from fastapi import HTTPException
from starlette import status
from typing import List, Optional, Dict
from uuid import UUID
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST, NOT_FOUND
from pecha_api.plans.users.recitation.user_recitations_models import UserRecitations

def save_user_recitation(db: Session, user_recitations: UserRecitations) -> None:
    try:
        db.add(user_recitations)
        db.commit()
        db.refresh(user_recitations)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump())

def get_user_recitations_by_user_id(db: Session, user_id: UUID) -> List[UserRecitations]:
    return db.query(UserRecitations).filter(
        UserRecitations.user_id == user_id
    ).order_by(UserRecitations.display_order).all()

def get_max_display_order_for_user(db: Session, user_id: UUID) -> Optional[int]:
    result = db.query(func.max(UserRecitations.display_order)).filter(
        UserRecitations.user_id == user_id
    ).scalar()
    return result

def update_recitation_order_in_bulk(db: Session, user_id: UUID, recitation_updates: List[Dict]) -> None:
    try:
        for update in recitation_updates:
            recitation = db.query(UserRecitations).filter(
                UserRecitations.text_id == update["text_id"],
                UserRecitations.user_id == user_id
            ).first()           
            if recitation:
                recitation.display_order = update["display_order"]      
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump())
    return db.query(UserRecitations).filter(UserRecitations.user_id == user_id).all()

def delete_user_recitation(db: Session, user_id: UUID, text_id: UUID) -> None:
    try:
        recitation = db.query(UserRecitations).filter(UserRecitations.user_id == user_id, UserRecitations.text_id == text_id).first()
        
        if not recitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=ResponseError(error="NOT_FOUND",message=f"Recitation with ID {text_id} not found for this user").model_dump())      
        
        db.delete(recitation)
        db.commit()

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=ResponseError(error=BAD_REQUEST,message=f"Database integrity error: {str(e.orig)}").model_dump())