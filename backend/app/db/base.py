"""
SQLAlchemy base class and session management.
All models should inherit from Base.
"""
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy import create_engine
from app.core.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Scoped session for thread-safe database access
db_session = scoped_session(SessionFactory)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes.
    Yields a database session and ensures cleanup.
    """
    session = db_session()
    try:
        yield session
    finally:
        session.close()
