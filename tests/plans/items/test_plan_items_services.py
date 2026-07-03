from pecha_api.plans.platform_enums import PlatformRole
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, call
from fastapi import HTTPException

from pecha_api.plans.items.plan_items_services import create_plan_item, delete_plan_days, update_plans_day_number
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.items.plan_items_response_models import (
    ItemDTO,
    ReorderDaysRequest,
    ItemDayNumberDTO,
    CreateDaysRequest,
    DeleteDaysRequest,
)


def _mock_session_local(mock_session_local):
    mock_db_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db_session
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db_session


def test_create_plan_item_success():
    plan_id = uuid.uuid4()
    saved_item_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_get_last_day_number, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save_plan_items:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_last_day_number.return_value = 3

        saved_item = MagicMock()
        saved_item.id = saved_item_id
        saved_item.plan_id = plan_id
        saved_item.day_number = 4
        mock_save_plan_items.return_value = [saved_item]

        resp = create_plan_item(
            token="dummy-token",
            plan_id=plan_id,
            create_days_request=CreateDaysRequest(number_of_days=1),
        )

        assert mock_validate_author.call_count == 1
        mock_get_plan_by_id.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_get_last_day_number.assert_called_once_with(db=db_session, plan_id=plan_id)

        mock_save_plan_items.assert_called_once()
        called_kwargs = mock_save_plan_items.call_args.kwargs
        assert called_kwargs["db"] is db_session
        created_items = called_kwargs["plan_items"]
        assert len(created_items) == 1
        assert isinstance(created_items[0], PlanItem)
        assert created_items[0].plan_id == plan_id
        assert created_items[0].day_number == 4
        assert created_items[0].created_by == author.email

        assert isinstance(resp, list)
        assert len(resp) == 1
        assert isinstance(resp[0], ItemDTO)
        assert resp[0].id == saved_item_id
        assert resp[0].plan_id == plan_id
        assert resp[0].day_number == 4


