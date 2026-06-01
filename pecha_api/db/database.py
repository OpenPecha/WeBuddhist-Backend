
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from ..config import get


# Configure connection pool to prevent memory leaks
engine = create_engine(
    get("DATABASE_URL"),
    pool_size=10,                    # Maximum number of permanent connections in pool
    max_overflow=20,                 # Maximum number of temporary connections
    pool_pre_ping=True,             # Verify connections before use
    pool_recycle=1800,              # Recycle connections every 30 minutes
    echo=False                       # Disable SQL logging in production
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()