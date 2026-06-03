from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo.errors import ConfigurationError

from pecha_api.db.mongo_database import lifespan


def _mongo_get_side_effect(key: str) -> str:
    return {
        "MONGO_CONNECTION_STRING": "mongodb://localhost:27017",
        "MONGO_DATABASE_NAME": "testdb",
    }[key]


@pytest.mark.asyncio
async def test_lifespan_closes_mongo_client_on_shutdown():
    api = MagicMock()

    with patch("pecha_api.db.mongo_database.AsyncIOMotorClient") as mock_client_cls, patch(
        "pecha_api.db.mongo_database.init_beanie",
        new_callable=AsyncMock,
    ), patch(
        "pecha_api.db.mongo_database.get",
        side_effect=_mongo_get_side_effect,
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        async with lifespan(api):
            assert api.mongodb is mock_db

    mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_skips_mongo_when_connection_string_empty():
    api = MagicMock()

    with patch("pecha_api.db.mongo_database.AsyncIOMotorClient") as mock_client_cls, patch(
        "pecha_api.db.mongo_database.init_beanie",
        new_callable=AsyncMock,
    ), patch(
        "pecha_api.db.mongo_database.get",
        side_effect=lambda key: {
            "MONGO_CONNECTION_STRING": "",
            "MONGO_DATABASE_NAME": "testdb",
        }[key],
    ):
        async with lifespan(api):
            assert api.mongodb is None

    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
async def test_lifespan_skips_mongo_when_connection_string_invalid():
    api = MagicMock()

    with patch("pecha_api.db.mongo_database.AsyncIOMotorClient") as mock_client_cls, patch(
        "pecha_api.db.mongo_database.init_beanie",
        new_callable=AsyncMock,
    ), patch(
        "pecha_api.db.mongo_database.get",
        side_effect=_mongo_get_side_effect,
    ):
        mock_client_cls.side_effect = ConfigurationError(
            "Empty host (or extra comma in host list)."
        )

        async with lifespan(api):
            assert api.mongodb is None

    mock_client_cls.assert_called_once()
