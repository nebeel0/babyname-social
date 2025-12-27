"""Check which tables exist in database"""
import asyncio
import asyncpg


async def check_tables():
    """List all tables"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='postgres',
        password='postgres',
        database='babynames_db'
    )

    try:
        # List all tables
        result = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print("📊 Tables in database:")
        for row in result:
            print(f"  - {row['table_name']}")

        print(f"\n✅ Total: {len(result)} tables")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_tables())
