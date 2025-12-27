"""
IMDb Scraper
Extracts famous people and fictional characters from IMDb.
Uses Cinemagoer (IMDbPY) library with rate limiting.
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
import re

from imdb import Cinemagoer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IMDbScraper:
    """Scraper for IMDb using Cinemagoer library."""

    RATE_LIMIT_DELAY = 1.0  # 1 second between requests

    def __init__(self, db_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db"):
        self.db_url = db_url
        self.ia = Cinemagoer()

    async def search_people_by_name(self, name: str, limit: int = 10) -> List[Dict]:
        """
        Search for real people on IMDb with the given name.

        Args:
            name: The name to search for
            limit: Maximum number of results to return

        Returns:
            List of person data dictionaries
        """
        logger.info(f"Searching IMDb for people named: {name}")

        await asyncio.sleep(self.RATE_LIMIT_DELAY)

        try:
            # Search for people with this name
            results = self.ia.search_person(name)

            people_data = []

            for person in results[:limit]:
                try:
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)

                    # Get full person data
                    self.ia.update(person, info=['main', 'biography'])

                    # Extract birth and death years
                    birth_year = None
                    death_year = None

                    if 'birth date' in person:
                        birth_match = re.search(r'\b(19|20)\d{2}\b', person['birth date'])
                        if birth_match:
                            birth_year = int(birth_match.group(0))

                    if 'death date' in person:
                        death_match = re.search(r'\b(19|20)\d{2}\b', person['death date'])
                        if death_match:
                            death_year = int(death_match.group(0))

                    # Determine profession (actor, director, etc.)
                    profession = "Unknown"
                    if 'filmography' in person:
                        filmography = person.get('filmography', {})
                        if 'actor' in filmography or 'actress' in filmography:
                            profession = "Actor"
                        elif 'director' in filmography:
                            profession = "Director"
                        elif 'writer' in filmography:
                            profession = "Writer"
                        elif 'producer' in filmography:
                            profession = "Producer"

                    # Check if the first name matches our search
                    person_name = person.get('name', '')
                    first_name = person_name.split()[0] if person_name else ''

                    # Only include if first name matches (case-insensitive)
                    if first_name.lower() == name.lower():
                        imdb_url = f"https://www.imdb.com/name/nm{person.personID}/"

                        people_data.append({
                            'full_name': person_name,
                            'category': 'real',
                            'profession': profession,
                            'birth_year': birth_year,
                            'death_year': death_year,
                            'source_url': imdb_url,
                        })

                        logger.info(f"  Found: {person_name} ({profession})")

                except Exception as e:
                    logger.error(f"  Error processing person {person}: {e}")
                    continue

            return people_data

        except Exception as e:
            logger.error(f"  Error searching for people named '{name}': {e}")
            return []

    async def search_characters_by_name(self, name: str, limit: int = 10) -> List[Dict]:
        """
        Search for fictional characters on IMDb with the given name.

        Args:
            name: The character name to search for
            limit: Maximum number of results to return

        Returns:
            List of character data dictionaries
        """
        logger.info(f"Searching IMDb for characters named: {name}")

        await asyncio.sleep(self.RATE_LIMIT_DELAY)

        try:
            # Search for characters with this name
            results = self.ia.search_character(name)

            characters_data = []

            for character in results[:limit]:
                try:
                    await asyncio.sleep(self.RATE_LIMIT_DELAY)

                    # Get character details
                    character_name = character.get('name', character.get('long imdb canonical name', ''))

                    # Extract the first name from the character
                    first_name = character_name.split()[0] if character_name else ''

                    # Only include if first name matches (case-insensitive)
                    if first_name.lower() == name.lower():
                        # Try to get the movie/show this character is from
                        filmography = character.get('filmography', [])
                        show_name = "Unknown"

                        if filmography and len(filmography) > 0:
                            # Get the first/most famous appearance
                            first_appearance = filmography[0]
                            if 'title' in first_appearance:
                                show_name = first_appearance['title']

                        imdb_url = f"https://www.imdb.com/character/ch{character.characterID}/"

                        characters_data.append({
                            'full_name': character_name,
                            'category': 'fictional',
                            'profession': f"Character from {show_name}",
                            'birth_year': None,
                            'death_year': None,
                            'source_url': imdb_url,
                        })

                        logger.info(f"  Found character: {character_name} from {show_name}")

                except Exception as e:
                    logger.error(f"  Error processing character {character}: {e}")
                    continue

            return characters_data

        except Exception as e:
            logger.error(f"  Error searching for characters named '{name}': {e}")
            return []

    async def save_to_database(
        self,
        name_id: int,
        people_data: List[Dict],
        session: AsyncSession
    ):
        """Save IMDb data to the database."""

        try:
            for person in people_data:
                # Check if this person already exists (by source_url)
                result = await session.execute(
                    text("""
                        SELECT id FROM famous_namesakes
                        WHERE source_url = :source_url
                    """),
                    {'source_url': person['source_url']}
                )

                existing = result.first()

                if not existing:
                    # Insert new record
                    await session.execute(text("""
                        INSERT INTO famous_namesakes (
                            name_id, full_name, category, profession,
                            birth_year, death_year, source_url
                        )
                        VALUES (
                            :name_id, :full_name, :category, :profession,
                            :birth_year, :death_year, :source_url
                        )
                    """), {
                        'name_id': name_id,
                        'full_name': person['full_name'],
                        'category': person['category'],
                        'profession': person['profession'],
                        'birth_year': person['birth_year'],
                        'death_year': person['death_year'],
                        'source_url': person['source_url'],
                    })

            await session.commit()
            return True

        except Exception as e:
            logger.error(f"  Error saving to database: {e}")
            await session.rollback()
            return False

    async def scrape_and_update_all_names(self, people_limit: int = 5, characters_limit: int = 5):
        """Scrape IMDb data for all names in the database."""
        logger.info("Starting IMDb scraper for all names")

        # Setup database
        engine = create_async_engine(self.db_url, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        total_people = 0
        total_characters = 0
        total_names_processed = 0

        async with async_session() as session:
            # Get all names from database
            result = await session.execute(
                text("SELECT id, name FROM names ORDER BY name")
            )
            names = result.all()

            logger.info(f"Found {len(names)} names to process")

            for i, (name_id, name) in enumerate(names, 1):
                logger.info(f"[{i}/{len(names)}] Processing: {name}")

                # Search for real people
                people_data = await self.search_people_by_name(name, limit=people_limit)

                # Search for fictional characters
                characters_data = await self.search_characters_by_name(name, limit=characters_limit)

                # Combine results
                all_data = people_data + characters_data

                if all_data:
                    # Save to database
                    success = await self.save_to_database(name_id, all_data, session)

                    if success:
                        total_people += len(people_data)
                        total_characters += len(characters_data)
                        total_names_processed += 1
                        logger.info(f"  ✅ Added {len(people_data)} people, {len(characters_data)} characters")
                    else:
                        logger.warning(f"  ⚠️  Failed to save data for {name}")
                else:
                    logger.info(f"  ℹ️  No results found for {name}")

        await engine.dispose()

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ IMDb Scraper Complete!")
        logger.info(f"   Names processed: {total_names_processed}/{len(names)}")
        logger.info(f"   Total real people: {total_people}")
        logger.info(f"   Total fictional characters: {total_characters}")
        logger.info(f"   Total entries: {total_people + total_characters}")
        logger.info(f"{'='*60}\n")

        return total_people, total_characters


async def main():
    """Run the IMDb scraper."""
    scraper = IMDbScraper()
    await scraper.scrape_and_update_all_names(
        people_limit=5,  # Max 5 real people per name
        characters_limit=5  # Max 5 fictional characters per name
    )


if __name__ == "__main__":
    asyncio.run(main())
