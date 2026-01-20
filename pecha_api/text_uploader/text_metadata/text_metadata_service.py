from typing import Any, List
import logging

from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest
from pecha_api.text_uploader.text_metadata.text_metadata_model import CriticalInstanceResponse, TextInstanceIds
from pecha_api.text_uploader.text_metadata.text_group_repository import (
    post_group,
    get_critical_instances,
    post_text,
    get_text_related_by_work,
    get_text_metadata
)
from pecha_api.text_uploader.collections.collections_repository import get_collection_by_pecha_collection_id
from pecha_api.text_uploader.text_metadata.text_metadata_model import TextGroupPayload
from pecha_api.text_uploader.text_metadata.text_group_repository import get_texts_by_pecha_text_ids


logging.basicConfig(level=logging.INFO)

class TextMetadataService:
    def __init__(self):
        self.version_group_id: str | None = None
        self.commentary_group_id: str | None = None
        self.text_ids: list[str] = []
        self.category: dict[str, str] = {}
        self.all_instance_ids: dict[str, str] = {}


    async def upload_text_metadata_service(self, text_upload_request: TextUploadRequest, token: str):
        text_id = text_upload_request.text_id
        text = await get_text_metadata(text_id, text_upload_request.openpecha_api_url)

        related_text_ids = []
        commentary_text_ids = []
        work_translation_group = {}

        text_related_by_work_response = await get_text_related_by_work(text_id, text_upload_request.openpecha_api_url)
        for key in text_related_by_work_response.keys():
            if text_related_by_work_response[key]["relation"] not in ['commentary', 'sibling_commentary']:
                work_translation_group[key] = text_related_by_work_response[key]["expression_ids"]
                expression_ids = text_related_by_work_response[key]["expression_ids"]
                related_text_ids.extend(expression_ids)
            else:
                commentary_ids = text_related_by_work_response[key]["expression_ids"]
                commentary_text_ids.extend(commentary_ids)
        if text["type"] not in ['commentary', 'sibling_commentary']:
            related_text_ids.append(text_id)
        else:
            commentary_text_ids.append(text_id)
        new_texts = await self.get_text_meta_data_service(text_ids=related_text_ids, type="translation", text_upload_request=text_upload_request, token=token)
        new_commentary_texts = await self.get_text_meta_data_service(text_ids=commentary_text_ids, type="commentary", text_upload_request=text_upload_request, token=token)
        new_texts.update(new_commentary_texts)
        
        result = TextInstanceIds(new_text=new_texts, all_text=self.all_instance_ids)
        
        # Reset
        self.version_group_id = None
        self.commentary_group_id = None
        self.all_instance_ids = {}
        return result

    async def get_text_meta_data_service(self, text_ids: List[str], type: str,text_upload_request: TextUploadRequest, token: str):

        if len(text_ids) == 0:
            return {}

        uploaded_texts, uploaded_text_ids, instances = await self.get_uploaded_texts(text_ids, text_upload_request.openpecha_api_url, text_upload_request.destination_url)

        if len(uploaded_texts) > 0 and type == "translation":
            group_id = uploaded_texts[0]['group_id']
            self.version_group_id = group_id

        new_texts = {}
        for text_id in text_ids:
            text_metadata = await get_text_metadata(text_id, text_upload_request.openpecha_api_url)
            language = text_metadata['language']
            title = text_metadata['title'][language]

            if text_id in uploaded_text_ids:
                logging.info(f"Skipping already uploaded text: {title}")
                continue
            
            if type == "translation":
                if not self.version_group_id:
                    group_response = await post_group('text', text_upload_request.destination_url, token)
                    self.version_group_id = group_response["id"]
                    logging.info(f"Created new group {group_response['id']} for translation")

                payload = await self.create_textmetada_payload(text_id, text_metadata, type="version", text_upload_request=text_upload_request)

            elif type == "commentary":
                group_response = await post_group('commentary', text_upload_request.destination_url, token)
                self.commentary_group_id = group_response["id"]
                logging.info(f"Created new group {group_response['id']} for commentary")

                payload = await self.create_textmetada_payload(text_id, text_metadata, type="commentary", text_upload_request=text_upload_request)

            text_response = await post_text(payload, token, text_upload_request.destination_url)   
            response_text_id = text_response["id"]
            new_texts[response_text_id] = instances[text_id]
            
            logging.info(f"Created new text {text_response['title']}")

        # get all instance ids
        self.all_instance_ids = instances
        
        return new_texts

            
           


    async def create_textmetada_payload(self, text_id: str, text_metadata: dict[str, Any], type: str, text_upload_request: TextUploadRequest):
        language = text_metadata['language']
        title = text_metadata['title'][language]
        instance = await self.get_text_critical_instance(text_id, text_upload_request.openpecha_api_url)

        if type == "version":
            category_id = text_metadata.get("category_id", "")
            wb_category_id = await self.get_wb_collection_id(pecha_collection_id=category_id, destination_url=text_upload_request.destination_url)
            category_ids = [wb_category_id]
            group_id = self.version_group_id
        elif type == "commentary":
            category_ids = [self.version_group_id]
            group_id = self.commentary_group_id

        return TextGroupPayload(
            pecha_text_id=instance.critical_instances[0].id,
            title=title,
            language=language,
            isPublished=text_metadata.get("isPublished", True),
            group_id=group_id,
            published_by="",
            type=type,
            categories=category_ids,  
            views=text_metadata.get("views", 0),
            source_link=instance.critical_instances[0].source,
            ranking=text_metadata.get("ranking"),
            license=text_metadata.get("license"),
        )



    async def get_text_critical_instance(self, text_id: str, openpecha_api_url: str) -> CriticalInstanceResponse:
        critical_instances_response = await get_critical_instances(text_id, openpecha_api_url)
        critical_instances_list = critical_instances_response.critical_instances
        return CriticalInstanceResponse(critical_instances=critical_instances_list)

    async def get_uploaded_texts(self, text_ids: List[str], openpecha_api_url: str, destination_url: str):
        instances = {}
        expressions = {}
        for text_id in text_ids:
            text_critical_instance = await self.get_text_critical_instance(text_id, openpecha_api_url)
            instance_id = text_critical_instance.critical_instances[0].id
            instances[text_id] = instance_id
            expressions[instance_id] = text_id
        
        instance_ids = instances.values()
        texts = await get_texts_by_pecha_text_ids(pecha_text_ids=instance_ids, destination_url=destination_url)
        pecha_text_ids = [text['pecha_text_id'] for text in texts]
        uploaded_text_ids = [expressions[id] for id in instance_ids if id in pecha_text_ids]

        return texts, uploaded_text_ids, instances

    async def get_wb_collection_id(self, pecha_collection_id: str, destination_url: str) -> str:
        wb_collection_id = await get_collection_by_pecha_collection_id(pecha_collection_id=pecha_collection_id, destination_url=destination_url)
        if wb_collection_id is None:
            raise ValueError(f"Collection with pecha_collection_id {pecha_collection_id} not found")
        return wb_collection_id


