from typing import List, Dict
from sqlalchemy.orm import Session
from pecha_api.texts.text_images_models import TextImage

def get_text_images_by_text_ids(db: Session, text_ids: List[str]) -> Dict[str, str]:
    if not text_ids:
        return {}

    text_images = db.query(TextImage).filter(TextImage.text_id.in_(text_ids)).all()

    return {img.text_id: img.image_url for img in text_images}
