"""One-command bootstrap script to rebuild entire database

This script implements the Bronze → Gold ETL pipeline:
1. Run migrations (create tables)
2. Load from Bronze layer (source files)
3. Generate statistics

Usage:
    uv run python scripts/bootstrap.py
"""
import asyncio
import sys
from pathlib import Path


async def main():
    print("="*70)
    print("🚀 BABY NAMES DATABASE BOOTSTRAP")
    print("="*70)
    print("\nThis script will:")
    print("  1. Run database migrations")
    print("  2. Import all data from Bronze layer (sources/)")
    print("  3. Generate statistics\n")

    # Step 1: Run migrations
    print("📦 STEP 1: Running database migrations...")
    from run_migration_incremental import run_migration
    success = await run_migration()
    if not success:
        print("❌ Migration failed!")
        return False

    # Step 2: Import all data
    print("\n📦 STEP 2: Importing data from Bronze layer...")
    from import_all_data import bootstrap_database
    await bootstrap_database()

    print("\n" + "="*70)
    print("✅ BOOTSTRAP COMPLETE!")
    print("="*70)
    print("\n📊 Your database is ready with:")
    print("  - Names table (~6,783 names)")
    print("  - Ethnicity probabilities (~6,751 records)")
    print("  - Nicknames (~1,042 mappings)")
    print("  - Historical popularity trends (~273,000 records)")
    print("  - Famous namesakes (~807 records)")
    print("\n🎉 You can now start the API server!")
    print("   Command: uv run fastapi dev app/main.py\n")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
