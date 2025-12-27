"""Seed the database with a corpus of baby names."""
import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from db.models.name import Name


async def seed_names():
    """Load baby names from JSON file into database."""
    # Database connection
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db",
        echo=True,
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Load names from JSON
    data_file = Path(__file__).parent.parent / "data" / "baby_names.json"
    with open(data_file, "r") as f:
        names_data = json.load(f)

    async with async_session() as session:
        # Check which names already exist
        existing_names = await session.execute(select(Name.name))
        existing_set = {name for (name,) in existing_names}

        # Track duplicates in the dataset itself
        seen_in_file = set()

        # Add new names
        added_count = 0
        skipped_count = 0
        duplicate_in_file = 0

        for name_data in names_data:
            # Check if duplicate in the JSON file itself
            if name_data["name"] in seen_in_file:
                print(f"⚠️  Duplicate in file: {name_data['name']}")
                duplicate_in_file += 1
                continue

            seen_in_file.add(name_data["name"])

            if name_data["name"] in existing_set:
                print(f"⏭️  Skipping {name_data['name']} (already exists in DB)")
                skipped_count += 1
                continue

            name = Name(**name_data)
            session.add(name)
            print(f"✅ Adding {name_data['name']}")
            added_count += 1

        # Commit all changes
        await session.commit()

        print(f"\n📊 Summary:")
        print(f"   Added: {added_count} names")
        print(f"   Skipped (already in DB): {skipped_count} names")
        print(f"   Duplicates in file: {duplicate_in_file} names")
        print(f"   Total in file: {len(names_data)} names")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_names())
