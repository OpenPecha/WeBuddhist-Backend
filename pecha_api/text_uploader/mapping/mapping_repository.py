from pecha_api.text_uploader.constants import SQSURL
from pecha_api.config import get_int
from pecha_api.text_uploader.mapping.mapping_model import TriggerMappingPayload
import httpx
from fastapi import HTTPException

async def trigger_mapping_repo(text_ids: list[str], source: str, destination: str):

    url = f"{SQSURL.DEVELOPMENT.value}/job/text-ids"
    headers = {
        "Content-Type": "application/json",
    }
    timeout = get_int("SQS_TIMEOUT")

    payload = TriggerMappingPayload(text_ids=text_ids, source=source, destination=destination).model_dump()
    print("payload>>>>>>>>>>>>>>>>", payload)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url,
            json=payload,
            headers=headers
        )

        if not response.is_success:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()