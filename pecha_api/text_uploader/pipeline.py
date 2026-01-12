import asyncio
from fastapi import HTTPException
from starlette import status
from pecha_api.error_contants import ErrorConstants


from pecha_api.text_uploader.collections.collection_service import CollectionService
from pecha_api.text_uploader.text_metadata.text_metadata_service import TextMetadataService
from pecha_api.text_uploader.segments.segment_service import SegmentService
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest
from pecha_api.text_uploader.table_of_content.toc_service import TocService
from pecha_api.text_uploader.mapping.mapping_services import MappingService
from pecha_api.users.users_service import verify_admin_access
from pecha_api.text_uploader.constants import DestinationURL, OpenPechaAPIURL

from pecha_api.text_uploader.text_uploader_response_model import TextUploadResponse


async def pipeline(text_upload_request: TextUploadRequest, token: str)-> TextUploadResponse:

    destination_url_enum = text_upload_request.destination_url
    openpecha_api_url_enum = text_upload_request.openpecha_api_url
    destination_url = DestinationURL[destination_url_enum].value
    openpecha_api_url = OpenPechaAPIURL[openpecha_api_url_enum].value

    text_upload_request_payload = TextUploadRequest(
        destination_url=destination_url,
        openpecha_api_url=openpecha_api_url,
        text_id=text_upload_request.text_id,
    )

    is_admin = verify_admin_access(token=token)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorConstants.ADMIN_ERROR_MESSAGE)

    # # collection upload
    collection = CollectionService()
    await collection.upload_collections(text_upload_request=text_upload_request_payload, token=token)

    # text metadata upload
    text_metadata = TextMetadataService()
    instance_ids_response = await text_metadata.upload_text_metadata_service(text_upload_request=text_upload_request_payload, token=token)

    new_texts = instance_ids_response.new_text
    all_text = instance_ids_response.all_text

    new_uploaded_texts_count = len(new_texts)

    if new_uploaded_texts_count > 0:
        # segment upload
        segment = SegmentService()
        await segment.upload_segments(text_upload_request=text_upload_request_payload,text_ids = new_texts, token=token)

        # table of content upload
        toc = TocService()
        await toc.upload_toc(text_ids=new_texts, text_upload_request=text_upload_request_payload, token=token)

   

    #mapping upload
    if text_upload_request.destination_url != DestinationURL.LOCAL.name:
        mapping = MappingService()
        await mapping.trigger_mapping(text_ids=all_text, text_upload_request=text_upload_request)


    if new_uploaded_texts_count > 0:

        return TextUploadResponse(message=new_texts)
    else:
        return TextUploadResponse(message="All texts are already uploaded")