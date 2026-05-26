from typing import Optional
from fastapi import APIRouter, Query
from starlette import status


from pecha_api.recitations.recitations_services import (
    get_list_of_recitations_service, 
    get_recitation_details_service
)

from pecha_api.recitations.recitations_response_models import(
    RecitationsResponse, 
    RecitationDetailsRequest, 
    RecitationDetailsResponse
)
recitation_router=APIRouter(
    prefix="/recitations",
    tags=["Recitations"],
)

@recitation_router.get("",status_code=status.HTTP_200_OK,response_model=RecitationsResponse)
async def get_list_of_recitations(search: Optional[str] = Query(None, description="Search by Recitation title"),language: str = Query()):
    return await get_list_of_recitations_service(search=search, language=language)

@recitation_router.post("/{text_id}",status_code=status.HTTP_200_OK,response_model=RecitationDetailsResponse)
async def get_recitation_details(text_id: str, recitation_details_request: RecitationDetailsRequest):
    return await get_recitation_details_service(text_id=text_id, recitation_details_request=recitation_details_request)
