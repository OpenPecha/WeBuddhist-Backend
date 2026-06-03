import logging
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConfigurationError

from ..topics.topics_models import Topic
from ..collections.collections_models import Collection
from ..terms.terms_models import Term
from ..texts.texts_models import Text
from ..texts.segments.segments_models import Segment
from ..texts.texts_models import TableOfContent
from ..texts.groups.groups_models import Group
from ..config import get

logger = logging.getLogger(__name__)

mongodb_client = None
mongodb = None

BEANIE_DOCUMENT_MODELS = [
    Collection,
    Term,
    Topic,
    Text,
    Segment,
    TableOfContent,
    Group,
]


def _is_mongo_connection_string_configured(connection_string: str) -> bool:
    return bool(connection_string and connection_string.strip())


@asynccontextmanager
async def lifespan(api: FastAPI):
    global mongodb_client, mongodb
    api.mongodb = None

    connection_string = get("MONGO_CONNECTION_STRING")
    if not _is_mongo_connection_string_configured(connection_string):
        logger.warning(
            "MONGO_CONNECTION_STRING is not set; MongoDB and Beanie will not be initialized."
        )
        yield
        return

    try:
        mongodb_client = AsyncIOMotorClient(connection_string)
        mongodb = mongodb_client[get("MONGO_DATABASE_NAME")]
        api.mongodb = mongodb
    except ConfigurationError:
        logger.exception(
            "Invalid MONGO_CONNECTION_STRING; MongoDB will not be initialized."
        )
        yield
        return
    except Exception:
        logger.exception(
            "Failed to create MongoDB client; MongoDB will not be initialized."
        )
        yield
        return

    try:
        await init_beanie(
            database=mongodb,
            document_models=BEANIE_DOCUMENT_MODELS,
        )
        logger.info("Beanie initialized with MongoDB document models.")
    except Exception:
        logger.exception("Error during Beanie initialization.")

    yield

    if mongodb_client:
        mongodb_client.close()