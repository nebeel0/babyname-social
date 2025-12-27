# Baby Names Social Network - Backend

FastAPI backend for the Baby Names Social Network application.

## Quick Start

```bash
# Start backend with hot reload
uv run fastapi dev app/main.py --port 8001

# API Documentation
# http://localhost:8001/docs
```

## Project Structure

```
apps/backend/
├── app/                    # FastAPI application
│   ├── api/v1/            # API endpoints
│   │   ├── endpoints/
│   │   │   ├── names.py          # Name CRUD
│   │   │   ├── preferences.py    # User favorites/ratings
│   │   │   └── enrichment.py     # Famous people, trends, trivia
│   │   └── router.py
│   ├── auth/              # Authentication (fastapi-users)
│   └── main.py            # App entry point
├── db/                    # Database layer
│   ├── models/            # SQLAlchemy models
│   ├── migrations/        # SQL migrations
│   └── base.py            # Database sessions
├── scrapers/              # Data collection scripts
│   ├── ssa_scraper.py           # US SSA popularity data (1880-2023)
│   └── wikipedia_scraper.py     # Famous people via MediaWiki API
├── scripts/               # Utility scripts
│   ├── seed_names.py              # Load initial 80 names
│   └── add_sample_enrichment_data.py
├── data/                  # Seed data files
│   └── baby_names.json
└── docs/                  # Documentation
    └── SCRAPING_STRATEGY.md     # Data collection plan
```

## Data Scrapers

### Location
All scrapers are in `/apps/backend/scrapers/` and can be run directly with `uv run python scrapers/<scraper_name>.py`

### SSA Scraper (`scrapers/ssa_scraper.py`)

Imports historical baby name popularity data from the US Social Security Administration.

**Data Source**: https://www.ssa.gov/oact/babynames/names.zip (Public Domain)

**What it does**:
- Downloads 140+ years of data (1880-2023)
- Imports ~2 million trend records
- Calculates rankings within each gender per year
- Updates `popularity_trends` table

**Run it**:
```bash
cd apps/backend
uv run python scrapers/ssa_scraper.py
```

**Time**: ~5-10 minutes (downloads ~2MB ZIP, processes all years)

**Database impact**:
- Table: `popularity_trends`
- Records added: ~2,000,000
- Updates: `names.has_trends = TRUE`

**Example data**:
```
name_id=1, year=2023, rank=1, count=15,000, gender='female', source='SSA'
name_id=1, year=2022, rank=2, count=14,500, gender='female', source='SSA'
...
```

### Wikipedia Scraper (`scrapers/wikipedia_scraper.py`)

Finds famous people for each name using Wikipedia's official API.

