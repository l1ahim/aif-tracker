from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from fastapi import Depends
from typing import Generator
import logging

from .config import settings

# Configure logging
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

# Create engine with optimized settings
engine = create_engine(
    settings.database_url_for_context,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Additional connections beyond pool_size
    echo=settings.DEBUG,  # Only echo SQL in debug mode
    connect_args={
        "connect_timeout": 30,
        "application_name": "aif_tracker_backend",
        "options": "-c timezone=utc"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def create_tables():
    """Create all tables - useful for testing"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables - useful for testing"""
    Base.metadata.drop_all(bind=engine)


# Event listeners for better PostgreSQL performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set PostgreSQL specific settings for better performance"""
    if 'postgresql' in settings.DATABASE_URL:
        with dbapi_connection.cursor() as cursor:
            # Set timezone
            cursor.execute("SET timezone TO 'UTC'")
            # Optimize for better performance
            cursor.execute("SET statement_timeout = '30s'")
            cursor.execute("SET lock_timeout = '10s'")
