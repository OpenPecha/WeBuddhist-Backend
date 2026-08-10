import logging
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from ..topics.topics_models import Topic
from ..collections.collections_models import Collection
from ..terms.terms_models import Term
from ..texts.texts_models import Text
from ..texts.segments.segments_models import Segment
from ..texts.texts_models import TableOfContent
from ..texts.text_audio_models import TextAudio
from ..texts.groups.groups_models import Group
from ..config import get
from ..scheduler import setup_scheduler, shutdown_scheduler
from ..group_posts.comment_websocket import init_broadcaster
from ..chat.chat_websocket import init_broadcaster as init_chat_broadcaster

mongodb_client = None
mongodb = None


@asynccontextmanager
async def lifespan(api: FastAPI):
    global mongodb_client, mongodb
    # Initialize the MongoDB client and database
    mongodb_client = AsyncIOMotorClient(get("MONGO_CONNECTION_STRING"))
    mongodb = mongodb_client[get("MONGO_DATABASE_NAME")]
    api.mongodb = mongodb  # Attach the database instance to the FastAPI app

    try:
        # Initialize collections and indexes if necessary
        try:
            await init_beanie(
                database=mongodb,
                document_models=[
                    Collection,
                    Term,
                    Topic,
                    Text,
                    Segment,
                    TableOfContent,
                    TextAudio,
                    Group,
                ],
            )
            logging.info("Beanie initialized with the 'terms' collection.")
        except Exception as e:
            logging.error(f"Error during collection initialization: {e}")
            raise

        setup_scheduler()

        # Initialize the comment WebSocket broadcaster (connects to Redis)
        try:
            redis_url = get("REDIS_URL")
            await init_broadcaster(redis_url=redis_url)
            logging.info("✅ Comment broadcaster initialized with Redis")
            await init_chat_broadcaster(redis_url=redis_url)
            logging.info("✅ Chat broadcaster initialized with Redis")
        except ConnectionRefusedError as e:
            error_msg = (
                f"❌ REDIS CONNECTION FAILED: Cannot connect to Redis at {get('REDIS_URL')}\n"
                f"   - Make sure Redis/Dragonfly is running\n"
                f"   - Check REDIS_URL config: {get('REDIS_URL')}\n"
                f"   - Try: docker run -d -p 6379:6379 redis:latest\n"
                f"   Error: {e}"
            )
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e
        except TimeoutError as e:
            error_msg = (
                f"❌ REDIS TIMEOUT: Connection to Redis at {get('REDIS_URL')} timed out\n"
                f"   - Redis may be unresponsive or overloaded\n"
                f"   - Check REDIS_URL: {get('REDIS_URL')}\n"
                f"   Error: {e}"
            )
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = (
                f"❌ REDIS INITIALIZATION FAILED: {type(e).__name__}\n"
                f"   - Redis URL: {get('REDIS_URL')}\n"
                f"   - Error: {str(e)}\n"
                f"   - Make sure Redis/Dragonfly is running and accessible"
            )
            logging.error(error_msg)
            raise RuntimeError(error_msg) from e

        yield
    finally:
        shutdown_scheduler()
        # Disconnect the comment broadcaster
        from ..group_posts.comment_websocket import broadcaster
        if broadcaster:
            await broadcaster.disconnect()
            logging.info("Comment broadcaster disconnected")
        from ..chat.chat_websocket import broadcaster as chat_broadcaster
        if chat_broadcaster:
            await chat_broadcaster.disconnect()
            logging.info("Chat broadcaster disconnected")
        if mongodb_client:
            mongodb_client.close()