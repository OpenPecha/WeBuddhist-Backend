
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import declarative_base
from starlette.concurrency import run_in_threadpool

from ..config import get


engine = create_engine(get("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


async def get_db() -> AsyncGenerator[Session, None]:
    """Provide a request-scoped session without blocking the event loop."""
    db = SessionLocal()
    try:
        yield db
    finally:
        await run_in_threadpool(db.close)