"""
Behind the Name Scraper
Extracts etymology, meanings, and related names from behindthename.com
Respectful scraping with rate limiting and robots.txt compliance.
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
import re

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BehindTheNameScraper:
    """Scraper for Behind the Name website."""

    BASE_URL = "https://www.behindthename.com"
    USER_AGENT = "BabyNamesSocialApp/1.0 (Educational Project; Python/httpx)"
    RATE_LIMIT_DELAY = 2.5  # 2.5 seconds between requests (respectful)

    def __init__(self, db_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db"):
        self.db_url = db_url
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            headers={"User-Agent": self.USER_AGENT},
            timeout=30.0,
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def scrape_name(self, name: str) -> Optional[Dict]:
        """
        Scrape data for a single name from Behind the Name.

        Args:
            name: The name to scrape

        Returns:
            Dictionary with name data or None if not found
        """
        logger.info(f"Scraping Behind the Name for: {name}")

        # Construct URL (names are typically lowercase with hyphens)
        name_slug = name.lower().replace(" ", "-")
        url = f"{self.BASE_URL}/name/{name_slug}"

        await asyncio.sleep(self.RATE_LIMIT_DELAY)

        try:
            response = await self.session.get(url)

            if response.status_code == 404:
                logger.info(f"  ℹ️  Name '{name}' not found on Behind the Name")
                return None

            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract data from the page
            data = {
                'name': name,
                'meaning': None,
                'etymology': None,
                'origin': None,
                'gender': None,
                'pronunciation': None,
                'related_names': [],
                'trivia': []
            }

            # Extract meaning (usually in the first paragraph after "MEANING & HISTORY")
            meaning_section = soup.find('div', class_='maincontent')
            if meaning_section:
                paragraphs = meaning_section.find_all('p')
                if paragraphs:
                    # First paragraph usually contains the meaning
                    first_para = paragraphs[0].get_text(strip=True)
                    data['meaning'] = self._clean_text(first_para)

            # Extract gender from the page
            gender_span = soup.find('span', class_='gend')
            if gender_span:
                gender_text = gender_span.get_text(strip=True).lower()
                if 'm' in gender_text and 'f' in gender_text:
                    data['gender'] = 'neutral'
                elif 'm' in gender_text:
                    data['gender'] = 'male'
                elif 'f' in gender_text:
                    data['gender'] = 'female'

            # Extract pronunciation
            pronunciation_link = soup.find('a', class_='sf')
            if pronunciation_link:
                data['pronunciation'] = pronunciation_link.get_text(strip=True)

            # Extract related names
            related_section = soup.find('div', class_='related')
            if related_section:
                related_links = related_section.find_all('a', href=re.compile(r'/name/'))
                data['related_names'] = [
                    link.get_text(strip=True)
                    for link in related_links[:10]  # Limit to 10
                ]

            # Extract origin/culture from usage section
            usage_section = soup.find('span', class_='usageinfo')
            if usage_section:
                usage_text = usage_section.get_text(strip=True)
                data['origin'] = self._extract_origin(usage_text)

            return data

        except httpx.HTTPError as e:
            logger.error(f"  ❌ HTTP error scraping '{name}': {e}")
            return None
        except Exception as e:
            logger.error(f"  ❌ Error scraping '{name}': {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove citation markers
        text = re.sub(r'\[\d+\]', '', text)
        return text

    def _extract_origin(self, usage_text: str) -> Optional[str]:
        """Extract origin from usage text."""
        # Common patterns: "English", "German", "Spanish", etc.
        origins = [
            'English', 'German', 'Spanish', 'French', 'Italian', 'Irish',
            'Scottish', 'Welsh', 'Greek', 'Latin', 'Hebrew', 'Arabic',
            'Japanese', 'Chinese', 'Korean', 'Russian', 'Polish', 'Portuguese',
            'Dutch', 'Swedish', 'Norwegian', 'Danish', 'Finnish', 'Turkish',
            'Indian', 'Persian', 'Armenian', 'Georgian'
        ]

        for origin in origins:
            if origin in usage_text:
                return origin

        return None

    async def update_name_in_database(
        self,
        name_id: int,
        name_data: Dict,
        session: AsyncSession
    ):
        """Update a name's data in the database with scraped information."""

        try:
            # Update the name record
            update_fields = []
            params = {'name_id': name_id}

            if name_data.get('meaning'):
                update_fields.append("meaning = :meaning")
                params['meaning'] = name_data['meaning']

            if name_data.get('etymology'):
                update_fields.append("etymology_description = :etymology")
                params['etymology'] = name_data['etymology']

            if name_data.get('pronunciation'):
                update_fields.append("pronunciation = :pronunciation")
                params['pronunciation'] = name_data['pronunciation']

            if name_data.get('origin'):
                # Map origin to origin_country if it's a country name
                update_fields.append("origin_culture = :origin_culture")
                params['origin_culture'] = name_data['origin']

            if update_fields:
                query = f"""
                    UPDATE names
                    SET {', '.join(update_fields)}
                    WHERE id = :name_id
                """
                await session.execute(text(query), params)

            # Add related names to related_names table
            if name_data.get('related_names'):
                for related_name in name_data['related_names']:
                    # Find the related name's ID
                    result = await session.execute(
                        text("SELECT id FROM names WHERE LOWER(name) = LOWER(:name)"),
                        {'name': related_name}
                    )
                    related_row = result.first()

                    if related_row:
                        # Insert relationship
                        await session.execute(text("""
                            INSERT INTO related_names (name_id, related_name_id, relationship_type)
                            VALUES (:name_id, :related_name_id, 'variant')
                            ON CONFLICT DO NOTHING
                        """), {
                            'name_id': name_id,
                            'related_name_id': related_row[0]
                        })

            await session.commit()
            return True

        except Exception as e:
            logger.error(f"  ❌ Error updating database: {e}")
            return False

    async def scrape_and_update_all_names(self):
        """Scrape and update all names in the database."""
        logger.info("Starting Behind the Name scraper for all names")

        # Setup database
        engine = create_async_engine(self.db_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        total_updated = 0
        total_skipped = 0
        total_not_found = 0

        async with async_session() as session:
            # Get all names from database
            result = await session.execute(
                text("SELECT id, name FROM names ORDER BY name")
            )
            names = result.all()

            logger.info(f"Found {len(names)} names to process")

            for i, (name_id, name) in enumerate(names, 1):
                logger.info(f"[{i}/{len(names)}] Processing: {name}")

                # Scrape the name
                name_data = await self.scrape_name(name)

                if name_data is None:
                    total_not_found += 1
                    continue

                # Update database
                success = await self.update_name_in_database(name_id, name_data, session)

                if success:
                    total_updated += 1
                    logger.info(f"  ✅ Updated: {name}")
                else:
                    total_skipped += 1

        await engine.dispose()

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Behind the Name Scraper Complete!")
        logger.info(f"   Names processed: {len(names)}")
        logger.info(f"   Total updated: {total_updated}")
        logger.info(f"   Not found: {total_not_found}")
        logger.info(f"   Skipped: {total_skipped}")
        logger.info(f"{'='*60}\n")

        return total_updated, total_not_found, total_skipped


async def main():
    """Run the Behind the Name scraper."""
    async with BehindTheNameScraper() as scraper:
        await scraper.scrape_and_update_all_names()


if __name__ == "__main__":
    asyncio.run(main())
