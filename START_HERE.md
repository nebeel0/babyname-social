# 🚀 Quick Start Guide

## Option 1: With Docker (Recommended)

### Prerequisites
- Docker Desktop installed and running
- Make installed

### Steps

1. **Start Everything**
   ```bash
   cd /home/ben/babyname-social/universe1

   # Start infrastructure (Postgres, Redis)
   make build

   # Initialize databases
   cd apps/backend
   uv run python scripts/init_db.py
   cd ../..

   # Start backend
   make dev
   ```

2. **In a New Terminal - Start Frontend**
   ```bash
   cd /home/ben/babyname-social/universe1
   make dev-frontend
   ```

3. **Access the Application**
   - Frontend: Opens automatically in Chrome (http://localhost:5173)
   - Backend API: http://localhost:8001/docs
   - PgAdmin: http://localhost:5050

---

## Option 2: Without Docker (Quick Test)

If Docker is not available, you can still run the application:

### Prerequisites
- Python 3.12+ with UV installed
- Flutter 3.7+

### Steps

1. **Start Docker Desktop** (if you have it installed)
   - Open Docker Desktop application
   - Wait for it to fully start
   - Green indicator means it's ready

2. **Start Backend**
   ```bash
   cd /home/ben/babyname-social/universe1
   chmod +x start-backend.sh
   ./start-backend.sh
   ```

   Backend will start on: http://localhost:8001

3. **In a New Terminal - Start Frontend**
   ```bash
   cd /home/ben/babyname-social/universe1
   chmod +x start-frontend.sh
   ./start-frontend.sh
   ```

4. **Important**: The backend needs PostgreSQL and Redis
   - If you don't have Docker, you'll get database connection errors
   - Backend will start but API calls requiring database will fail
   - You can still view the API documentation

---

## Option 3: Manual Docker Start

If Docker is installed but not running:

### macOS
```bash
open -a Docker
# Wait 30-60 seconds for Docker to start
```

### Linux
```bash
sudo systemctl start docker
# or
sudo service docker start
```

### Windows
- Open Docker Desktop from Start Menu
- Wait for it to start

Then follow Option 1 steps above.

---

## Verify Everything is Running

### Backend Health Check
```bash
curl http://localhost:8001/health
```

Should return: `{"status":"healthy"}`

### Database Check
```bash
curl http://localhost:8001/api/v1/names/
```

Should return: `[]` (empty array if no names added yet)

### Frontend
- Should automatically open in Chrome
- You'll see the "Baby Names Social Network" home screen

---

## Common Issues

### "Docker daemon not running"
**Solution**: Start Docker Desktop application

### "Port 8001 already in use"
**Solution**:
```bash
# Find what's using the port
lsof -i :8001
# Kill the process or change port in .env
```

### "Connection refused" to database
**Solution**:
1. Check Docker is running: `docker ps`
2. Start services: `make build`
3. Check logs: `docker compose logs`

### Flutter build errors
**Solution**:
```bash
cd apps/frontend
flutter clean
flutter pub get
```

---

## Next Steps After Starting

1. **Register a User**
   - Go to http://localhost:8001/docs
   - Try `POST /auth/register`

2. **Create Some Names**
   - Use `POST /api/v1/names`

3. **Search Names**
   - Use `GET /api/v1/names/search/{query}`

4. **Develop Features**
   - Backend: Edit files in `apps/backend/`
   - Frontend: Edit files in `apps/frontend/lib/`
   - Changes hot-reload automatically!

---

## Full Command Reference

```bash
# All-in-one
make help          # Show all commands

# Docker
make build         # Start Docker services
make down          # Stop Docker services
make clean         # Remove everything (DESTRUCTIVE!)

# Backend
make dev           # Start FastAPI
make lint          # Run linters
make test          # Run tests

# Frontend
make dev-frontend  # Start Flutter web

# Database
make db-init       # Initialize tables
make pgadmin       # Open PgAdmin

# API
make docs          # Open API documentation
make generate-api  # Generate Dart API client
```

---

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:8001 | - |
| API Docs | http://localhost:8001/docs | - |
| Frontend Web | http://localhost:5173 | - |
| PgAdmin | http://localhost:5050 | admin@babynames.local / admin |
| PostgreSQL (names) | localhost:5434 | postgres / postgres |
| PostgreSQL (users) | localhost:5433 | postgres / postgres |
| Redis (cache) | localhost:6379 | - |
| Redis (sessions) | localhost:6380 | - |

---

## Support

- Full documentation: [SETUP.md](SETUP.md)
- Main README: [README.md](README.md)
- Backend README: [apps/backend/README.md](apps/backend/README.md)
