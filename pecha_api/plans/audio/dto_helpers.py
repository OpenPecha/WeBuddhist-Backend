from typing import Optional, Tuple

from pecha_api.config import get
from pecha_api.plans.audio.plan_item_audio_models import PlanItemAudio
from pecha_api.plans.audio.timestamp_service import timestamp_fields_from_subtask
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.plans_enums import ContentType
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from pecha_api.uploads.S3_utils import generate_presigned_access_url


def build_plan_day_audio_fields(
    plan_item: PlanItem,
) -> Tuple[Optional[str], Optional[int], Optional[str], bool]:
    audio = getattr(plan_item, "audio", None)
    audio_key = getattr(audio, "audio_key", None) if audio is not None else None
    if not audio_key or not isinstance(audio_key, str):
        return None, None, None, False
    audio_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=audio_key,
    )
    return audio_url, getattr(audio, "duration_ms", None), audio_key, True


def build_subtask_timestamp_fields(subtask: PlanSubTask) -> Tuple[Optional[int], Optional[int]]:
    return timestamp_fields_from_subtask(subtask)


def generate_subtask_content_url(content_type: ContentType, content: str) -> str:
    if content_type == ContentType.IMAGE and content:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=content,
        )
    return content or ""
