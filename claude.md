# Claude Context - Baby Names Social Network (Universe 1)

> **Purpose**: This file provides comprehensive context for AI assistants (Claude) working on this project. It includes architecture, current state, conventions, and important locations.

**Last Updated**: 2025-12-22

## Project Overview

A full-stack social network for discovering, analyzing, and sharing baby names with comprehensive historical, cultural, and statistical data.

**Tech Stack:**
- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Redis 7
- **Frontend**: Flutter 3.8+ + Riverpod 2.x + go_router
- **Infrastructure**: Docker Compose for local development
- **Package Management**: UV (backend), Flutter pub (frontend)

## Repository Structure

```
universe1/
├── apps/
│   ├── backend/              # FastAPI application
│   │   ├── app/             # Application code
│   │   │   ├── main.py      # FastAPI app entry point
│   │   │   ├── api/v1/      # API routes
│   │   │   ├── db/          # Database models & config
│   │   │   └── core/        # Settings, dependencies
│   │   ├── pyproject.toml   # Python dependencies (UV)
│   │   └── .env            # Backend environment vars
│   └── frontend/            # Flutter application
│       ├── lib/
│       │   ├── main.dart    # Flutter entry point
│       │   ├── core/        # Models, routing, theme
│       │   │   └── models/  # UserProfile, NameEnhancements
│       │   ├── features/    # Feature-based modules
│       │   │   ├── names/   # Name browsing, search, comparison
│       │   │   └── profile/ # User profile management
│       │   └── shared/      # Shared widgets, utils
│       ├── pubspec.yaml     # Flutter dependencies
│       └── openapi_generator_config.json  # API client generation config
├── scripts/
│   ├── generate_ports.py    # Port management automation
│   └── README.md            # Port management documentation
├── docker-compose.yml       # Development services
├── .env                     # Infrastructure ports
├── Makefile                 # Development commands
└── claude.md               # This file
```

## Current State (As of 2025-12-22)

### ✅ Completed
- **Backend**:
  - FastAPI application running on port 8001
  - Dual database architecture (names_db, users_db)
  - Dual Redis instances (cache, sessions)
  - Basic CRUD endpoints for names
  - Authentication system (fastapi-users) - partially implemented
  - Database models for names, popularity, variants, famous references

- **Frontend**:
  - Flutter app running on port 5173
  - Names list screen with grid/list view
  - Filtering (gender, origin, era)
  - Name comparison feature (select up to 4 names)
  - Favorites system (local storage via SharedPreferences)
  - Name detail modal
  - Add/Edit name dialogs
  - Profile settings screen (stub)

- **Infrastructure**:
  - Docker Compose setup for PostgreSQL + Redis + PgAdmin
  - Port conflict resolution system
  - Automated port generation script

### 🚧 In Progress / Needs Work
- **OpenAPI Code Generation**: Not yet configured
  - Config file exists but no generated code
  - Currently using manual Dio HTTP calls
  - Location for generated code: `lib/generated/api/` (when implemented)

- **Backend API**:
  - Running on port 8001 (non-standard)
  - Missing many endpoints from README

- **Authentication**:
  - Backend has fastapi-users configured
  - Frontend has no authentication implementation yet

### ❌ Not Started
- Profile onboarding flow
- User-specific name preferences
- Popularity charts
- Name trends analysis
- Social features (comments, sharing)

## Port Configuration

### Current Ports (.env)
```
POSTGRES_NAMES_PORT=15434
POSTGRES_USERS_PORT=15433
REDIS_CACHE_PORT=16381
REDIS_SESSIONS_PORT=16382
PGADMIN_PORT=15050
BACKEND_PORT=8000    # NOTE: Actually running on 8001
FRONTEND_PORT=5173
```

### Port Management
- **Script**: `scripts/generate_ports.py`
- **Purpose**: Auto-generates available ports to avoid conflicts
- **Usage**: `python scripts/generate_ports.py [--dry-run|--fresh]`
- **Documentation**: See `scripts/README.md`

**Important**: Ports were moved to high ranges (15000+) to avoid conflicts with other Docker-based projects (e.g., landbridge, impromptu).

## Key Files & Their Purposes

### Backend (`apps/backend/`)

**Configuration**:
- `core/settings.py` - Pydantic settings, database URLs, environment variables
  - Uses POSTGRES_NAMES_PORT and POSTGRES_USERS_PORT from .env
  - Has backward compatibility properties (NAMES_DB_PORT, USERS_DB_PORT)

**Database**:
- `db/base.py` - Database engines, session management
- `db/models/` - SQLAlchemy models
  - `name.py` - Main name model with variants, references, etc.
  - `user.py` - User authentication model
  - `user_profile.py` - User preferences for name recommendations

