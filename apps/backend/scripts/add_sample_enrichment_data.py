"""Add sample enrichment data to demonstrate features."""
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def add_sample_data():
    """Add sample famous people and trends data."""
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db",
        echo=False,
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Add famous people for Emma
        await session.execute(text("""
            INSERT INTO famous_namesakes (name_id, full_name, category, description, profession, birth_year, notable_for)
            SELECT id, 'Emma Watson', 'celebrity', 'British actress best known for playing Hermione Granger', 'Actress', 1990, 'Harry Potter film series'
            FROM names WHERE name = 'Emma' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        await session.execute(text("""
            INSERT INTO famous_namesakes (name_id, full_name, category, description, profession, birth_year, notable_for)
            SELECT id, 'Emma Stone', 'celebrity', 'Academy Award-winning American actress', 'Actress', 1988, 'La La Land, Easy A'
            FROM names WHERE name = 'Emma' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        # Add famous people for Olivia
        await session.execute(text("""
            INSERT INTO famous_namesakes (name_id, full_name, category, description, profession, birth_year, notable_for)
            SELECT id, 'Olivia Rodrigo', 'celebrity', 'American singer-songwriter and actress', 'Singer', 2003, 'drivers license, good 4 u'
            FROM names WHERE name = 'Olivia' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        # Add famous people for Alexander
        await session.execute(text("""
            INSERT INTO famous_namesakes (name_id, full_name, category, description, profession, birth_year, death_year, notable_for)
            SELECT id, 'Alexander the Great', 'historical', 'Ancient Macedonian ruler and military commander', 'King/Military Leader', -356, -323, 'Created one of the largest empires in history'
            FROM names WHERE name = 'Alexander' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        await session.execute(text("""
            INSERT INTO famous_namesakes (name_id, full_name, category, description, profession, birth_year, death_year, notable_for)
            SELECT id, 'Alexander Hamilton', 'historical', 'American founding father and first Secretary of Treasury', 'Politician/Economist', 1755, 1804, 'Founding Father, Broadway musical'
            FROM names WHERE name = 'Alexander' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        # Add popularity trends for Emma (sample data)
        await session.execute(text("""
            INSERT INTO popularity_trends (name_id, year, rank, count, gender, source)
            SELECT id, 2023, 1, 15000, 'female', 'SSA' FROM names WHERE name = 'Emma' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        await session.execute(text("""
            INSERT INTO popularity_trends (name_id, year, rank, count, gender, source)
            SELECT id, 2020, 2, 15000, 'female', 'SSA' FROM names WHERE name = 'Emma' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        await session.execute(text("""
            INSERT INTO popularity_trends (name_id, year, rank, count, gender, source)
            SELECT id, 2010, 3, 17000, 'female', 'SSA' FROM names WHERE name = 'Emma' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        await session.execute(text("""
            INSERT INTO popularity_trends (name_id, year, rank, count, gender, source)
            SELECT id, 2000, 15, 8000, 'female', 'SSA' FROM names WHERE name = 'Emma' LIMIT 1
            ON CONFLICT DO NOTHING;
        """))

        # Mark names as enriched
        await session.execute(text("""
            UPDATE names SET has_famous_people = TRUE, has_trends = TRUE
            WHERE name IN ('Emma', 'Olivia', 'Alexander');
        """))

        await session.commit()
        print("✅ Sample enrichment data added successfully!")
        print("   - Added famous people for Emma, Olivia, Alexander")
        print("   - Added popularity trends for Emma")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_sample_data())