def test_create_plan_item_propagates_repository_error():
    plan_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_get_last_day_number, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save_plan_items:
        _ = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_last_day_number.return_value = 0

        error = HTTPException(status_code=400, detail={"error": "Bad request", "message": "duplicate"})
        mock_save_plan_items.side_effect = error

        with pytest.raises(HTTPException) as exc_info:
            create_plan_item(
                token="dummy-token",
                plan_id=plan_id,
                create_days_request=CreateDaysRequest(number_of_days=1),
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == {"error": "Bad request", "message": "duplicate"}


def _mock_series_plan(plan_id, author, start_date, display_order=1):
    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = uuid.uuid4()
    plan.display_order = display_order
    plan.start_date = start_date
    plan.author_id = author.id
    return plan


def test_create_plan_item_rejects_days_overlapping_next_series_plan():
    plan_id = uuid.uuid4()

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR

    # Plan starts Jun 14 and already has 25 days (last day Jul 8); next plan starts Jul 10
    plan = _mock_series_plan(plan_id, author, start_date=datetime(2026, 6, 14, tzinfo=timezone.utc))

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_get_last_day_number, \
         patch("pecha_api.plans.items.plan_items_services.get_next_series_plan_start_date") as mock_next_start, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save_plan_items:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_last_day_number.return_value = 25
        mock_next_start.return_value = datetime(2026, 7, 10, tzinfo=timezone.utc)

        with pytest.raises(HTTPException) as exc_info:
            create_plan_item(
                token="dummy-token",
                plan_id=plan_id,
                create_days_request=CreateDaysRequest(number_of_days=2),
            )

        assert exc_info.value.status_code == 400
        assert "2026-07-10" in exc_info.value.detail["message"]
        assert "1 more day(s)" in exc_info.value.detail["message"]
        mock_next_start.assert_called_once_with(
            db=db_session,
            series_id=plan.series_id,
            display_order=plan.display_order,
        )
        mock_save_plan_items.assert_not_called()


def test_create_plan_item_allows_days_up_to_next_series_plan_start():
    plan_id = uuid.uuid4()

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR

    # Plan starts Jun 14 with 25 days; one more day (Jul 9) still ends before Jul 10
    plan = _mock_series_plan(plan_id, author, start_date=datetime(2026, 6, 14, tzinfo=timezone.utc))

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_get_last_day_number, \
         patch("pecha_api.plans.items.plan_items_services.get_next_series_plan_start_date") as mock_next_start, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save_plan_items:
        _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_last_day_number.return_value = 25
        mock_next_start.return_value = datetime(2026, 7, 10, tzinfo=timezone.utc)

        saved_item = MagicMock()
        saved_item.id = uuid.uuid4()
        saved_item.plan_id = plan_id
        saved_item.day_number = 26
        mock_save_plan_items.return_value = [saved_item]

        resp = create_plan_item(
            token="dummy-token",
            plan_id=plan_id,
            create_days_request=CreateDaysRequest(number_of_days=1),
        )

        assert len(resp) == 1
        assert resp[0].day_number == 26
        mock_save_plan_items.assert_called_once()


def test_create_plan_item_skips_series_check_when_no_next_plan():
    plan_id = uuid.uuid4()

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR

    plan = _mock_series_plan(plan_id, author, start_date=datetime(2026, 6, 14, tzinfo=timezone.utc))

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_get_last_day_number, \
         patch("pecha_api.plans.items.plan_items_services.get_next_series_plan_start_date") as mock_next_start, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save_plan_items:
        _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_last_day_number.return_value = 100
        mock_next_start.return_value = None

        saved_item = MagicMock()
        saved_item.id = uuid.uuid4()
        saved_item.plan_id = plan_id
        saved_item.day_number = 101
        mock_save_plan_items.return_value = [saved_item]

        resp = create_plan_item(
            token="dummy-token",
            plan_id=plan_id,
            create_days_request=CreateDaysRequest(number_of_days=1),
        )

        assert len(resp) == 1
        mock_save_plan_items.assert_called_once()


def test_delete_plan_days_success_reorders():
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None

    item_to_delete = MagicMock()
    item_to_delete.id = day_id

    remaining_items = [
        MagicMock(id=uuid.uuid4(), day_number=1),
        MagicMock(id=uuid.uuid4(), day_number=3),
        MagicMock(id=uuid.uuid4(), day_number=5),
    ]

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id_and_day_ids") as mock_get_days_by_ids, \
         patch("pecha_api.plans.items.plan_items_services.delete_days_by_ids") as mock_delete, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id") as mock_get_days, \
         patch("pecha_api.plans.items.plan_items_services.update_days_in_bulk_by_plan_id") as mock_bulk_update:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_days_by_ids.return_value = [item_to_delete]
        mock_get_days.return_value = remaining_items

        delete_plan_days(
            token="dummy-token",
            plan_id=plan_id,
            delete_days_request=DeleteDaysRequest(day_ids=[day_id]),
        )

        assert mock_validate_author.call_count == 1
        mock_get_plan_by_id.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_get_days_by_ids.assert_called_once_with(db=db_session, plan_id=plan_id, day_ids=[day_id])
        mock_delete.assert_called_once_with(
            db=db_session, plan_id=plan_id, day_ids=[day_id], commit=False,
        )
        db_session.commit.assert_called_once()

        assert mock_bulk_update.call_count == 2
        temp_call, final_call = mock_bulk_update.call_args_list
        assert temp_call.kwargs["commit"] is False
        assert [d.day_number for d in temp_call.kwargs["days"]] == [-2, -3]
        assert final_call.kwargs["commit"] is False
        assert [d.day_number for d in final_call.kwargs["days"]] == [2, 3]


def test_delete_plan_days_success_reorders_when_first_day_deleted():
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()

    item_to_delete = MagicMock()
    item_to_delete.id = day_id

    remaining_items = [
        MagicMock(id=uuid.uuid4(), day_number=2),
        MagicMock(id=uuid.uuid4(), day_number=3),
        MagicMock(id=uuid.uuid4(), day_number=4),
    ]

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id_and_day_ids") as mock_get_days_by_ids, \
         patch("pecha_api.plans.items.plan_items_services.delete_days_by_ids") as mock_delete, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id") as mock_get_days, \
         patch("pecha_api.plans.items.plan_items_services.update_days_in_bulk_by_plan_id") as mock_bulk_update:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_days_by_ids.return_value = [item_to_delete]
        mock_get_days.return_value = remaining_items

        delete_plan_days(
            token="dummy-token",
            plan_id=plan_id,
            delete_days_request=DeleteDaysRequest(day_ids=[day_id]),
        )

        assert mock_bulk_update.call_count == 2
        temp_call, final_call = mock_bulk_update.call_args_list
        assert [d.day_number for d in temp_call.kwargs["days"]] == [-1, -2, -3]
        assert [d.day_number for d in final_call.kwargs["days"]] == [1, 2, 3]