**Data Source**: Wikipedia MediaWiki API (https://en.wikipedia.org/w/api.php)

**What it does**:
- Searches for notable people with each name
- Extracts: full name, profession, birth/death years, achievements
- Categorizes: celebrity, historical, fictional
- Inserts into `famous_namesakes` table

**Run it**:
```bash
cd apps/backend
uv run python scrapers/wikipedia_scraper.py
```

**Time**: ~2-3 hours (respectful rate limiting: 1.5s between requests)

**Database impact**:
- Table: `famous_namesakes`
- Records added: ~500-800 (up to 10 per name)
- Updates: `names.has_famous_people = TRUE`

**Rate Limiting**:
- 1.5 seconds between all Wikipedia API requests
- Compliant with Wikipedia's Terms of Service
- User-Agent: "BabyNamesSocialApp/1.0"

**Example data**:
```
name_id=1, full_name='Emma Watson', category='celebrity',
profession='Actor', birth_year=1990,
wikipedia_url='https://en.wikipedia.org/wiki/Emma_Watson'
```

### Running Multiple Scrapers

You can run scrapers in parallel (they use different data sources):

```bash
# Terminal 1
uv run python scrapers/ssa_scraper.py

# Terminal 2
uv run python scrapers/wikipedia_scraper.py
```

Or run in background:
```bash
uv run python scrapers/ssa_scraper.py > logs/ssa.log 2>&1 &
uv run python scrapers/wikipedia_scraper.py > logs/wiki.log 2>&1 &
```

## Database Management

### Migrations

```bash
# Apply migration
docker exec -i babynames_db psql -U postgres -d babynames_db < db/migrations/002_add_enrichment_tables.sql

# Connect to database
docker exec -it babynames_db psql -U postgres -d babynames_db
```

### Seeding Data

```bash
# Load 80 initial baby names
uv run python scripts/seed_names.py

# Add sample enrichment data
uv run python scripts/add_sample_enrichment_data.py
```

## API Endpoints

### Names
- `GET /api/v1/names/` - List all names
- `GET /api/v1/names/{id}` - Get single name
- `POST /api/v1/names/` - Create name
- `PUT /api/v1/names/{id}` - Update name
- `DELETE /api/v1/names/{id}` - Delete name

### Enrichment
- `GET /api/v1/enrichment/{name_id}/trends` - Popularity trends
- `GET /api/v1/enrichment/{name_id}/famous-people` - Famous namesakes
- `GET /api/v1/enrichment/{name_id}/trivia` - Fun facts
- `GET /api/v1/enrichment/stats/overview` - Overall statistics

### Preferences
- `GET /api/v1/preferences/` - User's favorites/ratings
- `POST /api/v1/preferences/` - Add favorite/rating
- `DELETE /api/v1/preferences/{id}` - Remove favorite

## Environment Variables

See `.env` file:
```
# Database
NAMES_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5434/babynames_db
USERS_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/babynames_users_db

# Redis
REDIS_CACHE_URL=redis://localhost:6379/0
REDIS_SESSION_URL=redis://localhost:6380/0

# API
API_PORT=8001
CORS_ORIGINS=["http://localhost:5173"]
```

## Development

### Hot Reload
FastAPI dev mode watches for file changes:
```bash
uv run fastapi dev app/main.py --port 8001
```

### Testing Endpoints
```bash
# Get all names
curl http://localhost:8001/api/v1/names/

# Get famous people for name ID 1
curl http://localhost:8001/api/v1/enrichment/1/famous-people

# Get popularity trends for name ID 1
curl http://localhost:8001/api/v1/enrichment/1/trends
```

## Dependencies

Managed via UV (pyproject.toml):
- FastAPI 0.126+
- SQLAlchemy 2.0 (async)
- httpx (async HTTP client for scrapers)
- fastapi-users (authentication)

## Docker Services

The backend uses these Docker services (see `docker-compose.yml`):
- `babynames_db` - PostgreSQL 17 (names database) - Port 5434
- `babynames_users_db` - PostgreSQL 17 (users database) - Port 5433
- `babynames_redis_cache` - Redis (caching) - Port 6379
- `babynames_redis_sessions` - Redis (sessions) - Port 6380

## Ethical Data Collection

All scrapers follow ethical guidelines:
- ✅ Respect robots.txt
- ✅ Rate limiting (1-3 sec between requests)
- ✅ Use official APIs where available
- ✅ Attribution and source tracking
- ✅ Public domain data prioritized
- ✅ No personal data collection

See `docs/SCRAPING_STRATEGY.md` for full strategy.

## Troubleshooting

### Port conflicts
If port 8001 is in use:
```bash
# Change port in .env
API_PORT=8002

# Or override:
uv run fastapi dev app/main.py --port 8002
```

### Database connection errors
```bash
# Check Docker containers are running
docker ps | grep babynames

# Restart if needed
docker-compose restart
```

### Scraper issues
```bash
# Check internet connectivity
curl -I https://www.ssa.gov

# Check database connection
docker exec -it babynames_db psql -U postgres -d babynames_db -c "SELECT COUNT(*) FROM names;"
```

## See Also

- Main project README: `../../README.md`
- Scraping strategy: `docs/SCRAPING_STRATEGY.md`
- Progress summary: `../../PROGRESS_SUMMARY.md`
