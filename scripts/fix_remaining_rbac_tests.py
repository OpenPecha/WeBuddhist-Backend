"""Align remaining plan CMS tests with group-scoped RBAC."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    print(f"updated {path.relative_to(ROOT)}")


def fix_audio_tests() -> None:
    path = ROOT / "tests/plans/audio/test_cms_plan_audio_service.py"
    text = _read(path)
    text = text.replace(
        """    mock_repo.assert_called_once_with(
        db=mock_db,
        search="recording",
        plan_id=plan_id,
        author_id=author.id,
        is_admin=False,
        skip=0,
        limit=10,
    )""",
        """    mock_repo.assert_called_once_with(
        db=mock_db,
        search="recording",
        plan_id=plan_id,
        group_ids=[],
        see_all=False,
        skip=0,
        limit=10,
    )""",
    )
    text = text.replace(
        '    assert mock_repo.call_args.kwargs["is_admin"] is True\n',
        '    assert mock_repo.call_args.kwargs["see_all"] is True\n',
    )
    text = text.replace(
        "    plan = MagicMock()\n    plan.author_id = author.id\n",
        "    plan = MagicMock()\n    plan.author_id = author.id\n    plan.group_id = uuid.uuid4()\n",
    )
    _write(path, text)
    path = ROOT / "tests/plans/audio/test_plan_day_audio_service.py"
    text = _read(path)
    text = text.replace("author.is_admin = True", "author.platform_role = PlatformRole.SUPER_ADMIN")
    if "author.is_admin = False" in text:
        text = text.replace("author.is_admin = False", "author.platform_role = PlatformRole.CREATOR")
    _write(path, text)


def fix_author_details_test() -> None:
    path = ROOT / "tests/plans/authors/test_plan_author_service.py"
    text = _read(path)
    old = """    async def test_get_author_details_success(
        self,
        mock_generate_presigned_url,
        mock_get_config,
        mock_get_social_profile,
        mock_build_author_access_context,
        mock_validate_and_extract,
    ):"""
    new = """    async def test_get_author_details_success(
        self,
        mock_validate_and_extract,
        mock_build_author_access_context,
        mock_get_social_profile,
        mock_get_config,
        mock_generate_presigned_url,
    ):"""
    if old in text:
        text = text.replace(old, new)
    _write(path, text)


def fix_dashboard() -> None:
    path = ROOT / "tests/plans/dashboard/test_dashboard_service.py"
    text = _read(path)
    text = text.replace(
        '    assert mock_repo.call_args.kwargs["author_id"] is None\n',
        '    assert mock_repo.call_args.kwargs["group_ids"] is None\n',
    )
    text = text.replace(
        """    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([], 0),
    ) as mock_repo:
        _session_local_context(mock_session_local)
        get_dashboard_items_list(
            token="author-token",
            tab="series",
            page=1,
            page_size=10,
            search="found",
            status=PlanStatus.PUBLISHED,
            language="en",
            featured=False,
        )

    mock_repo.assert_called_once()
    kwargs = mock_repo.call_args.kwargs
    assert kwargs["author_id"] == author_id""",
        """    group_ids = [uuid.uuid4()]
    with patch(
        "pecha_api.plans.dashboard.dashboard_service.validate_cms_author_details",
        return_value=mock_author,
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.SessionLocal"
    ) as mock_session_local, patch(
        "pecha_api.plans.dashboard.dashboard_service.get_author_group_ids",
        return_value=group_ids,
    ), patch(
        "pecha_api.plans.dashboard.dashboard_service.get_dashboard_items",
        return_value=([], 0),
    ) as mock_repo:
        _session_local_context(mock_session_local)
        get_dashboard_items_list(
            token="author-token",
            tab="series",
            page=1,
            page_size=10,
            search="found",
            status=PlanStatus.PUBLISHED,
            language="en",
            featured=False,
        )

    mock_repo.assert_called_once()
    kwargs = mock_repo.call_args.kwargs
    assert kwargs["group_ids"] == group_ids""",
    )
    _write(path, text)


def fix_plan_items() -> None:
    path = ROOT / "tests/plans/items/test_plan_items_services.py"
    text = _read(path)
    text = text.replace("author.is_admin = False", "author.platform_role = PlatformRole.CREATOR")
    text = text.replace("author.is_admin = True", "author.platform_role = PlatformRole.SUPER_ADMIN")
    text = re.sub(
        r"(    plan = MagicMock\(\)\n    plan\.id = plan_id\n)",
        r"\1    plan.deleted_at = None\n    plan.group_id = uuid.uuid4()\n",
        text,
    )
    text = re.sub(
        r"(    plan = MagicMock\(\)\n    plan\.id = [^\n]+\n)",
        lambda m: m.group(1)
        if "plan.deleted_at" in m.group(0) or "plan.group_id" in m.group(0)
        else m.group(1) + "    plan.deleted_at = None\n    plan.group_id = uuid.uuid4()\n",
        text,
    )
    if "from pecha_api.plans.platform_enums import PlatformRole" not in text:
        text = text.replace(
            "from pecha_api.plans.platform_enums import PlatformRole",
            "from pecha_api.plans.platform_enums import PlatformRole",
        )
    _write(path, text)


def fix_plan_views() -> None:
    path = ROOT / "tests/plans/cms/test_plan_views.py"
    text = _read(path)
    if "group_id=" not in text.split("test_create_plan_success")[1].split("async def")[0]:
        text = text.replace(
            """    request = CreatePlanRequest(
        title="Mindfulness Basics",""",
            """    request = CreatePlanRequest(
        group_id=uuid.uuid4(),
        title="Mindfulness Basics",""",
            1,
        )
    _write(path, text)


def fix_plan_service() -> None:
    path = ROOT / "tests/plans/cms/test_plan_service.py"
    text = _read(path)
    text = text.replace(
        "    mock_series = MagicMock()\n    mock_series.author_id = uuid.uuid4()\n",
        "    mock_series = MagicMock()\n    mock_series.author_id = uuid.uuid4()\n    mock_series.group_id = TEST_GROUP_ID\n",
    )
    text = text.replace(
        "    mock_series.author_id = author_id\n",
        "    mock_series.author_id = author_id\n    mock_series.group_id = TEST_GROUP_ID\n",
    )
    # get_details plan needs group_id and deleted_at
    text = text.replace(
        """    plan = Plan(
        id=uuid.uuid4(),
        title="Test Plan",
        description="Test Description",
        image_url="https://example.com/image.jpg",
        status=PlanStatus.PUBLISHED,
        author_id=uuid.uuid4(),
        created_by="tester@example.com",
    )""",
        """    plan = Plan(
        id=uuid.uuid4(),
        title="Test Plan",
        description="Test Description",
        image_url="https://example.com/image.jpg",
        status=PlanStatus.PUBLISHED,
        author_id=uuid.uuid4(),
        group_id=TEST_GROUP_ID,
        created_by="tester@example.com",
    )""",
    )
    text = text.replace(
        "        mock_get_plan_by_id.assert_called_once_with(db=db_session, plan_id=plan.id)\n",
        "        assert mock_get_plan_by_id.call_count == 2\n",
    )
    # mock_plan blocks in update tests - add group_id and deleted_at
    text = re.sub(
        r"(mock_plan\.display_order = None\n)",
        r"\1    mock_plan.group_id = TEST_GROUP_ID\n    mock_plan.deleted_at = None\n",
        text,
    )
    # get_plan_day_details tests need get_plan_by_id patch
    for fn in (
        "test_get_plan_day_details_success",
        "test_get_plan_day_details_not_found",
        "test_get_plan_day_details_no_subtasks",
    ):
        if f'patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id")' not in text.split(f"def {fn}")[1].split("\n\n")[0]:
            text = text.replace(
                f'    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \\\n        patch("pecha_api.plans.cms.cms_plans_service.get_plan_day_with_tasks_and_subtasks")',
                f'    mock_plan_for_day = MagicMock()\n    mock_plan_for_day.group_id = TEST_GROUP_ID\n    mock_plan_for_day.deleted_at = None\n\n    with patch("pecha_api.plans.cms.cms_plans_service.SessionLocal") as mock_session_local, \\\n        patch("pecha_api.plans.cms.cms_plans_service.get_plan_by_id", return_value=mock_plan_for_day), \\\n        patch("pecha_api.plans.cms.cms_plans_service.get_plan_day_with_tasks_and_subtasks")',
                1,
            )
    _write(path, text)


def fix_series_plans_group_id() -> None:
    path = ROOT / "tests/plans/series/test_series_service.py"
    text = _read(path)
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    plan_var: str | None = None
    for line in lines:
        m = re.match(r"    (plan(?:_[a-z]+)?|deleted_plan|published_plan|draft_plan|archived_plan|conflicting_plan|existing_plan(?:_[a-z]+)?|fetched_plan(?:_[a-z]+)?|other_authors_plan|valid_plan|attached_plan) = MagicMock\(\)\n", line)
        if m:
            plan_var = m.group(1)
        if plan_var and line.strip().startswith(f"{plan_var}.") and "group_id" in line:
            plan_var = None
        if plan_var and re.match(rf"    {plan_var}\.[a-z_]+ = .+\n", line):
            out.append(line)
            continue
        if plan_var and line.strip() == "":
            out.append(f"    {plan_var}.group_id = FIXTURE_GROUP_ID\n")
            plan_var = None
            out.append(line)
            continue
        if plan_var and (line.startswith("    row = MagicMock") or line.startswith("    with patch") or line.startswith("def test_")):
            out.append(f"    {plan_var}.group_id = FIXTURE_GROUP_ID\n")
            plan_var = None
        out.append(line)
    _write(path, "".join(out))


def fix_series_views() -> None:
    path = ROOT / "tests/plans/series/test_series_views.py"
    text = _read(path)
    text = text.replace(
        """    payload = {
        "metadata": [{"title": "New Series", "language": "EN"}],
        "image_key": "series/uploads/key.jpg",
        "featured": False,
    }""",
        """    payload = {
        "group_id": str(uuid.uuid4()),
        "metadata": [{"title": "New Series", "language": "EN"}],
        "image_key": "series/uploads/key.jpg",
        "featured": False,
    }""",
    )
    text = text.replace(
        """    payload = {
        "metadata": [{"title": "Minimal", "language": "EN"}],
    }""",
        """    payload = {
        "group_id": str(uuid.uuid4()),
        "metadata": [{"title": "Minimal", "language": "EN"}],
    }""",
    )
    _write(path, text)


def fix_public_plan() -> None:
    path = ROOT / "tests/plans/public/test_plan_public_service.py"
    text = _read(path)
    fixture_group = "FIXTURE_GROUP_ID = uuid4()"
    if fixture_group not in text:
        text = text.replace(
            "from pecha_api.plans.plans_enums import ContentType\n",
            "from pecha_api.plans.plans_enums import ContentType\n\nFIXTURE_GROUP_ID = uuid4()\n",
        )
    text = text.replace(
        "    plan.deleted_at = None\n    plan.start_date = None\n    return plan",
        "    plan.deleted_at = None\n    plan.start_date = None\n    plan.group_id = FIXTURE_GROUP_ID\n    return plan",
    )
    _write(path, text)


def fix_sub_tasks_order_test() -> None:
    path = ROOT / "tests/plans/sub_tasks/test_plan_sub_tasks_services.py"
    text = _read(path)
    text = text.replace(
        """        mock_get_task.assert_called_once_with(
            db=db_mock,
            task_id=task_id,
            current_author=mock_validate.return_value,
            is_admin=mock_validate.return_value.is_admin
        )""",
        """        mock_get_task.assert_called_once_with(
            db=db_mock,
            task_id=task_id,
            current_author=mock_validate.return_value,
        )""",
    )
    _write(path, text)


def fix_tasks_subtasks() -> None:
    path = ROOT / "tests/plans/tasks/test_plan_tasks_services.py"
    text = _read(path)
    text = text.replace(
        """async def test_delete_task_by_id_unauthorized():
    \"\"\"Test task deletion fails when user is not the task creator.\"\"\"
    task_id = uuid.uuid4()
    token = "valid_token_123"
    author_email = "author@example.com"
    different_author_email = "different@example.com"

    mock_author = SimpleNamespace(id=__import__('uuid').uuid4(), email=author_email, platform_role=PlatformRole.CREATOR, is_active=True)

    mock_task = SimpleNamespace(
        id=task_id,
        title="Test Task",
        created_by=different_author_email,
        plan_item_id=uuid.uuid4(),
    )

    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    with patch(
        "pecha_api.plans.tasks.plan_tasks_services.validate_cms_author_details",
        return_value=SimpleNamespace(id=__import__('uuid').uuid4(), email=author_email, platform_role=PlatformRole.CREATOR, is_active=True),
    ) as mock_validate, patch(
        "pecha_api.plans.tasks.plan_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.plan_tasks_services.get_task_by_id",
        return_value=mock_task,
    ) as mock_get_task, patch(
        "pecha_api.plans.tasks.plan_tasks_services.delete_task",
    ) as mock_delete, patch(
        "pecha_api.plans.tasks.plan_tasks_services.get_tasks_by_plan_item_id",
    ) as mock_get_tasks, patch(
        "pecha_api.plans.tasks.plan_tasks_services._reorder_sequentially",
    ) as mock_reorder:
        with pytest.raises(HTTPException) as exc_info:
            await delete_task_by_id(task_id=task_id, token=token)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"] == FORBIDDEN
        assert exc_info.value.detail["message"] == UNAUTHORIZED_TASK_ACCESS

        assert mock_validate.call_count == 1
        assert mock_get_task.call_count == 1
        # ensure delete, get_tasks and reorder were not called
        assert mock_delete.call_count == 0
        assert mock_get_tasks.call_count == 0
        assert mock_reorder.call_count == 0""",
        """async def test_delete_task_by_id_unauthorized():
    \"\"\"Test task deletion fails when user lacks edit permission on the plan group.\"\"\"
    task_id = uuid.uuid4()
    token = "valid_token_123"
    author_email = "author@example.com"

    db_mock = MagicMock()
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock

    with patch(
        "pecha_api.plans.tasks.plan_tasks_services.validate_cms_author_details",
        return_value=SimpleNamespace(id=uuid.uuid4(), email=author_email, platform_role=PlatformRole.CREATOR, is_active=True),
    ) as mock_validate, patch(
        "pecha_api.plans.tasks.plan_tasks_services.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.plans.tasks.plan_tasks_services._get_author_task",
        side_effect=HTTPException(
            status_code=403,
            detail={"error": FORBIDDEN, "message": UNAUTHORIZED_TASK_ACCESS},
        ),
    ) as mock_get_author_task, patch(
        "pecha_api.plans.tasks.plan_tasks_services.delete_task",
    ) as mock_delete, patch(
        "pecha_api.plans.tasks.plan_tasks_services.get_tasks_by_plan_item_id",
    ) as mock_get_tasks, patch(
        "pecha_api.plans.tasks.plan_tasks_services._reorder_sequentially",
    ) as mock_reorder:
        with pytest.raises(HTTPException) as exc_info:
            await delete_task_by_id(task_id=task_id, token=token)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"] == FORBIDDEN
        assert exc_info.value.detail["message"] == UNAUTHORIZED_TASK_ACCESS

        assert mock_validate.call_count == 1
        assert mock_get_author_task.call_count == 1
        assert mock_delete.call_count == 0
        assert mock_get_tasks.call_count == 0
        assert mock_reorder.call_count == 0""",
    )

    # Patch _get_author_task for subtasks success/forbidden tests
    for test_name in (
        "test_get_task_subtasks_service_success",
        "test_get_task_subtasks_service_forbidden_when_not_creator",
        "test_get_task_subtasks_service_image_content_uses_presigned_url",
    ):
        block = text.split(f"async def {test_name}")[1].split("\n@pytest.mark.asyncio\nasync def")[0]
        if "_get_author_task" in block:
            continue
        old_patch = """    ), patch(
        "pecha_api.plans.tasks.plan_tasks_services.get_task_by_id",
        return_value=mock_task,
    ) as mock_get_task:"""
        new_patch = """    ), patch(
        "pecha_api.plans.tasks.plan_tasks_services._get_author_task",
        return_value=mock_task,
    ) as mock_get_task:"""
        if old_patch in text:
            text = text.replace(old_patch, new_patch, 1)

    text = text.replace(
        'assert mock_get_task.call_args.kwargs == {"db": db_mock, "task_id": task_id}',
        'assert mock_get_task.call_args.kwargs["task_id"] == task_id',
    )
    _write(path, text)


def main() -> None:
    fix_audio_tests()
    fix_author_details_test()
    fix_dashboard()
    fix_plan_items()
    fix_plan_views()
    fix_plan_service()
    fix_series_plans_group_id()
    fix_series_views()
    fix_public_plan()
    fix_sub_tasks_order_test()
    fix_tasks_subtasks()
    print("done")


if __name__ == "__main__":
    main()