def test_delete_plan_days_not_found():
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id_and_day_ids") as mock_get_days_by_ids:
        _ = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_days_by_ids.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            delete_plan_days(
                token="dummy-token",
                plan_id=plan_id,
                delete_days_request=DeleteDaysRequest(day_ids=[day_id]),
            )

        assert exc_info.value.status_code == 404


def test_delete_plan_days_auth_error():
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    with patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author:
        mock_validate_author.side_effect = HTTPException(status_code=401, detail="Unauthorized")

        with pytest.raises(HTTPException) as exc_info:
            delete_plan_days(
                token="bad-token",
                plan_id=plan_id,
                delete_days_request=DeleteDaysRequest(day_ids=[day_id]),
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Unauthorized"


def test_delete_plan_days_repository_error():
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None

    item_to_delete = MagicMock()
    item_to_delete.id = day_id

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id_and_day_ids") as mock_get_days_by_ids, \
         patch("pecha_api.plans.items.plan_items_services.delete_days_by_ids") as mock_delete:
        _ = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_days_by_ids.return_value = [item_to_delete]
        mock_delete.side_effect = HTTPException(
            status_code=400, detail={"error": "Bad request", "message": "cannot delete"}
        )

        with pytest.raises(HTTPException) as exc_info:
            delete_plan_days(
                token="dummy-token",
                plan_id=plan_id,
                delete_days_request=DeleteDaysRequest(day_ids=[day_id]),
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == {"error": "Bad request", "message": "cannot delete"}


def test_delete_plan_days_unexpected_error_rolls_back_and_wraps():
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()

    item_to_delete = MagicMock()
    item_to_delete.id = day_id

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id_and_day_ids") as mock_get_days_by_ids, \
         patch("pecha_api.plans.items.plan_items_services.delete_days_by_ids") as mock_delete:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_days_by_ids.return_value = [item_to_delete]
        mock_delete.side_effect = Exception("unexpected db failure")

        with pytest.raises(HTTPException) as exc_info:
            delete_plan_days(
                token="dummy-token",
                plan_id=plan_id,
                delete_days_request=DeleteDaysRequest(day_ids=[day_id]),
            )

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["message"] == "unexpected db failure"
        db_session.rollback.assert_called_once()
        db_session.commit.assert_not_called()


def test_delete_plan_days_no_reorder_when_already_sequential():
    plan_id = uuid.uuid4()
    day_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()

    item_to_delete = MagicMock()
    item_to_delete.id = day_id

    # Remaining days are already numbered 1..3 sequentially -> no reorder needed.
    remaining_items = [
        MagicMock(id=uuid.uuid4(), day_number=1),
        MagicMock(id=uuid.uuid4(), day_number=2),
        MagicMock(id=uuid.uuid4(), day_number=3),
    ]

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id_and_day_ids") as mock_get_days_by_ids, \
         patch("pecha_api.plans.items.plan_items_services.delete_days_by_ids"), \
         patch("pecha_api.plans.items.plan_items_services.get_days_by_plan_id") as mock_get_days, \
         patch("pecha_api.plans.items.plan_items_services.update_days_in_bulk_by_plan_id") as mock_bulk_update:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan
        mock_get_days_by_ids.return_value = [item_to_delete]
        mock_get_days.return_value = remaining_items

        delete_plan_days(
            token="dummy-token",
            plan_id=plan_id,
            delete_days_request=DeleteDaysRequest(day_ids=[day_id]),
        )

        # No day_number changes required, so bulk update is never invoked.
        mock_bulk_update.assert_not_called()
        db_session.commit.assert_called_once()


def test_update_plans_day_number_success_calls_bulk_update():
    plan_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    payload = ReorderDaysRequest(
        days=[
            ItemDayNumberDTO(id=uuid.uuid4(), day_number=1),
            ItemDayNumberDTO(id=uuid.uuid4(), day_number=2),
            ItemDayNumberDTO(id=uuid.uuid4(), day_number=3),
        ]
    )

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id, \
         patch("pecha_api.plans.items.plan_items_services.update_days_in_bulk_by_plan_id") as mock_bulk_update:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan

        update_plans_day_number(token="dummy-token", plan_id=plan_id, reorder_days_request=payload)

        assert mock_validate_author.call_count == 1
        mock_get_plan_by_id.assert_called_once_with(db=db_session, plan_id=plan_id)
        mock_bulk_update.assert_called_once()
        called_kwargs = mock_bulk_update.call_args.kwargs
        assert called_kwargs["db"] is db_session
        assert called_kwargs["days"] == payload.days


def test_create_plan_item_with_source_day_copies_tasks():
    plan_id = uuid.uuid4()
    source_day_id = uuid.uuid4()
    saved_item_id = uuid.uuid4()

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None

    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    plan.author_id = author.id

    source_day = MagicMock()

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_last_day, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_day_by_id_any_plan") as mock_get_source, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_source_plan, \
         patch("pecha_api.plans.items.plan_items_services._copy_tasks_and_subtasks_to_days") as mock_copy:
        db_session = _mock_session_local(mock_session_local)

        mock_validate_author.return_value = author
        mock_get_plan.return_value = plan
        mock_last_day.return_value = 0

        saved_item = MagicMock()
        saved_item.id = saved_item_id
        saved_item.plan_id = plan_id
        saved_item.day_number = 1
        mock_save.return_value = [saved_item]
        
        # Source day from same plan
        source_day.plan_id = plan_id
        mock_get_source.return_value = source_day
        mock_get_source_plan.return_value = plan

        create_plan_item(
            token="dummy-token",
            plan_id=plan_id,
            create_days_request=CreateDaysRequest(number_of_days=1, source_day_id=source_day_id),
        )

        mock_get_source.assert_called_once_with(db=db_session, day_id=source_day_id)
        mock_get_source_plan.assert_called_with(db=db_session, plan_id=plan_id)
        mock_copy.assert_called_once_with(
            db=db_session,
            source_day=source_day,
            target_days=[saved_item],
            created_by=author.email,
        )


def test_delete_plan_days_empty_day_ids_returns_early():
    with patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author:
        delete_plan_days(
            token="dummy-token",
            plan_id=uuid.uuid4(),
            delete_days_request=DeleteDaysRequest(day_ids=[]),
        )
        mock_validate_author.assert_not_called()


def test_get_author_plan_raises_404_when_not_admin_and_plan_missing():
    from pecha_api.plans.items.plan_items_services import _get_author_plan

    author = MagicMock()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR

    db = MagicMock()

    with patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan:
        mock_get_plan.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            _get_author_plan(db=db, plan_id=uuid.uuid4(), current_author=author)

        assert exc_info.value.status_code == 404


def test_copy_tasks_and_subtasks_no_tasks_returns_early():
    from pecha_api.plans.items.plan_items_services import _copy_tasks_and_subtasks_to_days

    source_day = MagicMock()
    source_day.tasks = []
    db = MagicMock()

    _copy_tasks_and_subtasks_to_days(
        db=db,
        source_day=source_day,
        target_days=[MagicMock()],
        created_by="author@example.com",
    )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_copy_tasks_and_subtasks_copies_correctly():
    from pecha_api.plans.items.plan_items_services import _copy_tasks_and_subtasks_to_days

    sub_task = MagicMock()
    sub_task.content_type = "text"
    sub_task.content = "content"
    sub_task.duration = 10
    sub_task.source_text_id = None
    sub_task.pecha_segment_id = None
    sub_task.segment_ids = []
    sub_task.display_order = 1
    sub_task.timestamp = None

    source_task = MagicMock()
    source_task.title = "Task 1"
    source_task.display_order = 1
    source_task.estimated_time = 5
    source_task.is_required = True
    source_task.sub_tasks = [sub_task]

    source_day = MagicMock()
    source_day.tasks = [source_task]

    target_day = MagicMock()
    target_day.id = uuid.uuid4()

    db = MagicMock()

    _copy_tasks_and_subtasks_to_days(
        db=db,
        source_day=source_day,
        target_days=[target_day],
        created_by="author@example.com",
    )

    assert db.add.call_count == 2
    assert db.flush.call_count == 2
    db.commit.assert_called_once()


def test_copy_tasks_and_subtasks_with_timestamp():
    from pecha_api.plans.items.plan_items_services import _copy_tasks_and_subtasks_to_days

    timestamp = MagicMock()
    timestamp.start_ms = 0
    timestamp.end_ms = 5000

    sub_task = MagicMock()
    sub_task.content_type = "audio"
    sub_task.content = None
    sub_task.duration = 5
    sub_task.source_text_id = None
    sub_task.pecha_segment_id = None
    sub_task.segment_ids = []
    sub_task.display_order = 1
    sub_task.timestamp = timestamp

    source_task = MagicMock()
    source_task.title = "Task"
    source_task.display_order = 1
    source_task.estimated_time = 5
    source_task.is_required = True
    source_task.sub_tasks = [sub_task]

    source_day = MagicMock()
    source_day.tasks = [source_task]

    target_day = MagicMock()
    target_day.id = uuid.uuid4()

    db = MagicMock()

    _copy_tasks_and_subtasks_to_days(
        db=db,
        source_day=source_day,
        target_days=[target_day],
        created_by="author@example.com",
    )

    assert db.add.call_count == 3
    db.commit.assert_called_once()


def test_copy_tasks_and_subtasks_db_error_raises_400():
    from pecha_api.plans.items.plan_items_services import _copy_tasks_and_subtasks_to_days

    source_task = MagicMock()
    source_task.title = "Task"
    source_task.display_order = 1
    source_task.estimated_time = 5
    source_task.is_required = True
    source_task.sub_tasks = []

    source_day = MagicMock()
    source_day.tasks = [source_task]

    target_day = MagicMock()
    target_day.id = uuid.uuid4()

    db = MagicMock()
    db.flush.side_effect = Exception("db error")

    with pytest.raises(HTTPException) as exc_info:
        _copy_tasks_and_subtasks_to_days(
            db=db,
            source_day=source_day,
            target_days=[target_day],
            created_by="author@example.com",
        )

    assert exc_info.value.status_code == 400
    db.rollback.assert_called_once()


def test_update_plans_day_number_duplicate_payload_raises_400():
    plan_id = uuid.uuid4()

    payload = ReorderDaysRequest(
        days=[
            ItemDayNumberDTO(id=uuid.uuid4(), day_number=1),
            ItemDayNumberDTO(id=uuid.uuid4(), day_number=1),
        ]
    )

    plan = MagicMock()
    plan.id = plan_id
    plan.deleted_at = None
    plan.group_id = uuid.uuid4()
    plan.series_id = None
    author_id = uuid.uuid4()
    plan.author_id = author_id

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan_by_id:
        _ = _mock_session_local(mock_session_local)

        author = MagicMock(email="author@example.com", id=author_id)
        mock_validate_author.return_value = author
        mock_get_plan_by_id.return_value = plan

        with pytest.raises(HTTPException) as exc_info:
            update_plans_day_number(token="dummy-token", plan_id=plan_id, reorder_days_request=payload)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == {"error": "Bad request", "message": "Duplicate day numbers"}


def test_create_plan_item_cross_plan_copy_success():
    """Test copying tasks from a different plan that the author owns"""
    target_plan_id = uuid.uuid4()
    source_plan_id = uuid.uuid4()
    source_day_id = uuid.uuid4()
    
    target_plan = MagicMock()
    target_plan.id = target_plan_id
    target_plan.deleted_at = None
    target_plan.group_id = uuid.uuid4()
    target_plan.series_id = None
    
    source_plan = MagicMock()
    source_plan.id = source_plan_id
    source_plan.deleted_at = None
    source_plan.group_id = target_plan.group_id
    
    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    
    target_plan.author_id = author.id
    source_plan.author_id = author.id  # Same author owns both plans
    
    source_day = MagicMock()
    source_day.plan_id = source_plan_id
    
    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_last_day, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_day_by_id_any_plan") as mock_get_source, \
         patch("pecha_api.plans.items.plan_items_services._copy_tasks_and_subtasks_to_days") as mock_copy:
        
        db_session = _mock_session_local(mock_session_local)
        
        mock_validate_author.return_value = author
        mock_get_plan.side_effect = lambda db, plan_id: target_plan if plan_id == target_plan_id else source_plan
        mock_last_day.return_value = 0
        
        saved_item = MagicMock()
        saved_item.id = uuid.uuid4()
        saved_item.plan_id = target_plan_id
        saved_item.day_number = 1
        mock_save.return_value = [saved_item]
        mock_get_source.return_value = source_day
        
        create_plan_item(
            token="dummy-token",
            plan_id=target_plan_id,
            create_days_request=CreateDaysRequest(number_of_days=1, source_day_id=source_day_id),
        )
        
        mock_get_source.assert_called_once_with(db=db_session, day_id=source_day_id)
        # Should check both target plan and source plan
        assert mock_get_plan.call_count == 2
        mock_copy.assert_called_once_with(
            db=db_session,
            source_day=source_day,
            target_days=[saved_item],
            created_by=author.email,
        )


def test_create_plan_item_cross_plan_copy_forbidden():
    """Test copying from a plan the author doesn't own"""
    target_plan_id = uuid.uuid4()
    source_plan_id = uuid.uuid4()
    source_day_id = uuid.uuid4()
    
    target_plan = MagicMock()
    target_plan.id = target_plan_id
    target_plan.deleted_at = None
    target_plan.group_id = uuid.uuid4()
    target_plan.series_id = None
    
    source_plan = MagicMock()
    source_plan.id = source_plan_id
    source_plan.deleted_at = None
    source_plan.group_id = target_plan.group_id
    
    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = "author@example.com"
    author.platform_role = PlatformRole.CREATOR
    
    other_author_id = uuid.uuid4()
    target_plan.author_id = author.id
    source_plan.author_id = other_author_id
    source_plan.group_id = uuid.uuid4()  # different group than target
    
    source_day = MagicMock()
    source_day.plan_id = source_plan_id
    
    forbidden = HTTPException(status_code=403, detail={"error": "Forbidden", "message": "Forbidden"})

    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.require_can_read_group_content", side_effect=forbidden), \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_last_day, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_day_by_id_any_plan") as mock_get_source:
        
        db_session = _mock_session_local(mock_session_local)
        
        mock_validate_author.return_value = author
        mock_get_plan.side_effect = lambda db, plan_id: target_plan if plan_id == target_plan_id else source_plan
        mock_last_day.return_value = 0
        
        saved_item = MagicMock()
        saved_item.id = uuid.uuid4()
        saved_item.plan_id = target_plan_id
        saved_item.day_number = 1
        mock_save.return_value = [saved_item]
        mock_get_source.return_value = source_day
        
        with pytest.raises(HTTPException) as exc_info:
            create_plan_item(
                token="dummy-token",
                plan_id=target_plan_id,
                create_days_request=CreateDaysRequest(number_of_days=1, source_day_id=source_day_id),
            )
        
        assert exc_info.value.status_code == 403


def test_create_plan_item_cross_plan_copy_admin_success():
    """Test admin can copy from any plan"""
    target_plan_id = uuid.uuid4()
    source_plan_id = uuid.uuid4()
    source_day_id = uuid.uuid4()
    
    target_plan = MagicMock()
    target_plan.id = target_plan_id
    target_plan.deleted_at = None
    target_plan.group_id = uuid.uuid4()
    target_plan.series_id = None
    
    source_plan = MagicMock()
    source_plan.id = source_plan_id
    source_plan.deleted_at = None
    source_plan.group_id = uuid.uuid4()
    
    admin = MagicMock()
    admin.id = uuid.uuid4()
    admin.email = "admin@example.com"
    admin.platform_role = PlatformRole.SUPER_ADMIN
    admin.is_active = True
    
    other_author_id = uuid.uuid4()
    target_plan.author_id = admin.id
    source_plan.author_id = other_author_id  # Different author owns source plan
    
    source_day = MagicMock()
    source_day.plan_id = source_plan_id
    
    with patch("pecha_api.plans.items.plan_items_services.SessionLocal") as mock_session_local, \
         patch("pecha_api.plans.items.plan_items_services.validate_cms_author_details") as mock_validate_author, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_by_id") as mock_get_plan, \
         patch("pecha_api.plans.items.plan_items_services.get_last_day_number") as mock_last_day, \
         patch("pecha_api.plans.items.plan_items_services.save_plan_items") as mock_save, \
         patch("pecha_api.plans.items.plan_items_services.get_plan_day_by_id_any_plan") as mock_get_source, \
         patch("pecha_api.plans.items.plan_items_services._copy_tasks_and_subtasks_to_days") as mock_copy:
        
        db_session = _mock_session_local(mock_session_local)
        
        mock_validate_author.return_value = admin
        mock_get_plan.side_effect = lambda db, plan_id: target_plan if plan_id == target_plan_id else source_plan
        mock_last_day.return_value = 0
        
        saved_item = MagicMock()
        saved_item.id = uuid.uuid4()
        saved_item.plan_id = target_plan_id
        saved_item.day_number = 1
        mock_save.return_value = [saved_item]
        mock_get_source.return_value = source_day
        
        create_plan_item(
            token="admin-token",
            plan_id=target_plan_id,
            create_days_request=CreateDaysRequest(number_of_days=1, source_day_id=source_day_id),
        )
        
        # Admin can access any plan, so no 403 error
        mock_copy.assert_called_once_with(
            db=db_session,
            source_day=source_day,
            target_days=[saved_item],
            created_by=admin.email,
        )
