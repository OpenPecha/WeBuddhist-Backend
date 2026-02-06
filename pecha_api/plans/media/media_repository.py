from sqlalchemy.orm import Session

from pecha_api.texts.text_images_models import TextImage


def create_text_image(db: Session, text_id: str, image_url: str) -> TextImage:
    new_text_image = TextImage(text_id=text_id, image_url=image_url)
    db.add(new_text_image)
    db.commit()
    db.refresh(new_text_image)
    return new_text_image
