import contextlib
import importlib
import uuid
from unittest.mock import MagicMock, patch

import pytest

from pecha_api.plans.platform_enums import PlatformRole


def make_cms_author(
    *,
    author_id=None,
    email="author@example.com",
    platform_role: PlatformRole = PlatformRole.CREATOR,
    is_admin: bool = False,
):
    author = MagicMock()
    author.id = author_id or uuid.uuid4()
    author.email = email
    author.platform_role = PlatformRole.SUPER_ADMIN if is_admin else platform_role
    author.is_active = True
    return author


_CMS_MODULES = (
    "pecha_api.plans.tasks.plan_tasks_services",
    "pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_services",
    "pecha_api.plans.tasks.sub_tasks.subtask_preset_service",
    "pecha_api.plans.items.plan_items_services",
    "pecha_api.plans.cms.cms_plans_service",
    "pecha_api.plans.series.series_service",
    "pecha_api.plans.audio.cms_plan_audio_service",
    "pecha_api.plans.audio.plan_day_audio_service",
    "pecha_api.plans.audio.plan_subtask_audio_service",
    "pecha_api.plans.dashboard.dashboard_service",
)

_PERMISSION_FUNCTIONS = (
    "require_can_create_content",
    "require_can_edit_content",
    "require_can_read_group_content",
    "require_can_change_status",
)


@pytest.fixture(autouse=True)
def _stub_cms_group_permissions():
    with contextlib.ExitStack() as stack:
        for module_path in _CMS_MODULES:
            module = importlib.import_module(module_path)
            for fn_name in _PERMISSION_FUNCTIONS:
                if fn_name in module.__dict__:
                    stack.enter_context(patch(f"{module_path}.{fn_name}"))
        yield