**API**:
- `api/v1/endpoints/names.py` - Name CRUD endpoints
- `api/v1/endpoints/auth.py` - Authentication endpoints (fastapi-users)

### Frontend (`apps/frontend/`)

**Core**:
- `lib/main.dart` - App entry point, routing configuration
- `lib/core/models/user_profile.dart` - User profile data model
  - Fields: ethnicity, age, location, preferences (1-5 scales)
  - Note: Model field names vs screen expectations (fixed on 2025-12-22)

**Features**:
- `lib/features/names/screens/names_list_screen.dart` - Main name browsing UI
  - Direct Dio HTTP calls to `http://localhost:8001/api/v1/names/`
  - Grid/list view modes
  - Filtering, search, comparison mode

- `lib/features/names/screens/name_comparison_screen.dart` - Compare names side-by-side

- `lib/features/profile/screens/profile_settings_screen.dart` - User profile view
  - Uses `userProfileProvider` (currently returns null)

**Providers**:
- `lib/features/profile/providers/user_profile_provider.dart` - Riverpod provider for user profile
  - Currently a stub returning null
  - TODO: Implement actual API integration

## Database Schema

### Names Database (`babynames_db` on port 15434)

**Main Tables**:
- `names` - Core name data (etymology, meaning, gender, origin)
- `popularity_history` - Time-series popularity data
- `name_variants` - Spelling variations, translations
- `famous_references` - Historical figures, celebrities with this name
- `cultural_contexts` - Religious/cultural significance
- `user_name_preferences` - User favorites, ratings, custom lists
- `comments` - User reviews

### Users Database (`users_db` on port 15433)

**Tables**:
- `users` - fastapi-users authentication
- `user_profiles` - Personalization preferences

## Development Workflow

### Starting the Project

```bash
# From universe1/ directory

# 1. Start infrastructure
docker compose up -d

# 2. Start backend (port 8001)
cd apps/backend
uv run fastapi dev app/main.py --port 8001

# 3. Start frontend (port 5173)
cd apps/frontend
flutter run -d chrome --web-port=5173
```

### Common Tasks

```bash
# Backend
cd apps/backend
uv run fastapi dev app/main.py --port 8001  # Dev server
uv add package-name                         # Add dependency
uv run pytest                               # Run tests

# Frontend
cd apps/frontend
flutter pub get                             # Install dependencies
flutter run -d chrome --web-port=5173       # Run on Chrome
flutter pub run build_runner build          # Generate code (.g.dart files)

# Database
docker exec -it babynames_db psql -U postgres -d babynames_db
docker exec -it babynames_users_db psql -U postgres -d users_db

# Port management
python scripts/generate_ports.py            # Generate new ports
docker compose down && docker compose up -d # Apply new ports
```

## Important Patterns & Conventions

### Backend
- **Async everywhere**: All database operations are async
- **Repository pattern**: Planned but not yet implemented
- **Pydantic models**: Request/response validation
- **Dual database**: Names data separate from user data

### Frontend
- **Feature-based structure**: Group by feature, not by type
- **Riverpod for state**: FutureProvider, StateNotifierProvider
- **go_router for navigation**: Declarative routing
- **Material Design 3**: Modern Flutter UI

### API Communication
- **Currently**: Direct Dio calls
- **Future**: OpenAPI-generated client
- **Base URL**: `http://localhost:8001/api/v1/`

## Recent Changes & Fixes (2025-12-22)

1. **Port Conflict Resolution**:
   - Moved all ports to high ranges (15000-16999)
   - Created automated port generation script
   - Stopped conflicting `impromptu_db` container
   - Baby names now uses: 15434 (names_db), 15433 (users_db), 16381 (cache), 16382 (sessions)

2. **Flutter Compilation Fixes**:
   - Installed missing go_router package (`flutter pub get`)
   - Created missing `user_profile_provider.dart`
   - Fixed field name mismatches in `profile_settings_screen.dart`:
     - `traditionalModernScale` → `traditionalVsModern`
     - Removed non-existent fields (preferredGender, preferredStartingLetters, etc.)
     - Added actual fields (preferredNameLength, preferredOrigins, dislikedSounds)

3. **Documentation**:
   - Created comprehensive port management docs (`scripts/README.md`)
   - Added this `claude.md` file

## Known Issues & Gotchas

1. **Backend Port Discrepancy**:
   - `.env` says BACKEND_PORT=8000
   - Actually running on port 8001
   - Frontend hardcoded to use 8001

2. **No OpenAPI Generation**:
   - Config exists but never run
   - Need to create annotation file and run build_runner
   - See `scripts/README.md` for OpenAPI generation steps

3. **Profile Provider is Stub**:
   - Returns null, shows "Create Profile" screen
   - Need to implement actual API integration

