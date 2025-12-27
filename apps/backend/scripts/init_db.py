"""Initialize database tables for both databases."""
import asyncio

from db.base import Base, names_engine, users_engine
from db.models import *  # noqa: F403, F401
from db.models.user import User  # noqa: F401


async def init_databases() -> None:
    """Create all database tables."""
    print("Creating tables in names database...")
    async with names_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Names database initialized!")

    print("\nCreating tables in users database...")
    async with users_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Users database initialized!")

    print("\n✨ All databases initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_databases())
