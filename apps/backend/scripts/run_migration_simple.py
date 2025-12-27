"""Run database migration script using asyncpg directly"""
import asyncio
import sys
from pathlib import Path
import asyncpg


async def run_migration(migration_file: str):
    """Run a SQL migration file"""
    migration_path = Path(__file__).parent.parent / "db" / "migrations" / migration_file

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False

    print(f"📂 Running migration: {migration_file}")

    with open(migration_path, 'r') as f:
        sql = f.read()

    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='postgres',
        database='babynames_db'
    )

    try:
        print("⚙️  Executing migration...")
        await conn.execute(sql)
        print(f"✅ Migration {migration_file} completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    migration_file = sys.argv[1] if len(sys.argv) > 1 else "003_add_demographic_and_personalization.sql"
    success = asyncio.run(run_migration(migration_file))
    sys.exit(0 if success else 1)
