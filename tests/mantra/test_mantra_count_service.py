from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.mantra.mantra_count_service import (
    _build_count_fields,
    _resolve_mantra_title,
    _resolve_mala_image_fields,
    get_user_mantra_count_detail_service,
    get_user_mantra_counts_service,
)
from pecha_api.plans.plans_enums import LanguageCode


class TestDataFactory:
    @staticmethod
    def create_user(user_id=None):
        user = MagicMock()
        user.id = user_id or uuid4()
        return user

    @staticmethod
    def create_mantra(mantra_id=None, title="Medicine Buddha Mantra", metadata_entries=None, mala=None):
        mantra = MagicMock()
        mantra.id = mantra_id or uuid4()
        if metadata_entries is None:
            metadata = MagicMock()
            metadata.title = title
            metadata.language = LanguageCode.EN
            metadata_entries = [metadata]
        mantra.metadata_entries = metadata_entries
        mantra.mala = mala
        return mantra

    @staticmethod
    def create_count_row(mantra_id=None, total_count=500, updated_at=None):
        row = MagicMock()
        row.mantra_id = mantra_id or uuid4()
        row.total_count = total_count
        row.updated_at = updated_at or datetime.now(timezone.utc)
        return row


class TestHelpers:
    def test_build_count_fields(self):
        assert _build_count_fields(500) == {
            "private_count": 500,
            "allocated_count": 0,
            "total_count": 500,
        }

    def test_resolve_mantra_title_returns_none_when_mantra_missing(self):
        assert _resolve_mantra_title(None, "en") is None

    def test_resolve_mantra_title_returns_none_when_metadata_missing(self):
        mantra = TestDataFactory.create_mantra(metadata_entries=[])
        assert _resolve_mantra_title(mantra, "bo") is None

    def test_resolve_mantra_title_returns_title_for_matching_language(self):
        bo_metadata = MagicMock()
        bo_metadata.title = "སྨན་བླའི་སྔགས"
        bo_metadata.language = LanguageCode.BO
        en_metadata = MagicMock()
        en_metadata.title = "Medicine Buddha Mantra"
        en_metadata.language = LanguageCode.EN
        mantra = TestDataFactory.create_mantra(metadata_entries=[bo_metadata, en_metadata])

        assert _resolve_mantra_title(mantra, "bo") == "སྨན་བླའི་སྔགས"

    def test_resolve_mala_image_fields_returns_none_when_mantra_missing(self):
        assert _resolve_mala_image_fields(None) == (None, None)

    def test_resolve_mala_image_fields_returns_none_when_mala_missing(self):
        mantra = TestDataFactory.create_mantra(mala=None)
        assert _resolve_mala_image_fields(mantra) == (None, None)

    @patch("pecha_api.mantra.mantra_count_service.generate_mala_image_presigned_url")
    def test_resolve_mala_image_fields_returns_id_and_url(self, mock_presign):
        mala_id = uuid4()
        mala = MagicMock()
        mala.id = mala_id
        mala.url = "mala-images/default.png"
        mantra = TestDataFactory.create_mantra(mala=mala)
        mock_presign.return_value = "https://signed-url"

        assert _resolve_mala_image_fields(mantra) == (mala_id, "https://signed-url")
        mock_presign.assert_called_once_with("mala-images/default.png")


