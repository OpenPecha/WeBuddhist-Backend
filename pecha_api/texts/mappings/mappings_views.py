from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from .mappings_response_models import TextMappingRequest
from .mappings_service import update_segment_mapping, delete_segment_mapping
from ..segments.segments_response_models import SegmentResponse

oauth2_scheme = HTTPBearer()

mapping_router = APIRouter(
    prefix="/mappings",
    tags=["Text Mapping"]
)


@mapping_router.post("",status_code=status.HTTP_201_CREATED)
async def create_text_mapping(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
                              text_mapping_request: TextMappingRequest) -> SegmentResponse:
    return await update_segment_mapping(token=authentication_credential.credentials, text_mapping_request=text_mapping_request)

@mapping_router.delete("",status_code=status.HTTP_204_NO_CONTENT)
async def delete_text_mapping(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
                              text_mapping_request: TextMappingRequest) -> None:
    await delete_segment_mapping(token=authentication_credential.credentials, text_mapping_request=text_mapping_request)