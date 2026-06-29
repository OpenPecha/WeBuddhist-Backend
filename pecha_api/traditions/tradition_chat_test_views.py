from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette import status

from pecha_api.traditions.tradition_response_models import (
    TraditionChatRequest,
    TraditionChatResponse,
)
from pecha_api.traditions.tradition_service import tradition_chat_core

tradition_chat_test_router = APIRouter(
    prefix="/traditions/chat-test",
    tags=["Tradition Chat Test"],
)

_CHAT_TEST_HTML = Path(__file__).resolve().parent / "static" / "tradition_chat_test.html"


@tradition_chat_test_router.get("/view", include_in_schema=False)
def get_tradition_chat_test_view() -> FileResponse:
    return FileResponse(_CHAT_TEST_HTML, media_type="text/html")


@tradition_chat_test_router.post(
    "/chat",
    status_code=status.HTTP_200_OK,
    response_model=TraditionChatResponse,
    response_model_exclude_none=True,
    include_in_schema=False,
)
async def test_tradition_chat(chat_request: TraditionChatRequest) -> TraditionChatResponse:
    return await tradition_chat_core(chat_request=chat_request)
