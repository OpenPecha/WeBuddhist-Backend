from pecha_api.text_uploader.mapping.mapping_repository import trigger_mapping_repo
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest
class MappingService:
    def __init__(self):
        self.all_text = {}

    async def trigger_mapping(self, text_ids: dict[str, str], text_upload_request: TextUploadRequest):
        text_ids_list = list(text_ids.values())
        source = text_upload_request.openpecha_api_url
        destination = text_upload_request.destination_url
        await trigger_mapping_repo(text_ids_list, source, destination)