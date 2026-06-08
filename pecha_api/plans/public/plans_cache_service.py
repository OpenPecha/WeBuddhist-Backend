from typing import Optional
from uuid import UUID

from pecha_api import config
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import get_cache_data, set_cache
from pecha_api.plans.public.plan_response_models import (
    PublicPlansResponse,
    PublicPlanDTO,
    PlanDaysResponse,
    PlanDayDTO,
    TagsResponse,
)
from pecha_api.plans.tags.tag_response_models import PublicTagsListResponse
from pecha_api.utils import Utils


def _plan_timeout() -> int:
    return config.get_int("CACHE_PLAN_TIMEOUT")


# ---------------------------------------------------------------------------
# Published plans list
# ---------------------------------------------------------------------------

async def get_published_plans_cache(
    tag: Optional[str],
    group_id: Optional[UUID],
    search: Optional[str],
    language: str,
    sort_by: str,
    sort_order: str,
    skip: int,
    limit: int,
) -> Optional[PublicPlansResponse]:
    payload = [tag, str(group_id), search, language, sort_by, sort_order, skip, limit, CacheType.PUBLISHED_PLANS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return PublicPlansResponse(**data)
    return None


async def set_published_plans_cache(
    tag: Optional[str],
    group_id: Optional[UUID],
    search: Optional[str],
    language: str,
    sort_by: str,
    sort_order: str,
    skip: int,
    limit: int,
    data: PublicPlansResponse,
) -> None:
    payload = [tag, str(group_id), search, language, sort_by, sort_order, skip, limit, CacheType.PUBLISHED_PLANS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_plan_timeout())


# ---------------------------------------------------------------------------
# Single plan detail
# ---------------------------------------------------------------------------

async def get_plan_detail_cache(plan_id: UUID) -> Optional[PublicPlanDTO]:
    payload = [str(plan_id), CacheType.PLAN_DETAIL]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return PublicPlanDTO(**data)
    return None


async def set_plan_detail_cache(plan_id: UUID, data: PublicPlanDTO) -> None:
    payload = [str(plan_id), CacheType.PLAN_DETAIL]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_plan_timeout())


# ---------------------------------------------------------------------------
# Plan days list
# ---------------------------------------------------------------------------

async def get_plan_days_cache(plan_id: UUID) -> Optional[PlanDaysResponse]:
    payload = [str(plan_id), CacheType.PLAN_DAYS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return PlanDaysResponse(**data)
    return None


async def set_plan_days_cache(plan_id: UUID, data: PlanDaysResponse) -> None:
    payload = [str(plan_id), CacheType.PLAN_DAYS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_plan_timeout())


# ---------------------------------------------------------------------------
# Single plan day detail
# ---------------------------------------------------------------------------

async def get_plan_day_detail_cache(plan_id: UUID, day_number: int) -> Optional[PlanDayDTO]:
    payload = [str(plan_id), day_number, CacheType.PLAN_DAY_DETAIL]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return PlanDayDTO(**data)
    return None


async def set_plan_day_detail_cache(plan_id: UUID, day_number: int, data: PlanDayDTO) -> None:
    payload = [str(plan_id), day_number, CacheType.PLAN_DAY_DETAIL]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_plan_timeout())


# ---------------------------------------------------------------------------
# Plan tags (by language)
# ---------------------------------------------------------------------------

async def get_plan_tags_cache(language: str) -> Optional[TagsResponse]:
    payload = [language, CacheType.PLAN_TAGS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return TagsResponse(**data)
    return None


async def set_plan_tags_cache(language: str, data: TagsResponse) -> None:
    payload = [language, CacheType.PLAN_TAGS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_plan_timeout())


# ---------------------------------------------------------------------------
# Public tags (paginated)
# ---------------------------------------------------------------------------

async def get_public_tags_cache(
    featured: Optional[bool],
    search: Optional[str],
    skip: int,
    limit: int,
) -> Optional[PublicTagsListResponse]:
    payload = [featured, search, skip, limit, CacheType.PUBLIC_TAGS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return PublicTagsListResponse(**data)
    return None


async def set_public_tags_cache(
    featured: Optional[bool],
    search: Optional[str],
    skip: int,
    limit: int,
    data: PublicTagsListResponse,
) -> None:
    payload = [featured, search, skip, limit, CacheType.PUBLIC_TAGS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_plan_timeout())
