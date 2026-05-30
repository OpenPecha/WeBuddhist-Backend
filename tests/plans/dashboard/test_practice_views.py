import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from starlette import status

from pecha_api.plans.dashboard.dashboard_response_models import (
    DashboardItemDTO,
    DashboardItemsResponse,
    DashboardPaginationDTO,
)
from pecha_api.plans.dashboard.dashboard_views import list_practice_items
from pecha_api.plans.plans_enums import PlanStatus


@pytest.mark.asyncio
async def test_list_practice_items_success():
    item_id = uuid.uuid4()
    expected = DashboardItemsResponse(
        items=[
            DashboardItemDTO(
                id=item_id,
                type="plan",
                title="Morning Practice",
                image_url="https://example.com/image.jpg",
                image_key="plan/cover.jpg",
                status=PlanStatus.PUBLISHED,
                featured=True,
                languages=["EN"],
                enrolled_count=5,
                updated_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
            )
        ],
        pagination=DashboardPaginationDTO(
            page=1,
            page_size=20,
            total=1,
            total_pages=1,
        ),
    )

    with patch(
        "pecha_api.plans.dashboard.dashboard_views.get_practice_items_list",
        return_value=expected,
    ) as mock_service:
        response = await list_practice_items(
            tab="all",
            page=1,
            page_size=20,
            search="morning",
            language="en",
            featured=True,
        )

        mock_service.assert_called_once_with(
            tab="all",
            page=1,
            page_size=20,
            search="morning",
            language="en",
            featured=True,
        )
        assert response == expected
        assert response.items[0].type == "plan"
        assert response.pagination.total == 1


@pytest.mark.asyncio
async def test_list_practice_items_nulls_author_id():
    from datetime import datetime, timezone

    from pecha_api.plans.dashboard.dashboard_service import _row_to_public_dto

    class _Row:
        item_type = "series"
        id = uuid.uuid4()
        image_key = None
        status = PlanStatus.PUBLISHED
        featured = True
        languages_raw = "EN"
        enrolled_count = 0
        plans_count = 2
        updated_at = datetime.now(timezone.utc)
        created_at = datetime.now(timezone.utc)
        metadata_json = None
        author_id = uuid.uuid4()

    dto = _row_to_public_dto(_Row())
    assert dto.type == "series"
    assert dto.author_id is None
