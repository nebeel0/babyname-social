from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
import asyncpg

from core.settings import get_settings

settings = get_settings()

# Create async engines for both databases
names_engine = create_async_engine(
    settings.names_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

users_engine = create_async_engine(
    settings.users_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create session makers
NamesSessionLocal = async_sessionmaker(
    names_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

UsersSessionLocal = async_sessionmaker(
    users_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Dependency for FastAPI
async def get_names_db() -> AsyncSession:
    """Get async database session for names database."""
    async with NamesSessionLocal() as session:
        yield session


async def get_users_db() -> AsyncSession:
    """Get async database session for users database."""
    async with UsersSessionLocal() as session:
        yield session


async def get_names_db_raw():
    """Get raw asyncpg connection for names database (for custom queries)"""
    # Extract connection params from SQLAlchemy URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    url_str = str(settings.names_database_url)
    # Convert postgresql+asyncpg:// to just extract params
    conn = await asyncpg.connect(
        host=settings.NAMES_DB_HOST,
        port=settings.NAMES_DB_PORT,
        user=settings.NAMES_DB_USER,
        password=settings.NAMES_DB_PASSWORD,
        database=settings.NAMES_DB_NAME,
    )
    try:
        yield conn
    finally:
        await conn.close()
