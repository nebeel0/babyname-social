"""
Wikipedia Famous People Scraper
Uses the official MediaWiki API to find famous people for each baby name.
Fully compliant with Wikipedia's ToS and rate limiting guidelines.
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WikipediaFamousPeopleScraper:
    """Scraper for finding famous people via Wikipedia API."""

    API_URL = "https://en.wikipedia.org/w/api.php"
    USER_AGENT = "BabyNamesSocialApp/1.0 (Educational Project; Contact: developer@example.com)"
    RATE_LIMIT_DELAY = 1.5  # 1.5 seconds between requests (respectful rate limiting)

    def __init__(self, db_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db"):
        self.db_url = db_url
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            headers={"User-Agent": self.USER_AGENT},
            timeout=30.0
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def search_famous_people(self, name: str, limit: int = 10) -> List[Dict]:
        """
        Search for famous people with a given name using Wikipedia API.

        Args:
            name: The first name to search for
            limit: Maximum number of people to return

        Returns:
            List of dictionaries with person data
        """
        logger.info(f"Searching Wikipedia for people named '{name}'")

        # Search for pages in categories related to the name
        search_queries = [
            f"{name} (given name)",
            f"People named {name}",
            name
        ]

        all_people = []

        for query in search_queries:
            await asyncio.sleep(self.RATE_LIMIT_DELAY)

            # First, search for relevant pages
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": 20,
                "srnamespace": 0,  # Main namespace only
            }

            try:
                response = await self.session.get(self.API_URL, params=search_params)
                response.raise_for_status()
                data = response.json()

                search_results = data.get("query", {}).get("search", [])

                # Filter for biographical pages
                for result in search_results:
                    title = result.get("title", "")

                    # Skip disambiguation pages and list pages
                    if "(disambiguation)" in title or title.startswith("List of"):
                        continue

                    # Get detailed info about this page
                    person_data = await self._get_person_details(title, name)
                    if person_data:
                        all_people.append(person_data)

                    if len(all_people) >= limit:
                        break

            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")
                continue

            if len(all_people) >= limit:
                break

        return all_people[:limit]

    async def _get_person_details(self, page_title: str, first_name: str) -> Optional[Dict]:
        """
        Get detailed information about a person from their Wikipedia page.

        Args:
            page_title: Wikipedia page title
            first_name: The first name we're searching for (to validate)

        Returns:
            Dictionary with person data or None if not valid
        """
        await asyncio.sleep(self.RATE_LIMIT_DELAY)

        params = {
            "action": "query",
            "prop": "extracts|pageprops|categories",
            "titles": page_title,
            "format": "json",
            "exintro": True,
            "explaintext": True,
            "cllimit": 50,
        }

        try:
            response = await self.session.get(self.API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None

            page = list(pages.values())[0]

            # Skip if page doesn't exist
            if "missing" in page:
                return None

            title = page.get("title", "")
            extract = page.get("extract", "")
            categories = [cat.get("title", "") for cat in page.get("categories", [])]

            # Validate this is a biographical page
            if not self._is_biographical_page(categories, extract):
                return None

            # Extract birth/death years and profession from the intro text
            birth_year, death_year = self._extract_years(extract)
            profession = self._extract_profession(extract, categories)
            category = self._determine_category(categories, extract)
            notable_for = self._extract_notable_achievement(extract)

            # Get Wikipedia URL
            wikipedia_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

            return {
                "full_name": title,
                "category": category,
                "description": extract[:500] if extract else None,  # First 500 chars
                "profession": profession,
                "birth_year": birth_year,
                "death_year": death_year,
                "notable_for": notable_for,
                "image_url": None,  # Could be enhanced later with image API
                "wikipedia_url": wikipedia_url,
            }

        except Exception as e:
            logger.error(f"Error getting details for '{page_title}': {e}")
            return None

    def _is_biographical_page(self, categories: List[str], extract: str) -> bool:
        """Check if this is a biographical page."""
        # Check categories for biographical indicators
        bio_keywords = [
            "births", "deaths", "people", "actors", "musicians", "writers",
            "politicians", "scientists", "athletes", "artists", "directors"
        ]

        category_text = " ".join(categories).lower()
        for keyword in bio_keywords:
            if keyword in category_text:
                return True

        # Check extract for biographical patterns
        bio_patterns = [
            r"\b(born|died|was|is)\b",
            r"\b\d{4}\s*[-–]\s*\d{4}\b",  # Birth-death year pattern
            r"\b(actor|actress|singer|musician|writer|author|politician|scientist)\b"
        ]

        for pattern in bio_patterns:
            if re.search(pattern, extract.lower()):
                return True

        return False

    def _extract_years(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Extract birth and death years from biographical text."""
        birth_year = None
        death_year = None

        # Pattern: (1990–2020) or (born 1990) or (1990 - 2020)
        year_range_pattern = r'\((?:born\s+)?(\d{4})\s*[-–]\s*(\d{4})\)'
        match = re.search(year_range_pattern, text)
        if match:
            birth_year = int(match.group(1))
            death_year = int(match.group(2))
            return birth_year, death_year

        # Pattern: (born 1990) or (b. 1990)
        born_pattern = r'\((?:born|b\.)\s+(\d{4})\)'
        match = re.search(born_pattern, text)
        if match:
            birth_year = int(match.group(1))
            return birth_year, None

        # Pattern: (1990-) for living people
        living_pattern = r'\((\d{4})\s*[-–]\s*\)'
        match = re.search(living_pattern, text)
        if match:
            birth_year = int(match.group(1))
            return birth_year, None

        return None, None

    def _extract_profession(self, extract: str, categories: List[str]) -> Optional[str]:
        """Extract profession from text and categories."""
        # Common profession keywords
        professions = {
            "actor": ["actor", "actress"],
            "musician": ["musician", "singer", "songwriter", "composer"],
            "writer": ["writer", "author", "novelist", "poet"],
            "politician": ["politician", "president", "senator", "congressman"],
            "scientist": ["scientist", "physicist", "chemist", "biologist"],
            "athlete": ["athlete", "footballer", "basketball", "baseball"],
            "director": ["director", "filmmaker"],
            "artist": ["artist", "painter", "sculptor"],
            "entrepreneur": ["entrepreneur", "businessman", "businesswoman"],
        }

        text_lower = extract.lower()

        for profession, keywords in professions.items():
            for keyword in keywords:
                if keyword in text_lower[:200]:  # Check first 200 chars
                    return profession.capitalize()

        # Check categories
        category_text = " ".join(categories).lower()
        for profession, keywords in professions.items():
            for keyword in keywords:
                if keyword in category_text:
                    return profession.capitalize()

        return None

    def _determine_category(self, categories: List[str], extract: str) -> str:
        """Determine if person is historical, celebrity, or fictional."""
        category_text = " ".join(categories).lower()
        extract_lower = extract.lower()

        # Check for fictional characters
        if "fictional" in category_text or "fictional character" in extract_lower:
            return "fictional"

        # Check for historical figures (died before 1950)
        death_year_match = re.search(r'died[^\d]*(\d{4})', extract_lower)
        if death_year_match:
            death_year = int(death_year_match.group(1))
            if death_year < 1950:
                return "historical"

        # Default to celebrity for modern people
        return "celebrity"

    def _extract_notable_achievement(self, extract: str) -> Optional[str]:
        """Extract a notable achievement or description."""
        # Get first sentence after name/birth info
        sentences = extract.split('.')
        if len(sentences) > 1:
            # Return second or third sentence (usually has key info)
            for sentence in sentences[1:3]:
                sentence = sentence.strip()
                if len(sentence) > 20 and not sentence.startswith('('):
                    return sentence[:200]  # Max 200 chars

        return None

    async def scrape_and_load_all_names(self, limit_per_name: int = 10):
        """
        Scrape famous people for all names in the database.

        Args:
            limit_per_name: Maximum number of famous people to find per name
        """
        logger.info("Starting Wikipedia famous people scraper for all names")

        # Setup database
        engine = create_async_engine(self.db_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        total_inserted = 0
        total_skipped = 0

        async with async_session() as session:
            # Get all names from database
            result = await session.execute(
                text("SELECT id, name FROM names ORDER BY name")
            )
            names = result.all()

            logger.info(f"Found {len(names)} names to process")

            for i, (name_id, name) in enumerate(names, 1):
                logger.info(f"[{i}/{len(names)}] Processing: {name}")

                # Check if we already have data for this name
                check_result = await session.execute(
                    text("SELECT COUNT(*) FROM famous_namesakes WHERE name_id = :name_id"),
                    {"name_id": name_id}
                )
                existing_count = check_result.scalar()

                if existing_count >= limit_per_name:
                    logger.info(f"  ⏭️  Already has {existing_count} famous people, skipping")
                    total_skipped += 1
                    continue

                # Search for famous people
                people = await self.search_famous_people(name, limit=limit_per_name)

                if not people:
                    logger.info(f"  ℹ️  No famous people found")
                    total_skipped += 1
                    continue

                # Insert each person
                inserted_for_name = 0
                for person in people:
                    try:
                        await session.execute(text("""
                            INSERT INTO famous_namesakes
                            (name_id, full_name, category, description, profession,
                             birth_year, death_year, notable_for, image_url, wikipedia_url)
                            VALUES (:name_id, :full_name, :category, :description, :profession,
                                    :birth_year, :death_year, :notable_for, :image_url, :wikipedia_url)
                            ON CONFLICT DO NOTHING
                        """), {
                            "name_id": name_id,
                            "full_name": person["full_name"],
                            "category": person["category"],
                            "description": person["description"],
                            "profession": person["profession"],
                            "birth_year": person["birth_year"],
                            "death_year": person["death_year"],
                            "notable_for": person["notable_for"],
                            "image_url": person["image_url"],
                            "wikipedia_url": person["wikipedia_url"],
                        })
                        inserted_for_name += 1
                    except Exception as e:
                        logger.error(f"  ❌ Error inserting {person['full_name']}: {e}")

                # Update has_famous_people flag
                if inserted_for_name > 0:
                    await session.execute(
                        text("UPDATE names SET has_famous_people = TRUE WHERE id = :name_id"),
                        {"name_id": name_id}
                    )
                    await session.commit()
                    total_inserted += inserted_for_name
                    logger.info(f"  ✅ Inserted {inserted_for_name} famous people")
                else:
                    total_skipped += 1

                # Rate limiting between names
                await asyncio.sleep(self.RATE_LIMIT_DELAY)

        await engine.dispose()

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Wikipedia Famous People Scraper Complete!")
        logger.info(f"   Names processed: {len(names)}")
        logger.info(f"   Total famous people inserted: {total_inserted:,}")
        logger.info(f"   Names skipped: {total_skipped}")
        logger.info(f"{'='*60}\n")

        return total_inserted, total_skipped


async def main():
    """Run the Wikipedia famous people scraper."""
    async with WikipediaFamousPeopleScraper() as scraper:
        # Scrape for all names
        await scraper.scrape_and_load_all_names(limit_per_name=10)


if __name__ == "__main__":
    asyncio.run(main())
