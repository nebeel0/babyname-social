# Integration Tests

## Overview

Integration tests require a PostgreSQL database because the application uses PostgreSQL-specific features like JSONB columns and custom functions.

## Setup

To run integration tests, you need:

1. A PostgreSQL test database
2. Environment variables configured to connect to the test database
3. Database migrations applied

## Example Integration Test Setup

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

# Example: Use a real PostgreSQL test database
TEST_DATABASE_URL = "postgresql+asyncpg://testuser:testpass@localhost:5432/test_db"

@pytest.fixture
async def test_db():
    """Create a test database connection."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_client(test_db):
    """Create a test HTTP client."""
    async_session = async_sessionmaker(
        test_db,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
```

## Running Integration Tests

```bash
# With a PostgreSQL test database configured
pytest tests/integration -v

# Skip integration tests if no database available
pytest tests/unit -v
```

## Future Work

Integration tests should be added for:
- [ ] Prefix tree API endpoints
- [ ] Name search and filtering
- [ ] User preferences
- [ ] Name enrichment
- [ ] Database transaction handling
- [ ] Concurrent request handling
