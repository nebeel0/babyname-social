"""Bootstrap database with all data - existing backup + new sources"""
import asyncio
import json
import csv
from pathlib import Path
from collections import defaultdict
import asyncpg


async def bootstrap_database():
    """Import all data: backups + new ethnicity + nicknames"""

    print("="*70)
    print("🚀 BABY NAMES DATABASE BOOTSTRAP")
    print("="*70)

    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='postgres',
        database='babynames_db'
    )

    try:
        # Step 1: Restore from backup
        print("\n📦 STEP 1: Restoring existing data from backup...")
        await restore_from_backup(conn)

        # Step 2: Import ethnicity data
        print("\n🌍 STEP 2: Importing ethnicity/race probabilities...")
        await import_ethnicity_data(conn)

        # Step 3: Import nickname data
        print("\n📝 STEP 3: Importing nickname data...")
        await import_nickname_data(conn)

        print("\n" + "="*70)
        print("✅ BOOTSTRAP COMPLETE!")
        print("="*70)

        # Show final statistics
        await show_statistics(conn)

    finally:
        await conn.close()


async def restore_from_backup(conn):
    """Restore data from latest backup"""
    backup_dir = Path(__file__).parent.parent / "data" / "backups" / "latest"

    if not backup_dir.exists():
        print("⚠️  No backup found, skipping restore")
        return

    # Read manifest
    manifest_file = backup_dir / "MANIFEST.json"
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)

    print(f"  📂 Loading backup from: {backup_dir.name}")
    print(f"  📅 Created: {manifest['export_date']}")

    # Order of tables matters due to foreign keys
    table_order = [
        'users',
        'names',
        'famous_namesakes',
        'popularity_trends',
        'popularity_history',
        'name_variants',
        'related_names',
        'name_trivia',
        'cultural_contexts',
        'famous_references',
        'user_name_preferences',
        'comments'
    ]

    total_imported = 0

    for table in table_order:
        json_file = backup_dir / f"{table}.json"
        if not json_file.exists():
            continue

        with open(json_file, 'r') as f:
            data = json.load(f)

        if not data:
            continue

        print(f"  📥 Importing {table}... ", end="")

        # Get column names from first row
        columns = list(data[0].keys())
        placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
        column_list = ', '.join(columns)

        # Prepare insert statement
        insert_sql = f"""
            INSERT INTO {table} ({column_list})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        # Batch insert
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            for row in batch:
                values = [row[col] for col in columns]
                try:
                    await conn.execute(insert_sql, *values)
                except Exception as e:
                    # Skip errors for now
                    pass

        print(f"✅ {len(data):,} rows")
        total_imported += len(data)

    print(f"\n  ✅ Restored {total_imported:,} total rows")


async def import_ethnicity_data(conn):
    """Import Harvard Dataverse ethnicity probabilities"""
    csv_file = Path(__file__).parent.parent / "data" / "sources" / "ethnicity" / "first_nameRaceProbs.csv"

    if not csv_file.exists():
        print(f"  ⚠️  File not found: {csv_file}")
        return

    print(f"  📖 Reading {csv_file.name}...")

    # First, get name_id mapping
    result = await conn.fetch("SELECT id, UPPER(name) as name FROM names")
    name_to_id = {row['name']: row['id'] for row in result}

    imported = 0
    skipped = 0

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        batch = []

        for row in reader:
            name_upper = row['name'].upper()
            name_id = name_to_id.get(name_upper)

            if not name_id:
                skipped += 1
                continue

            # Calculate confidence based on probability distribution
            probs = [float(row['whi']), float(row['bla']), float(row['his']), float(row['asi']), float(row['oth'])]
            max_prob = max(probs)
            confidence = 'high' if max_prob > 0.7 else 'medium' if max_prob > 0.4 else 'low'

            batch.append({
                'name_id': name_id,
                'white_probability': float(row['whi']),
                'black_probability': float(row['bla']),
                'hispanic_probability': float(row['his']),
                'asian_probability': float(row['asi']),
                'other_probability': float(row['oth']),
                'confidence_level': confidence
            })

            if len(batch) >= 1000:
                await insert_ethnicity_batch(conn, batch)
                imported += len(batch)
                print(f"    ✅ Imported {imported:,} ethnicity records...", end='\r')
                batch = []

        # Insert remaining
        if batch:
            await insert_ethnicity_batch(conn, batch)
            imported += len(batch)

    # Update has_ethnicity_data flag
    await conn.execute("""
        UPDATE names
        SET has_ethnicity_data = TRUE
        WHERE id IN (SELECT name_id FROM name_ethnicity_probabilities)
    """)

    print(f"\n  ✅ Imported {imported:,} ethnicity records")
    print(f"  ⏭️  Skipped {skipped:,} (names not in database)")


async def insert_ethnicity_batch(conn, batch):
    """Insert batch of ethnicity records"""
    for record in batch:
        try:
            await conn.execute("""
                INSERT INTO name_ethnicity_probabilities
                (name_id, white_probability, black_probability, hispanic_probability,
                 asian_probability, other_probability, confidence_level, data_source)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'Harvard Dataverse 2023')
                ON CONFLICT (name_id, data_source) DO UPDATE
                SET white_probability = EXCLUDED.white_probability,
                    black_probability = EXCLUDED.black_probability,
                    hispanic_probability = EXCLUDED.hispanic_probability,
                    asian_probability = EXCLUDED.asian_probability,
                    other_probability = EXCLUDED.other_probability,
                    confidence_level = EXCLUDED.confidence_level,
                    updated_at = NOW()
            """, record['name_id'], record['white_probability'], record['black_probability'],
                record['hispanic_probability'], record['asian_probability'], record['other_probability'],
                record['confidence_level'])
        except Exception as e:
            pass  # Skip errors


async def import_nickname_data(conn):
    """Import nickname data from CSV files"""
    data_dir = Path(__file__).parent.parent / "data" / "sources" / "nicknames"

    # Get name_id mapping
    result = await conn.fetch("SELECT id, UPPER(name) as name FROM names")
    name_to_id = {row['name']: row['id'] for row in result}

    total_imported = 0

    # Import male nicknames
    male_file = data_dir / "male_diminutives.csv"
    if male_file.exists():
        count = await import_nickname_file(conn, male_file, name_to_id, 'male')
        print(f"  ✅ Male nicknames: {count:,} mappings")
        total_imported += count

    # Import female nicknames
    female_file = data_dir / "female_diminutives.csv"
    if female_file.exists():
        count = await import_nickname_file(conn, female_file, name_to_id, 'female')
        print(f"  ✅ Female nicknames: {count:,} mappings")
        total_imported += count

    # Update has_nicknames flag and counts
    await conn.execute("""
        UPDATE names
        SET has_nicknames = TRUE,
            nickname_count = (SELECT COUNT(*) FROM name_nicknames WHERE name_id = names.id)
        WHERE id IN (SELECT DISTINCT name_id FROM name_nicknames)
    """)

    print(f"\n  ✅ Total nickname mappings: {total_imported:,}")


async def import_nickname_file(conn, csv_file, name_to_id, gender):
    """Import nicknames from a CSV file"""
    imported = 0

    with open(csv_file, 'r') as f:
        reader = csv.reader(f)

        for row in reader:
            if not row:
                continue

            canonical_name = row[0].strip().upper()
            nicknames = [n.strip() for n in row[1:] if n.strip()]

            name_id = name_to_id.get(canonical_name)
            if not name_id:
                continue

            for rank, nickname in enumerate(nicknames, 1):
                try:
                    await conn.execute("""
                        INSERT INTO name_nicknames (name_id, nickname, is_diminutive, popularity_rank)
                        VALUES ($1, $2, TRUE, $3)
                        ON CONFLICT (name_id, nickname) DO NOTHING
                    """, name_id, nickname, rank)
                    imported += 1
                except Exception:
                    pass

    return imported


async def show_statistics(conn):
    """Show final database statistics"""
    stats = {}

    # Count rows in each table
    tables = ['names', 'famous_namesakes', 'popularity_trends', 'name_ethnicity_probabilities', 'name_nicknames']

    print("\n📊 DATABASE STATISTICS:")
    print("-" * 50)

    for table in tables:
        try:
            result = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table:.<40} {result:>8,}")
        except:
            pass

    # Show names with ethnicity data
    eth_count = await conn.fetchval("SELECT COUNT(*) FROM names WHERE has_ethnicity_data = TRUE")
    print(f"\n  Names with ethnicity data:....................... {eth_count:>8,}")

    # Show names with nicknames
    nick_count = await conn.fetchval("SELECT COUNT(*) FROM names WHERE has_nicknames = TRUE")
    print(f"  Names with nicknames:............................ {nick_count:>8,}")

    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(bootstrap_database())