4. **Many Background Processes Running**:
   - Multiple Flutter and backend instances from previous sessions
   - Recommend cleaning up: check `ps aux | grep flutter` and kill old processes

5. **Database Migrations**:
   - Using direct SQLAlchemy create_all() currently
   - Should migrate to Alembic for production

## Environment Variables

### Infrastructure (.env in project root)
```bash
POSTGRES_NAMES_PORT=15434
POSTGRES_USERS_PORT=15433
REDIS_CACHE_PORT=16381
REDIS_SESSIONS_PORT=16382
PGADMIN_PORT=15050
BACKEND_PORT=8000  # Note: actual backend runs on 8001
FRONTEND_PORT=5173
```

### Backend (apps/backend/.env) - Not created yet
Would contain:
- SECRET_KEY
- DATABASE_URLs (constructed from above ports)
- CORS_ORIGINS
- API keys (OpenAI, etc.)

## Testing

### Backend Tests
```bash
cd apps/backend
uv run pytest                    # All tests
uv run pytest -v                # Verbose
uv run pytest --cov=app         # With coverage
```

### Frontend Tests
```bash
cd apps/frontend
flutter test                    # Unit tests
flutter test integration_test/  # Integration tests
```

## API Endpoints

### Currently Implemented
- `GET /api/v1/names/` - List all names
- `GET /api/v1/names/{id}` - Get name by ID
- `POST /api/v1/names/` - Create name
- `PUT /api/v1/names/{id}` - Update name
- `DELETE /api/v1/names/{id}` - Delete name

### Planned
- `/api/v1/names/search?q=...` - Search names
- `/api/v1/names/trending` - Get trending names
- `/api/v1/popularity/...` - Popularity data
- `/api/v1/profiles/...` - User profiles
- `/api/v1/auth/...` - Authentication (fastapi-users)

## Next Steps / TODO

### High Priority
1. [ ] Set up OpenAPI code generation for Flutter
2. [ ] Implement proper API client in Flutter (replace Dio calls)
3. [ ] Fix backend port to match .env (8000 vs 8001)
4. [ ] Implement user profile API endpoints
5. [ ] Connect profile provider to backend

### Medium Priority
1. [ ] Add Alembic migrations
2. [ ] Implement caching layer
3. [ ] Add authentication to frontend
4. [ ] Create profile onboarding flow
5. [ ] Add popularity trend charts

### Low Priority
1. [ ] Clean up old background processes
2. [ ] Add comprehensive tests
3. [ ] Set up CI/CD
4. [ ] Add data import scripts (SSA, ONS data)

## Useful Commands Reference

```bash
# Check what's using a port
ss -tuln | grep :PORT_NUMBER
lsof -i :PORT_NUMBER

# Find process by name
ps aux | grep flutter
ps aux | grep fastapi

# Docker operations
docker ps                       # List running containers
docker ps -a                    # List all containers
docker logs CONTAINER_NAME      # View logs
docker exec -it CONTAINER bash  # Shell into container

# Database direct access
docker exec -it babynames_db psql -U postgres -d babynames_db
\dt                            # List tables
\d table_name                  # Describe table

# Generate new ports (if conflicts arise)
python scripts/generate_ports.py
docker compose down && docker compose up -d
```

## Architecture Decisions

### Why Dual Databases?
- **Security**: Isolate authentication data
- **Scaling**: Independent scaling strategies
- **Compliance**: Different retention policies

### Why Dual Redis?
- **Cache**: LRU eviction, no persistence, speed-optimized
- **Sessions**: Persistent, no eviction, data integrity

### Why UV over Poetry?
- **Speed**: 10-100x faster dependency resolution
- **Modern**: Growing adoption, future-proof
- **Compatible**: Standard pyproject.toml

### Why Feature-Based Frontend Structure?
- **Cohesion**: Related code stays together
- **Scalability**: Easy to add/remove features
- **Team**: Multiple developers can work in parallel

## Contact & Resources

- **Backend**: FastAPI on port 8001 → `http://localhost:8001/docs`
- **Frontend**: Flutter on port 5173 → `http://localhost:5173`
- **PgAdmin**: `http://localhost:15050` (admin@babynames.local / admin)
- **API Docs**: `http://localhost:8001/docs` (Swagger UI)
- **OpenAPI Spec**: `http://localhost:8001/openapi.json`

**Documentation**:
- Main README: `README.md`
- Setup Guide: `SETUP.md`
- Quick Start: `START_HERE.md`
- Port Management: `scripts/README.md`
- Progress: `PROGRESS_SUMMARY.md`

---

**Note for AI Assistants**: This file should be updated whenever significant changes are made to the project structure, architecture, or development workflow. When making major changes, please update the "Last Updated" date and the "Recent Changes & Fixes" section.
