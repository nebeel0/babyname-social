.PHONY: help install dev build up down clean test lint format backend-shell db-init

# Colors
GREEN=\033[32m
CYAN=\033[36m
YELLOW=\033[33m
RED=\033[31m
RESET=\033[0m

help:
	@echo "$(CYAN)Baby Names Social Network - Development Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Setup:$(RESET)"
	@echo "  make install       - Install all dependencies (backend + frontend)"
	@echo "  make install-backend  - Install Python dependencies with UV"
	@echo "  make install-frontend - Install Flutter dependencies"
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@echo "  make dev           - Start backend dev server"
	@echo "  make dev-frontend  - Start Flutter app"
	@echo "  make build         - Start all Docker services (DBs, Redis)"
	@echo "  make up            - Start all services including backend"
	@echo "  make down          - Stop all services"
	@echo ""
	@echo "$(GREEN)Database:$(RESET)"
	@echo "  make db-init       - Initialize database tables"
	@echo "  make db-migrate    - Run Alembic migrations"
	@echo "  make db-revision   - Create new Alembic migration"
	@echo "  make pgadmin       - Open PgAdmin (http://localhost:5050)"
	@echo ""
	@echo "$(GREEN)Code Quality:$(RESET)"
	@echo "  make lint          - Run all linters (black, ruff, mypy)"
	@echo "  make format        - Format code (black + ruff --fix)"
	@echo "  make test          - Run tests"
	@echo ""
	@echo "$(GREEN)API:$(RESET)"
	@echo "  make generate-api  - Generate Dart client from OpenAPI spec"
	@echo "  make docs          - Open API documentation (http://localhost:8000/docs)"
	@echo ""
	@echo "$(GREEN)Utilities:$(RESET)"
	@echo "  make backend-shell - Open bash shell in backend directory"
	@echo "  make clean         - Remove all containers and volumes (DESTRUCTIVE!)"

# Installation
install: install-backend install-frontend

install-backend:
	@echo "$(CYAN)Installing backend dependencies with UV...$(RESET)"
	cd apps/backend && uv sync
	@echo "$(GREEN)Backend dependencies installed!$(RESET)"

install-frontend:
	@echo "$(CYAN)Installing Flutter dependencies...$(RESET)"
	cd apps/frontend && flutter pub get
	@echo "$(GREEN)Frontend dependencies installed!$(RESET)"

# Development
dev:
	@echo "$(CYAN)Starting FastAPI dev server...$(RESET)"
	cd apps/backend && uv run fastapi dev app/main.py --port 8000

dev-frontend:
	@echo "$(CYAN)Starting Flutter app...$(RESET)"
	cd apps/frontend && flutter run -d chrome

# Docker
build:
	@echo "$(CYAN)Starting Docker services (databases, Redis)...$(RESET)"
	docker compose up -d db_names db_users redis_cache redis_sessions pgadmin
	@echo "$(GREEN)Services started!$(RESET)"
	@echo "$(YELLOW)PgAdmin: http://localhost:5050 (admin@babynames.local / admin)$(RESET)"

up:
	@echo "$(CYAN)Starting all services...$(RESET)"
	docker compose up -d
	@echo "$(GREEN)All services started!$(RESET)"

down:
	@echo "$(CYAN)Stopping all services...$(RESET)"
	docker compose down
	@echo "$(GREEN)Services stopped!$(RESET)"

clean:
	@echo "$(RED)WARNING: This will remove all containers, volumes, and data!$(RESET)"
	@read -p "Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v --remove-orphans; \
		echo "$(GREEN)Cleanup complete!$(RESET)"; \
	else \
		echo "$(YELLOW)Cancelled.$(RESET)"; \
	fi

# Database
db-init:
	@echo "$(CYAN)Initializing databases...$(RESET)"
	cd apps/backend && uv run python -c "from db.base import Base, names_engine, users_engine; import asyncio; asyncio.run(Base.metadata.create_all(bind=names_engine)); asyncio.run(Base.metadata.create_all(bind=users_engine))"
	@echo "$(GREEN)Databases initialized!$(RESET)"

db-migrate:
	@echo "$(CYAN)Running Alembic migrations...$(RESET)"
	cd apps/backend && uv run alembic upgrade head
	@echo "$(GREEN)Migrations complete!$(RESET)"

db-revision:
	@echo "$(CYAN)Creating new migration...$(RESET)"
	@read -p "Migration message: " message; \
	cd apps/backend && uv run alembic revision --autogenerate -m "$$message"

pgadmin:
	@echo "$(CYAN)Opening PgAdmin...$(RESET)"
	@echo "$(YELLOW)URL: http://localhost:5050$(RESET)"
	@echo "$(YELLOW)Email: admin@babynames.local$(RESET)"
	@echo "$(YELLOW)Password: admin$(RESET)"
	xdg-open http://localhost:5050 || open http://localhost:5050 || echo "Open http://localhost:5050 in your browser"

# Code Quality
lint: black ruff mypy

black:
	@echo "$(CYAN)Running Black...$(RESET)"
	cd apps/backend && uv run black .
	@echo "$(GREEN)Black finished!$(RESET)"

ruff:
	@echo "$(CYAN)Running Ruff...$(RESET)"
	cd apps/backend && uv run ruff check .
	@echo "$(GREEN)Ruff finished!$(RESET)"

mypy:
	@echo "$(CYAN)Running Mypy...$(RESET)"
	cd apps/backend && uv run mypy .
	@echo "$(GREEN)Mypy finished!$(RESET)"

format:
	@echo "$(CYAN)Formatting code...$(RESET)"
	cd apps/backend && uv run black .
	cd apps/backend && uv run ruff check . --fix
	@echo "$(GREEN)Formatting complete!$(RESET)"

test:
	@echo "$(CYAN)Running tests...$(RESET)"
	cd apps/backend && uv run pytest -vv
	@echo "$(GREEN)Tests complete!$(RESET)"

# API
generate-api:
	@echo "$(CYAN)Generating Dart API client...$(RESET)"
	@echo "$(YELLOW)Make sure backend is running on http://localhost:8000$(RESET)"
	curl http://localhost:8000/openapi.json > apps/frontend/schema/openapi.json
	cd apps/frontend && flutter pub run build_runner build --delete-conflicting-outputs
	@echo "$(GREEN)API client generated!$(RESET)"

docs:
	@echo "$(CYAN)Opening API docs...$(RESET)"
	xdg-open http://localhost:8000/docs || open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

# Utilities
backend-shell:
	cd apps/backend && bash
