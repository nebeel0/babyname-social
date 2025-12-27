"""
SSA Baby Names Scraper
Downloads and parses US Social Security Administration baby name data (1880-2023).
Public domain data, no API key required.
"""
import asyncio
import io
import logging
import zipfile
from pathlib import Path
from typing import List, Dict, Optional

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSAScraper:
    """Scraper for SSA baby name data."""

    BASE_URL = "https://www.ssa.gov/oact/babynames"
    NAMES_ZIP_URL = f"{BASE_URL}/names.zip"

    def __init__(self, db_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db"):
        self.db_url = db_url
        self.data_dir = Path(__file__).parent.parent / "data" / "ssa"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def download_names_zip(self) -> Path:
        """Download the SSA names.zip file containing all years."""
        logger.info(f"Downloading SSA names.zip from {self.NAMES_ZIP_URL}")

        headers = {
            "User-Agent": "BabyNamesSocialApp/1.0 (Educational Project; Python/httpx)"
        }

        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            response = await client.get(self.NAMES_ZIP_URL)
            response.raise_for_status()

        zip_path = self.data_dir / "names.zip"
        zip_path.write_bytes(response.content)

        logger.info(f"Downloaded {len(response.content)} bytes to {zip_path}")
        return zip_path

    def extract_zip(self, zip_path: Path) -> List[Path]:
        """Extract all year files from the zip."""
        logger.info(f"Extracting {zip_path}")

        extract_dir = self.data_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Get all .txt files (yobXXXX.txt format)
        year_files = sorted(extract_dir.glob("yob*.txt"))
        logger.info(f"Extracted {len(year_files)} year files")

        return year_files

    def parse_year_file(self, file_path: Path) -> tuple[int, List[Dict]]:
        """
        Parse a single year file.

        Format: name,gender,count
        Example: Mary,F,7065

        Returns: (year, list of name records)
        """
        # Extract year from filename (yob1880.txt -> 1880)
        year = int(file_path.stem.replace("yob", ""))

        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(',')
                if len(parts) != 3:
                    continue

                name, gender, count = parts
                gender_normalized = 'male' if gender == 'M' else 'female'

                records.append({
                    'name': name,
                    'gender': gender_normalized,
                    'count': int(count),
                    'year': year,
                })

        return year, records

    async def load_year_to_database(self, year: int, records: List[Dict], session: AsyncSession):
        """Load a year's worth of data into the database."""

        # Get all names and create a mapping
        result = await session.execute(select(text("id"), text("name")).select_from(text("names")))
        name_to_id = {name: id for id, name in result}

        # Calculate rankings within each gender for this year
        male_records = sorted([r for r in records if r['gender'] == 'male'],
                             key=lambda x: x['count'], reverse=True)
        female_records = sorted([r for r in records if r['gender'] == 'female'],
                               key=lambda x: x['count'], reverse=True)

        # Add rankings
        for rank, record in enumerate(male_records, 1):
            record['rank'] = rank
        for rank, record in enumerate(female_records, 1):
            record['rank'] = rank

        # Insert records
        inserted = 0
        skipped = 0

        for record in records:
            name_id = name_to_id.get(record['name'])
            if not name_id:
                skipped += 1
                continue

            # Insert trend record
            try:
                await session.execute(text("""
                    INSERT INTO popularity_trends
                    (name_id, year, rank, count, gender, country, source)
                    VALUES (:name_id, :year, :rank, :count, :gender, 'US', 'SSA')
                    ON CONFLICT (name_id, year, gender, country, source) DO NOTHING
                """), {
                    'name_id': name_id,
                    'year': record['year'],
                    'rank': record['rank'],
                    'count': record['count'],
                    'gender': record['gender'],
                })
                inserted += 1
            except Exception as e:
                logger.error(f"Error inserting {record['name']}: {e}")
                skipped += 1

        await session.commit()
        return inserted, skipped

    async def scrape_and_load_all(self, start_year: Optional[int] = None,
                                   end_year: Optional[int] = None):
        """
        Download, parse, and load all SSA data.

        Args:
            start_year: Only process years >= this (default: all)
            end_year: Only process years <= this (default: all)
        """
        # Download and extract
        zip_path = await self.download_names_zip()
        year_files = self.extract_zip(zip_path)

        # Filter by year range if specified
        if start_year or end_year:
            year_files = [
                f for f in year_files
                if (not start_year or int(f.stem.replace("yob", "")) >= start_year)
                and (not end_year or int(f.stem.replace("yob", "")) <= end_year)
            ]

        logger.info(f"Processing {len(year_files)} year files")

        # Setup database
        engine = create_async_engine(self.db_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        total_inserted = 0
        total_skipped = 0

        async with async_session() as session:
            for i, file_path in enumerate(year_files, 1):
                year, records = self.parse_year_file(file_path)
                logger.info(f"[{i}/{len(year_files)}] Processing {year}: {len(records)} records")

                inserted, skipped = await self.load_year_to_database(year, records, session)
                total_inserted += inserted
                total_skipped += skipped

                logger.info(f"  ✅ Inserted: {inserted}, Skipped: {skipped}")

        await engine.dispose()

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ SSA Data Import Complete!")
        logger.info(f"   Years processed: {len(year_files)}")
        logger.info(f"   Total inserted: {total_inserted:,}")
        logger.info(f"   Total skipped: {total_skipped:,}")
        logger.info(f"{'='*60}\n")

        return total_inserted, total_skipped


async def main():
    """Run the SSA scraper."""
    scraper = SSAScraper()

    # For quick testing, process just recent years
    # await scraper.scrape_and_load_all(start_year=2020)

    # For full historical data (takes ~5-10 minutes)
    await scraper.scrape_and_load_all()


if __name__ == "__main__":
    asyncio.run(main())
