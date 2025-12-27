# Baby Names Data Scraping Strategy

## Overview
Multi-source scraping strategy to build a comprehensive baby names database with enriched data including popularity trends, famous namesakes, and cultural significance.

## Data Sources

### 1. **US Social Security Administration (SSA)** ⭐ Primary Source
- **URL**: https://www.ssa.gov/oact/babynames/
- **Data Available**:
  - Top 1000 names per year (1880-2023)
  - Gender breakdown
  - Annual popularity rankings
  - State-by-state data
- **Format**: CSV/TXT files (public domain)
- **Legality**: ✅ Public data, explicitly allowed
- **Update Frequency**: Annually (May)
- **Implementation**: Direct download + parse

### 2. **Behind the Name** 🌍 Etymology & Meanings
- **URL**: https://www.behindthename.com/
- **Data Available**:
  - Etymology and meaning
  - Language origins
  - Historical usage
  - Related names
  - Famous bearers
- **Format**: HTML scraping
- **Legality**: ⚠️ Check robots.txt, rate limit required
- **Rate Limit**: 1 request per 2 seconds
- **Implementation**: Beautiful Soup + respectful crawling

### 3. **Wikipedia** 📚 Famous People
- **URL**: https://en.wikipedia.org/
- **Data Available**:
  - People with the name (via category pages)
  - Historical figures
  - Fictional characters
  - Brief descriptions
- **Format**: MediaWiki API
- **Legality**: ✅ API available, CC-BY-SA license
- **Rate Limit**: No hard limit, but be respectful
- **Implementation**: Use Wikipedia API, not scraping

### 4. **BabyCenter** 📊 Modern Trends
- **URL**: https://www.babycenter.com/baby-names
- **Data Available**:
  - User ratings and reviews
  - Sibling name suggestions
  - Celebrity baby names
  - Modern popularity
- **Format**: HTML scraping
- **Legality**: ⚠️ Review ToS
- **Rate Limit**: 1 request per 3 seconds
- **Implementation**: Selenium (JS-heavy site)

### 5. **Nameberry** 💎 Premium Context
- **URL**: https://nameberry.com/
- **Data Available**:
  - Name meanings
  - Celebrity usage
  - Style categories
  - Popularity predictions
- **Format**: HTML scraping
- **Legality**: ⚠️ Review ToS
- **Implementation**: Requests + BeautifulSoup

### 6. **IMDb** 🎬 Fictional Characters
- **URL**: https://www.imdb.com/
- **Data Available**:
  - Character names from movies/TV
  - Actor names
  - Popularity of fictional namesakes
- **Format**: IMDb API (non-commercial)
- **Legality**: ⚠️ Limited use, check licensing
- **Implementation**: IMDbPY library

## Database Schema Extensions

### New Tables

```sql
-- Famous people/characters associated with names
CREATE TABLE famous_namesakes (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id),
    full_name VARCHAR(255) NOT NULL,
    category VARCHAR(50), -- 'historical', 'celebrity', 'fictional', 'athlete', etc.
    description TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    profession VARCHAR(100),
    notable_for TEXT,
    image_url VARCHAR(500),
    wikipedia_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Popularity trends over time
CREATE TABLE popularity_trends (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id),
    year INTEGER NOT NULL,
    rank INTEGER,
    count INTEGER,
    gender VARCHAR(20),
    country VARCHAR(2) DEFAULT 'US',
    source VARCHAR(50) DEFAULT 'SSA',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name_id, year, gender, country)
);

-- Related/similar names
CREATE TABLE related_names (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id),
    related_name_id INTEGER REFERENCES names(id),
    relationship_type VARCHAR(50), -- 'variant', 'diminutive', 'similar', 'rhymes'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Name metadata and trivia
CREATE TABLE name_trivia (
    id SERIAL PRIMARY KEY,
    name_id INTEGER REFERENCES names(id),
    trivia_type VARCHAR(50), -- 'fact', 'quote', 'tradition', 'superstition'
    content TEXT NOT NULL,
    source VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Scraper Architecture

### Directory Structure
```
apps/backend/scrapers/
├── __init__.py
├── base_scraper.py           # Abstract base class
├── ssa_scraper.py            # SSA data downloader
├── behindthename_scraper.py  # Etymology scraper
├── wikipedia_scraper.py      # Famous people via API
├── imdb_scraper.py           # Fictional characters
└── utils/
    ├── rate_limiter.py
    ├── cache.py
    └── validators.py