class TestGetUserMantraCountsService:
    @patch("pecha_api.mantra.mantra_count_service.get_mantras_by_ids")
    @patch("pecha_api.mantra.mantra_count_service.get_user_mantra_counts")
    @patch("pecha_api.mantra.mantra_count_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_count_service.validate_and_extract_user_details")
    @patch("pecha_api.mantra.mantra_count_service.generate_mala_image_presigned_url")
    def test_get_user_mantra_counts_success(
        self,
        mock_presign,
        mock_validate_user,
        mock_session_local,
        mock_get_counts,
        mock_get_mantras,
    ):
        user = TestDataFactory.create_user()
        mala_id = uuid4()
        mala = MagicMock()
        mala.id = mala_id
        mala.url = "mala-images/default.png"
        mantra = TestDataFactory.create_mantra(mala=mala)
        row = TestDataFactory.create_count_row(mantra_id=mantra.id, total_count=500)

        mock_validate_user.return_value = user
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        mock_get_counts.return_value = ([row], 500)
        mock_get_mantras.return_value = {mantra.id: mantra}
        mock_presign.return_value = "https://signed-url"

        result = get_user_mantra_counts_service(token="valid_token", language="en")

        assert result.total == 500
        assert len(result.counts) == 1
        assert result.counts[0].mantra_id == mantra.id
        assert result.counts[0].mantra_title == "Medicine Buddha Mantra"
        assert result.counts[0].mala_image_id == mala_id
        assert result.counts[0].mala_image_url == "https://signed-url"
        assert result.counts[0].private_count == 500
        assert result.counts[0].allocated_count == 0
        assert result.counts[0].total_count == 500
        mock_get_counts.assert_called_once_with(
            db=mock_db,
            user_id=user.id,
            skip=0,
            limit=20,
        )

    @patch("pecha_api.mantra.mantra_count_service.get_user_mantra_counts")
    @patch("pecha_api.mantra.mantra_count_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_count_service.validate_and_extract_user_details")
    def test_get_user_mantra_counts_empty(
        self,
        mock_validate_user,
        mock_session_local,
        mock_get_counts,
    ):
        user = TestDataFactory.create_user()
        mock_validate_user.return_value = user
        mock_session_local.return_value.__enter__.return_value = MagicMock()
        mock_get_counts.return_value = ([], 0)

        result = get_user_mantra_counts_service(token="valid_token")

        assert result.total == 0
        assert result.counts == []

    @patch("pecha_api.mantra.mantra_count_service.get_mantras_by_ids")
    @patch("pecha_api.mantra.mantra_count_service.get_user_mantra_counts")
    @patch("pecha_api.mantra.mantra_count_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_count_service.validate_and_extract_user_details")
    def test_get_user_mantra_counts_missing_mantra_title(
        self,
        mock_validate_user,
        mock_session_local,
        mock_get_counts,
        mock_get_mantras,
    ):
        user = TestDataFactory.create_user()
        row = TestDataFactory.create_count_row(total_count=108)

        mock_validate_user.return_value = user
        mock_session_local.return_value.__enter__.return_value = MagicMock()
        mock_get_counts.return_value = ([row], 1)
        mock_get_mantras.return_value = {}

        result = get_user_mantra_counts_service(token="valid_token", skip=5, limit=10)

        assert result.counts[0].mantra_title is None
        assert result.skip == 5
        assert result.limit == 10

    @patch("pecha_api.mantra.mantra_count_service.get_mantras_by_ids")
    @patch("pecha_api.mantra.mantra_count_service.get_user_mantra_counts")
    @patch("pecha_api.mantra.mantra_count_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_count_service.validate_and_extract_user_details")
    def test_get_user_mantra_counts_no_metadata_for_language(
        self,
        mock_validate_user,
        mock_session_local,
        mock_get_counts,
        mock_get_mantras,
    ):
        user = TestDataFactory.create_user()
        mantra = TestDataFactory.create_mantra(metadata_entries=[])
        row = TestDataFactory.create_count_row(mantra_id=mantra.id, total_count=54)

        mock_validate_user.return_value = user
        mock_session_local.return_value.__enter__.return_value = MagicMock()
        mock_get_counts.return_value = ([row], 1)
        mock_get_mantras.return_value = {mantra.id: mantra}

        result = get_user_mantra_counts_service(token="valid_token", language="bo")

        assert result.counts[0].mantra_title is None
        assert result.counts[0].total_count == 54


class TestGetUserMantraCountDetailService:
    @patch("pecha_api.mantra.mantra_count_service.get_user_mantra_count_for_mantra")
    @patch("pecha_api.mantra.mantra_count_service.get_mantra_by_id")
    @patch("pecha_api.mantra.mantra_count_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_count_service.validate_and_extract_user_details")
    def test_get_user_mantra_count_detail_success(
        self,
        mock_validate_user,
        mock_session_local,
        mock_get_mantra_by_id,
        mock_get_count_for_mantra,
    ):
        user = TestDataFactory.create_user()
        mantra = TestDataFactory.create_mantra()
        updated_at = datetime.now(timezone.utc)

        mock_validate_user.return_value = user
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        mock_get_mantra_by_id.return_value = mantra
        mock_get_count_for_mantra.return_value = (500, updated_at)

        result = get_user_mantra_count_detail_service(
            token="valid_token",
            mantra_id=mantra.id,
            language="en",
        )

        assert result.mantra_id == mantra.id
        assert result.mantra_title == "Medicine Buddha Mantra"
        assert result.private_count == 500
        assert result.allocated_count == 0
        assert result.total_count == 500
        assert result.allocations == []
        assert result.updated_at == updated_at

    @patch("pecha_api.mantra.mantra_count_service.get_user_mantra_count_for_mantra")
    @patch("pecha_api.mantra.mantra_count_service.get_mantra_by_id")
    @patch("pecha_api.mantra.mantra_count_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_count_service.validate_and_extract_user_details")
    def test_get_user_mantra_count_detail_returns_zero_when_no_accumulators(
        self,
        mock_validate_user,
        mock_session_local,
        mock_get_mantra_by_id,
        mock_get_count_for_mantra,
    ):
        user = TestDataFactory.create_user()
        mantra = TestDataFactory.create_mantra()

        mock_validate_user.return_value = user
        mock_session_local.return_value.__enter__.return_value = MagicMock()
        mock_get_mantra_by_id.return_value = mantra
        mock_get_count_for_mantra.return_value = (0, None)

        result = get_user_mantra_count_detail_service(
            token="valid_token",
            mantra_id=mantra.id,
        )

        assert result.total_count == 0
        assert result.private_count == 0
        assert result.allocations == []
        assert result.updated_at is None

    @patch("pecha_api.mantra.mantra_count_service.get_mantra_by_id")
    @patch("pecha_api.mantra.mantra_count_service.SessionLocal")
    @patch("pecha_api.mantra.mantra_count_service.validate_and_extract_user_details")
    def test_get_user_mantra_count_detail_not_found(
        self,
        mock_validate_user,
        mock_session_local,
        mock_get_mantra_by_id,
    ):
        user = TestDataFactory.create_user()
        mantra_id = uuid4()

        mock_validate_user.return_value = user
        mock_session_local.return_value.__enter__.return_value = MagicMock()
        mock_get_mantra_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_user_mantra_count_detail_service(
                token="valid_token",
                mantra_id=mantra_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
