"""Patch task/item test mocks for RBAC."""
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

for rel in (
    "tests/plans/tasks/test_plan_tasks_services.py",
    "tests/plans/items/test_plan_items_services.py",
    "tests/plans/audio/test_plan_day_audio_service.py",
):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if "from pecha_api.plans.platform_enums import PlatformRole" not in text:
        text = "from pecha_api.plans.platform_enums import PlatformRole\n" + text
    text = text.replace(
        "SimpleNamespace(email=author_email, is_admin=False)",
        "SimpleNamespace(id=__import__('uuid').uuid4(), email=author_email, platform_role=PlatformRole.CREATOR, is_active=True)",
    )
    text = text.replace(
        'SimpleNamespace(email="creator@example.com", is_admin=False)',
        'SimpleNamespace(id=__import__("uuid").uuid4(), email="creator@example.com", platform_role=PlatformRole.CREATOR, is_active=True)',
    )
    text = text.replace(
        'SimpleNamespace(email="current_user@example.com", is_admin=False)',
        'SimpleNamespace(id=__import__("uuid").uuid4(), email="current_user@example.com", platform_role=PlatformRole.CREATOR, is_active=True)',
    )
    text = text.replace(
        'SimpleNamespace(email="owner@example.com", is_admin=False)',
        'SimpleNamespace(id=__import__("uuid").uuid4(), email="owner@example.com", platform_role=PlatformRole.CREATOR, is_active=True)',
    )
    text = text.replace(", is_admin=False)", ", platform_role=PlatformRole.CREATOR, is_active=True)")
    text = text.replace("is_admin=False,", "platform_role=PlatformRole.CREATOR, is_active=True,")
    text = text.replace(
        "_get_author_task(db=db, task_id=task_id, current_author=current_author, is_admin=False)",
        "_get_author_task(db=db, task_id=task_id, current_author=current_author)",
    )
    path.write_text(text, encoding="utf-8")
    print("updated", path)
