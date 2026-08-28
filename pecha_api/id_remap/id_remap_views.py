from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from pecha_api.plans.auth.cms_auth_deps import get_cms_author_token

from .id_remap_response_models import IdRemapResult, SegmentIdRemapRequest, TextIdRemapRequest
from .id_remap_service import remap_segment_id, remap_text_id

id_remap_router = APIRouter(prefix="/cms/admin/id-remap", tags=["CMS Admin ID Remap"])


@id_remap_router.post("/segments", status_code=status.HTTP_200_OK, response_model=IdRemapResult)
async def post_remap_segment_id(
    body: SegmentIdRemapRequest,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return await remap_segment_id(
        token=token,
        old_segment_id=body.old_segment_id,
        new_segment_id=body.new_segment_id,
    )


@id_remap_router.post("/texts", status_code=status.HTTP_200_OK, response_model=IdRemapResult)
async def post_remap_text_id(
    body: TextIdRemapRequest,
    token: Annotated[str, Depends(get_cms_author_token)] = "",
):
    return await remap_text_id(
        token=token,
        old_text_id=body.old_text_id,
        new_text_id=body.new_text_id,
    )
