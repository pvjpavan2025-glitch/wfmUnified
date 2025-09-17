"""
SQLAlchemy database configuration and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import os

from .config import settings

# Create async engine
if settings.database.sql_database_url:
    SQLALCHEMY_DATABASE_URL = settings.database.sql_database_url
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.database.postgres_user}:{settings.database.postgres_password}@{settings.database.postgres_host}:{settings.database.postgres_port}/{settings.database.postgres_db}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    future=True,
    echo=settings.service.debug if hasattr(settings, 'service') and hasattr(settings.service, 'debug') else False,
    pool_pre_ping=True,
    pool_recycle=300,
    poolclass=NullPool if hasattr(settings, 'testing') and settings.testing else None
)

# Create session factory
async_session_factory = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Create all tables
        from . import models  # Import models to register them with Base
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connections."""
    if engine is not None:
        await engine.dispose()