```

### Base Scraper Class
```python
from abc import ABC, abstractmethod
from typing import Dict, List
import time
import logging

class BaseScraper(ABC):
    def __init__(self, rate_limit_seconds: float = 1.0):
        self.rate_limit = rate_limit_seconds
        self.last_request = 0
        self.logger = logging.getLogger(self.__class__.__name__)

    def wait_for_rate_limit(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()

    @abstractmethod
    async def scrape_name(self, name: str) -> Dict:
        """Scrape data for a single name"""
        pass

    @abstractmethod
    async def scrape_batch(self, names: List[str]) -> List[Dict]:
        """Scrape data for multiple names"""
        pass
```

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. ✅ SSA Historical Data (1880-2023)
   - Download all years
   - Parse and load into popularity_trends table
   - ~2M records

2. ✅ Wikipedia Famous People
   - Use MediaWiki API
   - Category: "People named [X]"
   - Extract top 10 per name

### Phase 2: Etymology (Week 2)
3. Behind the Name scraper
   - Meanings and origins
   - Historical context
   - Related names

### Phase 3: Enrichment (Week 3)
4. IMDb fictional characters
5. Name trivia and facts
6. Modern trends from BabyCenter

## Ethical & Legal Considerations

### Compliance Checklist
- ✅ Check robots.txt for each site
- ✅ Implement respectful rate limiting
- ✅ Include User-Agent header
- ✅ Cache responses to avoid re-scraping
- ✅ Attribute data sources
- ✅ Review ToS for each platform
- ✅ Use APIs where available

### Rate Limiting
```python
RATE_LIMITS = {
    'ssa.gov': 0,  # No limit, public files
    'behindthename.com': 2.0,  # 2 seconds between requests
    'wikipedia.org': 0.5,  # 500ms via API
    'babycenter.com': 3.0,  # 3 seconds
    'nameberry.com': 2.0,  # 2 seconds
    'imdb.com': 1.0,  # 1 second
}
```

### Caching Strategy
- Redis cache for API responses (24 hour TTL)
- PostgreSQL for permanent storage
- File cache for large downloads (SSA datasets)

## Data Quality

### Validation Rules
- Name must be 2-50 characters
- Verify Unicode normalization
- Check for duplicates before insert
- Validate year ranges (1880-2024)
- Clean HTML entities
- Remove advertisements/tracking

### Deduplication
- Fuzzy matching for similar entries
- Canonical name resolution
- Multiple spellings handling

## Monitoring

### Metrics to Track
- Scrape success rate
- Average request duration
- Error rate by source
- Data coverage (% of names enriched)
- Last update timestamp

### Alerts
- Rate limit violations
- Scraper failures
- Data quality issues
- Site structure changes

## Usage Example

```python
from scrapers.ssa_scraper import SSAScraper
from scrapers.wikipedia_scraper import WikipediaScraper

# Scrape SSA data
ssa = SSAScraper()
await ssa.download_all_years()
await ssa.load_to_database()

# Enrich with famous people
wiki = WikipediaScraper()
for name in top_100_names:
    famous_people = await wiki.get_famous_people(name)
    await db.save_famous_namesakes(name, famous_people)
```

## Next Steps

1. Implement SSA scraper (highest ROI)
2. Create database migrations for new tables
3. Build Wikipedia API integration
4. Update frontend to display trends and famous people
5. Schedule periodic updates (cron jobs)
