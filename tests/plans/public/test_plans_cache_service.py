import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pecha_api.cache.cache_enums import CacheType
from pecha_api.plans.public.plans_cache_service import (
    _plan_day_detail_cache_keys,
    invalidate_plan_day_detail_cache,
    schedule_invalidate_plan_day_cache_for_task,
)
from pecha_api.utils import Utils


@pytest.mark.asyncio
async def test_invalidate_plan_day_detail_cache_deletes_legacy_and_current_keys():
    plan_id = uuid.uuid4()
    day_number = 1
    expected_keys = _plan_day_detail_cache_keys(plan_id=plan_id, day_number=day_number)

    with patch(
        "pecha_api.plans.public.plans_cache_service.delete_cache",
        new_callable=AsyncMock,
    ) as mock_delete:
        await invalidate_plan_day_detail_cache(plan_id=plan_id, day_number=day_number)

    assert mock_delete.await_count == len(expected_keys)
    deleted_keys = [call.kwargs["hash_key"] for call in mock_delete.await_args_list]
    assert deleted_keys == expected_keys


def test_plan_day_detail_cache_keys_include_legacy_enum_format():
    plan_id = uuid.uuid4()
    day_number = 3

    keys = _plan_day_detail_cache_keys(plan_id=plan_id, day_number=day_number)
    legacy_key = Utils.generate_hash_key(
        payload=[str(plan_id), day_number, CacheType.PLAN_DAY_DETAIL]
    )

    assert legacy_key in keys


def test_schedule_invalidate_plan_day_cache_for_task_resolves_plan_day():
    task_id = uuid.uuid4()
    plan_item_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    db = MagicMock()

    with patch(
        "pecha_api.plans.public.plans_cache_service.get_task_by_id",
        return_value=MagicMock(plan_item_id=plan_item_id),
    ), patch(
        "pecha_api.plans.public.plans_cache_service.get_plan_item_by_id",
        return_value=MagicMock(plan_id=plan_id, day_number=2),
    ), patch(
        "pecha_api.plans.public.plans_cache_service.schedule_invalidate_plan_day_cache",
    ) as mock_schedule:
        schedule_invalidate_plan_day_cache_for_task(db=db, task_id=task_id)

    mock_schedule.assert_called_once_with(plan_id=plan_id, day_number=2)
