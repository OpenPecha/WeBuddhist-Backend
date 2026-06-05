"""One-off script to align plan CMS tests with RBAC schema."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# test_plan_service.py
plan_service = ROOT / "tests/plans/cms/test_plan_service.py"
text = plan_service.read_text(encoding="utf-8")
text = text.replace(
    "    request = CreatePlanRequest(\n        title=",
    "    request = CreatePlanRequest(\n        group_id=TEST_GROUP_ID,\n        title=",
)
text = text.replace("author.is_admin = False", "author.platform_role = PlatformRole.CREATOR")
text = text.replace("is_admin=False", "platform_role=PlatformRole.CREATOR")
text = text.replace("MagicMock(is_admin=False)", "MagicMock(platform_role=PlatformRole.CREATOR, is_active=True)")
text = text.replace(
    'MagicMock(id=author_id, is_admin=False)',
    'MagicMock(id=author_id, platform_role=PlatformRole.CREATOR, is_active=True)',
)
text = text.replace(
    'MagicMock(id=uuid.uuid4(), is_admin=False)',
    'MagicMock(id=uuid.uuid4(), platform_role=PlatformRole.CREATOR, is_active=True)',
)
text = text.replace('"is_admin": False', '"platform_role": PlatformRole.CREATOR')
if "require_can_create_content" not in text:
    text = text.replace(
        'patch("pecha_api.plans.cms.cms_plans_service.validate_cms_author_details")',
        'patch("pecha_api.plans.cms.cms_plans_service.require_can_create_content"), \\\n        patch("pecha_api.plans.cms.cms_plans_service.require_can_edit_content"), \\\n        patch("pecha_api.plans.cms.cms_plans_service.require_can_read_group_content"), \\\n        patch("pecha_api.plans.cms.cms_plans_service.require_can_change_status"), \\\n        patch("pecha_api.plans.cms.cms_plans_service.validate_cms_author_details")',
    )
plan_service.write_text(text, encoding="utf-8")
print("updated", plan_service)

# test_series_service.py
series_service = ROOT / "tests/plans/series/test_series_service.py"
stext = series_service.read_text(encoding="utf-8")
if "FIXTURE_GROUP_ID" not in stext:
    stext = stext.replace(
        "from pecha_api.plans.series.series_response_models import (",
        "from pecha_api.plans.platform_enums import PlatformRole\n\nFIXTURE_GROUP_ID = uuid.uuid4()\n\nfrom pecha_api.plans.series.series_response_models import (",
    )
stext = stext.replace(
    "    request = CreateSeriesRequest(\n        metadata=",
    "    request = CreateSeriesRequest(\n        group_id=FIXTURE_GROUP_ID,\n        metadata=",
)
stext = stext.replace(
    "def _make_mock_author(author_id, email=\"author@example.com\", is_admin=False):\n    author = MagicMock()\n    author.id = author_id\n    author.email = email\n    author.is_admin = is_admin\n    return author",
    "def _make_mock_author(author_id, email=\"author@example.com\", is_admin=False):\n    author = MagicMock()\n    author.id = author_id\n    author.email = email\n    author.platform_role = PlatformRole.SUPER_ADMIN if is_admin else PlatformRole.CREATOR\n    author.is_active = True\n    return author",
)
if "require_can_create_content" not in stext:
    stext = stext.replace(
        'patch(\n        "pecha_api.plans.series.series_service.validate_cms_author_details"',
        'patch("pecha_api.plans.series.series_service.require_can_create_content"), patch(\n        "pecha_api.plans.series.series_service.validate_cms_author_details"',
    )
series_service.write_text(stext, encoding="utf-8")
print("updated", series_service)

# dashboard
dash = ROOT / "tests/plans/dashboard/test_dashboard_service.py"
dtext = dash.read_text(encoding="utf-8")
dtext = dtext.replace(
    "from pecha_api.plans.plans_enums import PlanStatus",
    "from pecha_api.plans.plans_enums import PlanStatus\nfrom pecha_api.plans.platform_enums import PlatformRole",
)
dtext = dtext.replace(
    "def _make_mock_author(*, author_id=None, is_admin=False):\n    author = MagicMock()\n    author.id = author_id or uuid.uuid4()\n    author.is_admin = is_admin\n    return author",
    "def _make_mock_author(*, author_id=None, is_admin=False):\n    author = MagicMock()\n    author.id = author_id or uuid.uuid4()\n    author.platform_role = PlatformRole.SUPER_ADMIN if is_admin else PlatformRole.CREATOR\n    author.is_active = True\n    return author",
)
dash.write_text(dtext, encoding="utf-8")
print("updated", dash)

# author details test
author_test = ROOT / "tests/plans/authors/test_plan_author_service.py"
atext = author_test.read_text(encoding="utf-8")
if "build_author_access_context" not in atext.split("test_get_author_details_success")[1].split("def ")[0]:
    atext = atext.replace(
        "    @patch('pecha_api.plans.authors.plan_authors_service.validate_and_extract_author_details')\n    @pytest.mark.asyncio\n    async def test_get_author_details_success(",
        "    @patch('pecha_api.plans.authors.plan_authors_service.build_author_access_context', return_value={\n        'platform_role': PlatformRole.CREATOR,\n        'is_verified': True,\n        'is_active': True,\n        'has_group': True,\n        'can_create_content': True,\n    })\n    @patch('pecha_api.plans.authors.plan_authors_service.validate_and_extract_author_details')\n    @pytest.mark.asyncio\n    async def test_get_author_details_success(",
    )
if "from pecha_api.plans.platform_enums import PlatformRole" not in atext:
    atext = atext.replace(
        "from pecha_api.plans.authors.plan_authors_service import",
        "from pecha_api.plans.platform_enums import PlatformRole\nfrom pecha_api.plans.authors.plan_authors_service import",
    )
author_test.write_text(atext, encoding="utf-8")
print("updated", author_test)
