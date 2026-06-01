import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pecha_api.db.mongo_database import lifespan


@pytest.mark.asyncio
async def test_lifespan_cancels_invite_task_and_closes_mongo_client():
    api = MagicMock()
    cancelled_task = asyncio.create_task(asyncio.sleep(3600))

    with patch("pecha_api.db.mongo_database.AsyncIOMotorClient") as mock_client_cls, patch(
        "pecha_api.db.mongo_database.init_beanie",
        new_callable=AsyncMock,
    ), patch(
        "pecha_api.db.mongo_database.get",
        side_effect=lambda key: {
            "MONGO_CONNECTION_STRING": "mongodb://localhost:27017",
            "MONGO_DATABASE_NAME": "testdb",
        }[key],
    ), patch(
        "pecha_api.db.mongo_database.asyncio.create_task",
        return_value=cancelled_task,
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        try:
            async with lifespan(api):
                assert api.mongodb is mock_db
        except asyncio.CancelledError:
            pass

    mock_client.close.assert_called_once()
    assert cancelled_task.cancelled() or cancelled_task.done()
