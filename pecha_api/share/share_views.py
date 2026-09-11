from fastapi import APIRouter, Depends, Query
from starlette import status
from typing import Optional

from .share_response_models import (
    ShareRequest,
    ShortUrlResponse
)

from .share_service import (
    get_generated_image,
    generate_short_url
)

share_router = APIRouter(
    prefix="/share",
    tags=["Share"]
)

# Social crawlers send HEAD to check an image before fetching it; a GET-only
# route answers 405 and the crawler then shows no preview image at all.
@share_router.api_route("/image", methods=["GET", "HEAD"], status_code=status.HTTP_200_OK)
async def get_image(
    segment_id: Optional[str] = Query(default=None),
    poem_id: Optional[str] = Query(default=None)
):
    return await get_generated_image(poem_id=poem_id)

@share_router.post("", status_code=status.HTTP_201_CREATED)
async def get_short_url(share_request: ShareRequest) -> ShortUrlResponse:
    return await generate_short_url(share_request=share_request)