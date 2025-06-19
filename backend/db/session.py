from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os
from typing import Generator

# Import config for database URL
try:
    from ..config import DATABASE_URL
except ImportError:
    # Fallback for direct execution
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/knowthee")

# Create engine and session factory with connection parameters
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=5,         # Maximum number of connections to keep
    max_overflow=10,     # Maximum number of connections that can be created beyond pool_size
    echo=False           # Disable SQL query logging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions.
    
    Yields:
        Session: A SQLAlchemy database session.
        
    Example:
        with get_db() as db:
            db.query(Employee).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_db_dep() -> Generator[Session, None, None]:
    """FastAPI dependency version of get_db (not a context manager)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize the database by creating all tables."""
    from .models import Base
    Base.metadata.create_all(bind=engine) 