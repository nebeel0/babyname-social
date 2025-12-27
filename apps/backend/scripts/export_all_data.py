"""Export all database data to JSON format for backup and bootstrap"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
import asyncpg


async def export_all_data():
    """Export all tables to JSON files"""
    export_dir = Path(__file__).parent.parent / "data" / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    export_dir.mkdir(parents=True, exist_ok=True)

    print(f"📂 Exporting data to: {export_dir}")

    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='postgres',
        database='babynames_db'
    )

    try:
        # Get list of all tables
        tables_result = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = [row['table_name'] for row in tables_result]
        print(f"📊 Found {len(tables)} tables to export")

        total_rows = 0
        exports = {}

        for table in tables:
            print(f"\n📦 Exporting {table}...", end=" ")

            # Get all data from table
            rows = await conn.fetch(f"SELECT * FROM {table}")

            # Convert to dict
            data = [dict(row) for row in rows]

            # Convert datetime objects to ISO format strings
            for row in data:
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):
                        row[key] = value.isoformat()

            # Save to JSON file
            output_file = export_dir / f"{table}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            print(f"✅ {len(data):,} rows")
            total_rows += len(data)

            exports[table] = {
                'rows': len(data),
                'file': f"{table}.json"
            }

        # Create manifest file
        manifest = {
            'export_date': datetime.now().isoformat(),
            'total_rows': total_rows,
            'tables': exports
        }

        manifest_file = export_dir / "MANIFEST.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"\n{'='*60}")
        print(f"✅ Export Complete!")
        print(f"   Location: {export_dir}")
        print(f"   Total rows: {total_rows:,}")
        print(f"   Total tables: {len(tables)}")
        print(f"   Manifest: MANIFEST.json")
        print(f"{'='*60}\n")

        # Also create a "latest" symlink
        latest_link = export_dir.parent / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(export_dir.name)
        print(f"🔗 Created symlink: backups/latest -> {export_dir.name}\n")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(export_all_data())
