# Complete Setup Guide - Baby Names Social Network

## 🎉 Project Status: FULLY SET UP!

All phases complete! Backend and Frontend are ready to run.

---

## What We've Built

### ✅ Backend (FastAPI)
- **Framework**: FastAPI 0.126 with UV package manager
- **Databases**: Dual PostgreSQL (names + users)
- **Cache**: Dual Redis (cache + sessions)
- **Auth**: fastapi-users with JWT
- **Models**: 7 comprehensive database models
- **API**: RESTful with automatic OpenAPI docs

### ✅ Frontend (Flutter)
- **Framework**: Flutter 3.32.6
- **State Management**: Riverpod 2.x
- **Routing**: go_router
- **HTTP Client**: Dio
- **Code Generation**: OpenAPI + Riverpod generators

### ✅ Architecture Decisions (Hybrid Best Practices)
- **From Landbridge (Proven)**:
  - Dual databases for security isolation
  - Dual Redis for optimized caching
  - Repository pattern support
  - fastapi-users authentication
  - Makefile task automation

- **Modern Improvements**:
  - Riverpod 2.x instead of Bloc (less boilerplate)
  - OpenAPI-first API design
  - Feature-first Flutter structure

---

## Prerequisites

- **Python 3.12+**
- **UV** package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Docker & Docker Compose**
- **Flutter 3.7+** (`flutter doctor`)
- **Make** (usually pre-installed)

---

## Quick Start (5 Steps)

### Step 1: Install Dependencies

```bash
cd /home/ben/babyname-social/universe1

# Backend
cd apps/backend
uv sync
cd ../..

# Frontend
cd apps/frontend
flutter pub get
cd ../..
```

### Step 2: Start Infrastructure

```bash
# Start Docker services (PostgreSQL, Redis, PgAdmin)
make build
```

This starts:
- PostgreSQL (names) on `localhost:5432`
- PostgreSQL (users) on `localhost:5433`
- Redis (cache) on `localhost:6379`
- Redis (sessions) on `localhost:6380`
- PgAdmin on `http://localhost:5050`

### Step 3: Initialize Databases

```bash
cd apps/backend
uv run python scripts/init_db.py
```

### Step 4: Start Backend

```bash
# From universe1 root
make dev
```

Backend runs on `http://localhost:8000`

**Test it:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- OpenAPI Spec: http://localhost:8000/openapi.json

### Step 5: Start Frontend

```bash
cd apps/frontend
flutter run -d chrome
```

Or use `make dev-frontend` from the root.

---

## Full Command Reference

### Development

```bash
make help              # Show all commands
make dev               # Start backend (FastAPI)
make dev-frontend      # Start Flutter web
make build             # Start Docker services only
make up                # Start all services (Docker + backend)
make down              # Stop all services
```

### Database

```bash
make db-init           # Initialize database tables
make pgadmin           # Open PgAdmin UI
make db-migrate        # Run Alembic migrations (future)
```

### Code Quality

```bash
make lint              # Run black + ruff + mypy
make format            # Auto-format code
make test              # Run tests
```

### API & Code Generation

```bash
make generate-api      # Generate Dart client from OpenAPI
make docs              # Open API documentation
```

---

## Project Structure

```
universe1/
├── apps/
│   ├── backend/                 # FastAPI Application
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI app entry
│   │   │   ├── api/v1/         # API endpoints
│   │   │   ├── auth/           # fastapi-users auth
│   │   │   └── dependencies/   # DI
│   │   ├── core/
│   │   │   ├── settings.py     # Configuration
│   │   │   └── models/v1/      # Pydantic schemas
│   │   ├── db/
│   │   │   ├── base.py         # Database setup
│   │   │   └── models/         # SQLAlchemy models
│   │   │       ├── name.py
│   │   │       ├── popularity_history.py
│   │   │       ├── famous_reference.py
│   │   │       └── user.py
│   │   ├── scripts/
│   │   │   └── init_db.py      # DB initialization
│   │   ├── pyproject.toml      # UV dependencies
│   │   └── .env                # Configuration
│   │
│   └── frontend/                # Flutter Application
│       ├── lib/
│       │   ├── main.dart       # App entry (Riverpod)
│       │   ├── core/           # Shared core
│       │   │   ├── api/
│       │   │   ├── providers/
│       │   │   └── models/
│       │   ├── features/       # Feature-first
│       │   │   ├── auth/
│       │   │   ├── names/
│       │   │   └── profile/
│       │   └── shared/
│       ├── schema/              # OpenAPI specs
│       ├── pubspec.yaml         # Flutter dependencies
│       └── build.yaml           # Code generation config
│
├── docker-compose.yml           # Infrastructure
├── Makefile                     # Task automation
└── README.md                    # Main docs
```

