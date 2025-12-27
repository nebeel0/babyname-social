"""Run database migration script"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import get_engine
from sqlalchemy import text


async def run_migration(migration_file: str):
    """Run a SQL migration file"""
    engine = get_engine("babynames")

    migration_path = Path(__file__).parent.parent / "db" / "migrations" / migration_file

    if not migration_path.exists():
        print(f"Migration file not found: {migration_path}")
        return False

    print(f"Running migration: {migration_file}")

    with open(migration_path, 'r') as f:
        sql = f.read()

    async with engine.begin() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        for i, statement in enumerate(statements, 1):
            try:
                print(f"Executing statement {i}/{len(statements)}...")
                await conn.execute(text(statement))
            except Exception as e:
                print(f"Error in statement {i}: {e}")
                print(f"Statement: {statement[:200]}...")
                raise

    print(f"✓ Migration {migration_file} completed successfully")
    return True


if __name__ == "__main__":
    migration_file = sys.argv[1] if len(sys.argv) > 1 else "003_add_demographic_and_personalization.sql"
    asyncio.run(run_migration(migration_file))
