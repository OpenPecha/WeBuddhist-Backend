from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pecha_api.db.mongo_database import lifespan


@pytest.mark.asyncio
async def test_lifespan_closes_mongo_client_on_shutdown():
    api = MagicMock()

    with patch("pecha_api.db.mongo_database.AsyncIOMotorClient") as mock_client_cls, patch(
        "pecha_api.db.mongo_database.init_beanie",
        new_callable=AsyncMock,
    ), patch(
        "pecha_api.db.mongo_database.get",
        side_effect=lambda key: {
            "MONGO_CONNECTION_STRING": "mongodb://localhost:27017",
            "MONGO_DATABASE_NAME": "testdb",
        }[key],
    ), patch("pecha_api.db.mongo_database.setup_scheduler") as mock_setup_scheduler, patch(
        "pecha_api.db.mongo_database.shutdown_scheduler"
    ) as mock_shutdown_scheduler:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        async with lifespan(api):
            assert api.mongodb is mock_db

    mock_setup_scheduler.assert_called_once()
    mock_shutdown_scheduler.assert_called_once()
    mock_client.close.assert_called_once()