---

## API Endpoints

### Authentication (fastapi-users)
- `POST /auth/register` - Register new user
- `POST /auth/jwt/login` - Login (returns JWT token)
- `POST /auth/jwt/logout` - Logout
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token
- `POST /auth/request-verify-token` - Request email verification
- `POST /auth/verify` - Verify email with token

### Users
- `GET /users/me` - Get current user
- `PATCH /users/me` - Update current user

### Names (API v1)
- `GET /api/v1/names` - List names (paginated, ?skip=0&limit=20)
- `GET /api/v1/names/{id}` - Get name details
- `POST /api/v1/names` - Create name (requires auth)
- `GET /api/v1/names/search/{query}` - Search names

---

## Database Models

### Names Database (babynames_db)

1. **names** - Core name data
   - Etymology, meaning, origins, gender
   - Aggregate stats (avg_rating, trending_score)
   - Phonetic characteristics

2. **popularity_history** - Time-series data
   - Year, country, state/province, city
   - Rank, count, percentage metrics
   - Optimized for analytics queries

3. **name_variants** - Variations
   - Spelling variants, diminutives, translations
   - Language and region info

4. **famous_references** - Notable people/characters
   - Historical figures, celebrities, fictional
   - Biographical data, media sources

5. **cultural_contexts** - Cultural significance
   - Religious, mythological, traditional
   - Name days, saint info

6. **user_name_preferences** - User favorites
   - Ratings (1-5), categories, notes
   - Sharing with partners

7. **comments** - User reviews
   - Public/private comments
   - Moderation flags

### Users Database (users_db)

1. **users** - Authentication & profiles
   - Email, password (hashed)
   - Profile data (name, location, demographics)
   - Partner linking, privacy settings

---

## Configuration

### Backend (.env)

```bash
# Database
NAMES_DB_HOST=localhost
NAMES_DB_PORT=5432
USERS_DB_PORT=5433

# Redis
REDIS_CACHE_PORT=6379
REDIS_SESSIONS_PORT=6380

# Auth
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Frontend (.env.web / .env.mobile)

```bash
# Web
BASE_URL=http://localhost:8000

# Mobile (Android emulator)
BASE_URL=http://10.0.2.2:8000
```

---

## Next Steps

### Immediate Todos
1. Start Docker: `make build`
2. Initialize DBs: `cd apps/backend && uv run python scripts/init_db.py`
3. Start backend: `make dev`
4. Test API: http://localhost:8000/docs

### Development Workflow

**Backend Development:**
1. Add/modify models in `db/models/`
2. Create schemas in `core/models/v1/`
3. Add endpoints in `app/api/v1/endpoints/`
4. Run linters: `make lint`
5. Test: `make test`

**Frontend Development:**
1. Generate API client: `make generate-api` (when backend is running)
2. Create features in `lib/features/`
3. Use Riverpod providers for state
4. Run: `flutter run -d chrome`

**Full-Stack Feature:**
1. Backend: Create model → schema → endpoint
2. Frontend: Generate API client → Create provider → Build UI
3. Test end-to-end

---

## Troubleshooting

### Docker won't start
```bash
# Check Docker is running
docker ps

# Restart Docker Desktop (if using)
# Or start Docker daemon (Linux)
sudo systemctl start docker
```

### Port already in use
```bash
# Check what's using the port
lsof -i :8000  # or :5432, :6379, etc.

# Kill the process or change port in .env
```

### Backend import errors
```bash
cd apps/backend
uv sync  # Reinstall dependencies
```

### Flutter build errors
```bash
cd apps/frontend
flutter clean
flutter pub get
```

### Database connection failed
```bash
# Ensure Docker is running
docker compose ps

# Check logs
docker compose logs db_names
docker compose logs db_users
```

---

## Testing

### Test Backend API

```bash
# Using curl
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/names

# Using API docs
open http://localhost:8000/docs
```

### Test Frontend

```bash
cd apps/frontend
flutter test
```

---

## Production Deployment

**TODO**: Add deployment guides for:
- Backend: Docker, Railway, Fly.io
- Frontend: Cloudflare Pages, Vercel, Firebase Hosting
- Database: Managed PostgreSQL (Neon, Supabase)
- Redis: Upstash, Redis Cloud

---

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [fastapi-users](https://fastapi-users.github.io/fastapi-users/)
- [Riverpod](https://riverpod.dev/)
- [Flutter](https://flutter.dev/)
- [UV Package Manager](https://github.com/astral-sh/uv)

---

## Support

For issues or questions:
1. Check this guide
2. Review the main [README.md](README.md)
3. Check Docker logs: `docker compose logs`
4. Backend logs: Check terminal output from `make dev`
5. Frontend logs: Check browser console

---

## License

TBD
