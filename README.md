# Baby Names Social Network - Universe 1

A full-stack social network for discovering, analyzing, and sharing baby names with comprehensive historical, cultural, and statistical data.

## Architecture

### Monorepo Structure
```
universe1/
├── apps/
│   ├── backend/        # FastAPI application
│   └── frontend/       # Flutter application (TODO)
├── docker-compose.yml  # Development infrastructure
├── Makefile           # Development commands
└── README.md          # This file
```

### Tech Stack

**Backend:**
- FastAPI 0.115+ (Modern Python web framework)
- UV (Fast package manager)
- PostgreSQL 16 (Dual database: names + users)
- Redis 7 (Dual instance: cache + sessions)
- SQLAlchemy 2.0 (Async ORM)
- fastapi-users (Authentication)
- Alembic (Database migrations)

**Frontend (Coming Soon):**
- Flutter 3.7+
- Riverpod 2.x (State management)
- OpenAPI Generator (Auto-generated API client)

### Database Architecture

**Dual Database Design:**
1. `babynames_db` (Port 5432): Names, popularity data, cultural info
2. `users_db` (Port 5433): User accounts, authentication

**Dual Redis Design:**
1. `redis_cache` (Port 6379): LRU cache, no persistence
2. `redis_sessions` (Port 6380): Session storage, persistent

### Data Models

**Names Database:**
- `names` - Core name entity with etymology, meanings, origins
- `popularity_history` - Time-series popularity data by region/year
- `name_variants` - Spelling variations, translations, diminutives
- `famous_references` - Historical figures, celebrities, fictional characters
- `cultural_contexts` - Religious, mythological, traditional significance
- `user_name_preferences` - User favorites, ratings, lists
- `comments` - User reviews and comments

**Users Database:**
- `users` - Authentication and profile data (via fastapi-users)

## Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- UV package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Make

### Installation

1. **Install dependencies:**
   ```bash
   make install-backend
   ```

2. **Start infrastructure (databases, Redis):**
   ```bash
   make build
   ```

   This starts:
   - PostgreSQL (names) on `localhost:5432`
   - PostgreSQL (users) on `localhost:5433`
   - Redis (cache) on `localhost:6379`
   - Redis (sessions) on `localhost:6380`
   - PgAdmin on `http://localhost:5050`

3. **Initialize databases:**
   ```bash
   cd apps/backend
   uv run python -c "from db.base import Base, names_engine, users_engine; from db.models import *; from db.models.user import User; import asyncio; asyncio.run(Base.metadata.create_all(names_engine)); asyncio.run(Base.metadata.create_all(users_engine))"
   ```

4. **Start backend:**
   ```bash
   make dev
   ```

   Backend runs on `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - OpenAPI spec: `http://localhost:8000/openapi.json`

## Development Commands

### Common Tasks

```bash
make help              # Show all available commands
make dev               # Start backend dev server
make build             # Start Docker services (DB, Redis)
make down              # Stop all services
make clean             # Remove all containers & volumes (DESTRUCTIVE!)
```

### Code Quality

```bash
make lint              # Run all linters (black, ruff, mypy)
make format            # Auto-format code
make test              # Run tests
```

### Database

```bash
make db-init           # Create all database tables
make db-migrate        # Run Alembic migrations
make db-revision       # Create new migration
make pgadmin           # Open PgAdmin UI
```

### API Development

```bash
make docs              # Open API docs (Swagger UI)
make generate-api      # Generate Dart client from OpenAPI
```

## API Endpoints

### Authentication (fastapi-users)
- `POST /auth/register` - Register new user
- `POST /auth/jwt/login` - Login (returns JWT)
- `POST /auth/jwt/logout` - Logout
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password
- `POST /auth/request-verify-token` - Request email verification
- `POST /auth/verify` - Verify email

### Names (v1)
- `GET /api/v1/names` - List names (paginated)
- `GET /api/v1/names/{id}` - Get name details
- `POST /api/v1/names` - Create name (admin)
- `GET /api/v1/names/search/{query}` - Search names

## Database Schema

### Key Tables

**names**
- Comprehensive name data (etymology, meaning, origins)
- Aggregate statistics (avg_rating, trending_score)
- Phonetic characteristics

**popularity_history**
- Time-series data optimized for analytics
- Geographic breakdown (country, state, city)
- Multiple metrics (rank, count, percentage, per_100k)

**famous_references**
- Historical figures, celebrities, fictional characters
- Biographical data, source media info
- External links (Wikipedia, IMDb)

## Architecture Decisions

### Why Dual Databases?
- **Security**: Auth data isolated from business data
- **Scaling**: Independent scaling strategies
- **Backup**: Different backup/retention policies

### Why Dual Redis?
- **Cache**: LRU eviction, no persistence, optimized for speed
- **Sessions**: Persistent, no eviction, data integrity

### Why Repository Pattern?
- **Testability**: Easy to mock data layer
- **DRY**: Reusable query logic
- **Caching**: Centralized caching layer

### Why UV over Poetry?
- **Speed**: 10-100x faster
- **Modern**: Industry momentum, future-proof
- **Compatibility**: Standard `pyproject.toml`

## Next Steps

- [ ] Add Alembic migrations
- [ ] Implement repository layer
- [ ] Add caching decorators
- [ ] Create trending calculation service
- [ ] Set up Flutter frontend with Riverpod
- [ ] Configure OpenAPI code generation
- [ ] Add comprehensive tests
- [ ] Implement data import scripts (SSA, ONS data)
- [ ] Add Elasticsearch for full-text search
- [ ] Create admin dashboard

## Project Status

**Current Phase:** Backend Foundation ✅
- ✅ Project structure
- ✅ Database models
- ✅ FastAPI application
- ✅ Authentication (fastapi-users)
- ✅ Basic API endpoints
- ✅ Docker Compose setup
- ✅ Makefile commands

**Next Phase:** Frontend Setup
- [ ] Flutter app scaffold
- [ ] Riverpod state management
- [ ] OpenAPI client generation
- [ ] Basic UI components

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [fastapi-users Guide](https://fastapi-users.github.io/fastapi-users/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Flutter Documentation](https://flutter.dev/)
- [Riverpod](https://riverpod.dev/)

## License

TBD
