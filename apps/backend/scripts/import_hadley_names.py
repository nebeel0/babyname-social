"""Import baby names from Hadley Wickham's dataset."""
import asyncio
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


async def import_hadley_names():
    """Import baby names from Hadley's CSV file."""

    # Database connection
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db",
        echo=False,
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Load CSV
    csv_file = Path(__file__).parent.parent / "data" / "hadley-baby-names.csv"
    print(f"📖 Reading {csv_file}")

    # Parse CSV and collect unique names and their trends
    unique_names = {}  # name -> {gender, first_year}
    trends_data = []  # list of trend records

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = int(row['year'])
            name = row['name']
            percent = float(row['percent'])
            sex = row['sex']
            gender = 'male' if sex == 'boy' else 'female'

            # Track unique names
            if name not in unique_names:
                unique_names[name] = {
                    'gender': gender,
                    'first_year': year
                }
            else:
                # Update first_year if this is earlier
                if year < unique_names[name]['first_year']:
                    unique_names[name]['first_year'] = year

            # Store trend data (we'll insert after names are in DB)
            trends_data.append({
                'name': name,
                'year': year,
                'percent': percent,
                'gender': gender
            })

    print(f"📊 Found {len(unique_names)} unique names")
    print(f"📊 Found {len(trends_data)} popularity trend records")

    async with async_session() as session:
        # Step 1: Get existing names from database
        print("\n🔍 Checking existing names...")
        result = await session.execute(text("SELECT name, id FROM names"))
        existing_names_map = {row.name: row.id for row in result}
        print(f"  ℹ️  Found {len(existing_names_map)} existing names in database")

        # Step 2: Insert unique names into names table
        print("\n💾 Inserting new names into database...")
        added_names = 0
        skipped_names = 0

        for name, data in unique_names.items():
            if name in existing_names_map:
                # Name already exists, just skip
                skipped_names += 1
                continue

            try:
                # Insert name
                result = await session.execute(text("""
                    INSERT INTO names (name, gender, first_recorded_year, origin_country, total_users_count, rating_count)
                    VALUES (:name, :gender, :first_year, 'United States', 0, 0)
                    ON CONFLICT (name) DO UPDATE
                    SET first_recorded_year = LEAST(names.first_recorded_year, EXCLUDED.first_recorded_year)
                    RETURNING id
                """), {
                    'name': name,
                    'gender': data['gender'],
                    'first_year': data['first_year']
                })

                added_names += 1
                if added_names % 1000 == 0:
                    print(f"  ✅ Inserted {added_names} names...")
                    await session.commit()

            except Exception as e:
                print(f"  ⚠️  Error inserting {name}: {e}")
                skipped_names += 1
                # Rollback the current transaction
                await session.rollback()

        await session.commit()
        print(f"  ✅ Total names inserted/updated: {added_names}")
        print(f"  ⏭️  Skipped (already in DB): {skipped_names}")

        # Step 3: Get name_id mapping
        print("\n🔍 Building name to ID mapping...")
        result = await session.execute(text("""
            SELECT id, name FROM names
        """))
        name_to_id = {row.name: row.id for row in result}

        print(f"  ✅ Mapped {len(name_to_id)} names")

        # Step 4: Insert popularity trends
        print("\n💾 Inserting popularity trends...")
        inserted_trends = 0
        skipped_trends = 0
        batch_size = 5000
        batch = []

        for i, trend in enumerate(trends_data):
            name_id = name_to_id.get(trend['name'])

            if not name_id:
                skipped_trends += 1
                continue

            batch.append({
                'name_id': name_id,
                'year': trend['year'],
                'percent': trend['percent'],
                'gender': trend['gender']
            })

            # Insert in batches
            if len(batch) >= batch_size:
                await insert_trends_batch(session, batch)
                inserted_trends += len(batch)
                print(f"  ✅ Inserted {inserted_trends:,} trends...")
                batch = []

        # Insert remaining batch
        if batch:
            await insert_trends_batch(session, batch)
            inserted_trends += len(batch)

        await session.commit()
        print(f"  ✅ Total trends inserted: {inserted_trends:,}")
        print(f"  ⏭️  Skipped: {skipped_trends:,}")

    await engine.dispose()

    print(f"\n{'='*60}")
    print(f"✅ Import Complete!")
    print(f"   Unique names: {len(unique_names):,}")
    print(f"   Trends imported: {inserted_trends:,}")
    print(f"{'='*60}\n")


async def insert_trends_batch(session: AsyncSession, batch: List[Dict]):
    """Insert a batch of trend records."""
    for trend in batch:
        try:
            await session.execute(text("""
                INSERT INTO popularity_trends
                (name_id, year, count, gender, country, source)
                VALUES (:name_id, :year, NULL, :gender, 'US', 'Hadley')
                ON CONFLICT (name_id, year, gender, country, source) DO NOTHING
            """), trend)
        except Exception as e:
            # Skip errors silently for batch inserts
            pass


if __name__ == "__main__":
    asyncio.run(import_hadley_names())
