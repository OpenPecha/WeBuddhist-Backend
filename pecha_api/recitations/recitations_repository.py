from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from pecha_api.recitations.recitations_response_models import RecitationDTO
from pecha_api.texts.text_images_models import TextImage

def apply_search_recitation_title_filter(texts: List[RecitationDTO], search: Optional[str]) -> List[RecitationDTO]:
    filtered_texts = []
    for text in texts:
        if search:
            if search.lower() in text.title.lower():
                filtered_texts.append(text)
        else:
            filtered_texts.append(text)
    return filtered_texts

def get_text_images_by_text_ids(db: Session, text_ids: List[str]) -> Dict[str, str]:
    if not text_ids:
        return {}

    text_images = db.query(TextImage).filter(TextImage.text_id.in_(text_ids)).all()

    return {img.text_id: img.image_url for img in text_images}
