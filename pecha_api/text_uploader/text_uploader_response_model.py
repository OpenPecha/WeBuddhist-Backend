from pydantic import BaseModel


class TextUploadRequest(BaseModel):
    destination_url: str
    openpecha_api_url: str
    text_id: str


class TextUploadResponse(BaseModel):
    message: dict[str, str] | str
