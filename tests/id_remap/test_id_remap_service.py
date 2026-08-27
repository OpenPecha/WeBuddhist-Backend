from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.id_remap.id_remap_service import remap_segment_id, remap_text_id
from pecha_api.plans.platform_enums import PlatformRole


def _make_author(platform_role=PlatformRole.SUPER_ADMIN):
    author = MagicMock()
    author.platform_role = platform_role.value
    author.is_active = True
    return author


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


MODULE = "pecha_api.id_remap.id_remap_service"


class TestRemapSegmentId:
    @pytest.mark.asyncio
    async def test_success_returns_postgres_counts_only(self):
        caller = _make_author()
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller), \
                patch(f"{MODULE}.SessionLocal") as mock_session_local, \
                patch(f"{MODULE}.remap_segment_ids_postgres", return_value=({"sub_tasks.pecha_segment_id": 2}, [])) as mock_pg:
            mock_db = _session_local_context(mock_session_local)

            result = await remap_segment_id(token="token", old_segment_id="old-seg", new_segment_id="new-seg")

        mock_pg.assert_called_once_with(db=mock_db, old_segment_id="old-seg", new_segment_id="new-seg")
        mock_db.commit.assert_called_once()
        assert result.old_id == "old-seg"
        assert result.new_id == "new-seg"
        assert result.updated_counts == {"sub_tasks.pecha_segment_id": 2}
        assert result.skipped == []

    @pytest.mark.asyncio
    async def test_allows_new_segment_id_not_present_in_mongo(self):
        """new_segment_id is never checked against Mongo; the endpoint is Postgres-only."""
        caller = _make_author()
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller), \
                patch(f"{MODULE}.SessionLocal") as mock_session_local, \
                patch(f"{MODULE}.remap_segment_ids_postgres", return_value=({}, [])):
            _session_local_context(mock_session_local)

            result = await remap_segment_id(
                token="token",
                old_segment_id="old-seg",
                new_segment_id="brand-new-id-not-in-mongo",
            )

        assert result.new_id == "brand-new-id-not-in-mongo"

    @pytest.mark.asyncio
    async def test_rejects_when_ids_are_equal(self):
        caller = _make_author()
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller):
            with pytest.raises(HTTPException) as exc_info:
                await remap_segment_id(token="token", old_segment_id="same-id", new_segment_id="same-id")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_forbidden_for_non_super_admin(self):
        caller = _make_author(platform_role=PlatformRole.CREATOR)
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller):
            with pytest.raises(HTTPException) as exc_info:
                await remap_segment_id(token="token", old_segment_id="old-seg", new_segment_id="new-seg")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_postgres_failure_rolls_back_and_raises_500(self):
        caller = _make_author()
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller), \
                patch(f"{MODULE}.SessionLocal") as mock_session_local, \
                patch(f"{MODULE}.remap_segment_ids_postgres", side_effect=RuntimeError("boom")):
            mock_db = _session_local_context(mock_session_local)

            with pytest.raises(HTTPException) as exc_info:
                await remap_segment_id(token="token", old_segment_id="old-seg", new_segment_id="new-seg")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestRemapTextId:
    @pytest.mark.asyncio
    async def test_success_returns_postgres_counts_only(self):
        caller = _make_author()
        old_id = "11111111-1111-1111-1111-111111111111"
        new_id = "22222222-2222-2222-2222-222222222222"
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller), \
                patch(f"{MODULE}.SessionLocal") as mock_session_local, \
                patch(f"{MODULE}.remap_text_ids_postgres", return_value=({"accumulators.text_id": 3}, [])) as mock_pg:
            mock_db = _session_local_context(mock_session_local)

            result = await remap_text_id(token="token", old_text_id=old_id, new_text_id=new_id)

        mock_pg.assert_called_once_with(db=mock_db, old_text_id=old_id, new_text_id=new_id)
        mock_db.commit.assert_called_once()
        assert result.updated_counts == {"accumulators.text_id": 3}

    @pytest.mark.asyncio
    async def test_allows_new_text_id_not_present_in_mongo(self):
        """new_text_id is never checked against Mongo, and no format is enforced."""
        caller = _make_author()
        old_id = "11111111-1111-1111-1111-111111111111"
        new_id = "33333333-3333-3333-3333-333333333333"
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller), \
                patch(f"{MODULE}.SessionLocal") as mock_session_local, \
                patch(f"{MODULE}.remap_text_ids_postgres", return_value=({}, [])):
            _session_local_context(mock_session_local)

            result = await remap_text_id(token="token", old_text_id=old_id, new_text_id=new_id)

        assert result.new_id == new_id

    @pytest.mark.asyncio
    async def test_allows_non_uuid_text_ids(self):
        """text_id-holding columns are plain strings now, so non-UUID ids are accepted."""
        caller = _make_author()
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller), \
                patch(f"{MODULE}.SessionLocal") as mock_session_local, \
                patch(f"{MODULE}.remap_text_ids_postgres", return_value=({}, [])) as mock_pg:
            mock_db = _session_local_context(mock_session_local)

            result = await remap_text_id(token="token", old_text_id="not-a-uuid", new_text_id="also-not-a-uuid")

        mock_pg.assert_called_once_with(db=mock_db, old_text_id="not-a-uuid", new_text_id="also-not-a-uuid")
        assert result.new_id == "also-not-a-uuid"

    @pytest.mark.asyncio
    async def test_reports_skipped_conflicts_from_postgres(self):
        caller = _make_author()
        old_id = "11111111-1111-1111-1111-111111111111"
        new_id = "22222222-2222-2222-2222-222222222222"
        skipped = [{"table": "user_recitations", "reason": "duplicate (user_id, text_id)", "detail": {"user_id": "abc"}}]
        with patch(f"{MODULE}.validate_and_extract_author_details", return_value=caller), \
                patch(f"{MODULE}.SessionLocal") as mock_session_local, \
                patch(f"{MODULE}.remap_text_ids_postgres", return_value=({}, skipped)):
            _session_local_context(mock_session_local)

            result = await remap_text_id(token="token", old_text_id=old_id, new_text_id=new_id)

        assert len(result.skipped) == 1
        assert result.skipped[0].table == "user_recitations"
        assert result.skipped[0].detail == {"user_id": "abc"}
