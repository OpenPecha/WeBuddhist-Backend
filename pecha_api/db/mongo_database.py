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
from ..texts.groups.groups_models import Group
from ..config import get
from fastapi import HTTPException

mongodb_client = None
mongodb = None


@asynccontextmanager
async def lifespan(api: FastAPI):
    global mongodb_client, mongodb
    # Initialize the MongoDB client and database
    mongodb_client = AsyncIOMotorClient(get("MONGO_CONNECTION_STRING"))
    mongodb = mongodb_client[get("MONGO_DATABASE_NAME")]
    api.mongodb = mongodb  # Attach the database instance to the FastAPI app

    # Initialize collections and indexes if necessary
    try:
        await init_beanie(database=mongodb,document_models=[Collection, Term, Topic, Text, Segment, TableOfContent, Group])
        logging.info("Beanie initialized with the 'terms' collection.")
        
    except Exception as e:
        logging.error(f"Error during collection initialization: {e}")
        raise
    # Yield control back to FastAPI
    yield

    # Close the MongoDB connection when the application shuts down
    if mongodb_client:
        mongodb_client.close()