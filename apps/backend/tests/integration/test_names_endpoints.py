"""Integration tests for names endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from db.models.name import Name
from db.base import get_names_db


@pytest.fixture
async def client():
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session():
    """Get database session."""
    async for session in get_names_db():
        yield session


@pytest.fixture
async def cleanup_test_names(db_session: AsyncSession):
    """Clean up test names after each test."""
    yield
    # Delete any test names
    await db_session.execute(
        delete(Name).where(Name.name.like("TestName%"))
    )
    await db_session.commit()


@pytest.fixture
async def sample_names(db_session: AsyncSession):
    """Create sample names for testing."""
    names = [
        Name(name="Leo", gender="male", meaning="Lion", origin_country="Italy"),
        Name(name="Leon", gender="male", meaning="Lion", origin_country="Greece"),
        Name(name="Leona", gender="female", meaning="Lioness", origin_country="Italy"),
        Name(name="Leonardo", gender="male", meaning="Brave as a lion", origin_country="Italy"),
        Name(name="Napoleon", gender="male", meaning="Lion of Naples", origin_country="France"),
        Name(name="Cleo", gender="female", meaning="Glory", origin_country="Greece"),
        Name(name="Emma", gender="female", meaning="Universal", origin_country="Germany"),
        Name(name="Olivia", gender="female", meaning="Olive tree", origin_country="England"),
    ]

    for name in names:
        db_session.add(name)

    await db_session.commit()

    # Refresh to get IDs
    for name in names:
        await db_session.refresh(name)

    yield names

    # Cleanup
    for name in names:
        await db_session.delete(name)
    await db_session.commit()


class TestSearchNames:
    """Test suite for search functionality."""

    @pytest.mark.asyncio
    async def test_search_exact_match_first(self, client: AsyncClient, sample_names):
        """Test that exact matches appear first in search results."""
        response = await client.get("/api/v1/names/search/leo")

        assert response.status_code == 200
        results = response.json()

        assert len(results) > 0
        # First result should be exact match
        assert results[0]["name"].lower() == "leo"

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, client: AsyncClient, sample_names):
        """Test that search is case-insensitive."""
        response_lower = await client.get("/api/v1/names/search/leo")
        response_upper = await client.get("/api/v1/names/search/LEO")
        response_mixed = await client.get("/api/v1/names/search/Leo")

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert response_mixed.status_code == 200

        # All should return same results
        results_lower = response_lower.json()
        results_upper = response_upper.json()
        results_mixed = response_mixed.json()

        assert len(results_lower) == len(results_upper) == len(results_mixed)
        assert results_lower[0]["name"] == results_upper[0]["name"] == results_mixed[0]["name"]

    @pytest.mark.asyncio
    async def test_search_starts_with_prioritized(self, client: AsyncClient, sample_names):
        """Test that names starting with query are prioritized over contains."""
        response = await client.get("/api/v1/names/search/leo")

        assert response.status_code == 200
        results = response.json()

        # Extract just names
        result_names = [r["name"] for r in results]

        # Names starting with "Leo" should come before "Napoleon" and "Cleo"
        leo_index = result_names.index("Leo")
        leon_index = result_names.index("Leon")
        leona_index = result_names.index("Leona")
        leonardo_index = result_names.index("Leonardo")

        napoleon_index = result_names.index("Napoleon") if "Napoleon" in result_names else float('inf')
        cleo_index = result_names.index("Cleo") if "Cleo" in result_names else float('inf')

        # All "Leo*" names should come before "Napoleon" and "Cleo"
        assert leo_index < napoleon_index
        assert leon_index < napoleon_index
        assert leona_index < napoleon_index
        assert leonardo_index < napoleon_index
        assert leo_index < cleo_index
        assert leon_index < cleo_index

    @pytest.mark.asyncio
    async def test_search_limit_parameter(self, client: AsyncClient, sample_names):
        """Test that limit parameter works correctly."""
        response = await client.get("/api/v1/names/search/leo?limit=3")

        assert response.status_code == 200
        results = response.json()

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_no_results(self, client: AsyncClient, sample_names):
        """Test search with no matching results."""
        response = await client.get("/api/v1/names/search/zzzzzzzzz")

        assert response.status_code == 200
        results = response.json()

        assert results == []

    @pytest.mark.asyncio
    async def test_search_partial_match(self, client: AsyncClient, sample_names):
        """Test partial match search."""
        response = await client.get("/api/v1/names/search/leon")

        assert response.status_code == 200
        results = response.json()

        result_names = [r["name"] for r in results]

        # Should include Leon, Leona, Leonardo, Napoleon
        assert "Leon" in result_names
        assert "Leona" in result_names
        assert "Leonardo" in result_names
        assert "Napoleon" in result_names


class TestGetNames:
    """Test suite for get_names endpoint."""

    @pytest.mark.asyncio
    async def test_get_names_default_pagination(self, client: AsyncClient, sample_names):
        """Test getting names with default pagination."""
        response = await client.get("/api/v1/names/")

        assert response.status_code == 200
        results = response.json()

        assert isinstance(results, list)
        assert len(results) >= len(sample_names)

    @pytest.mark.asyncio
    async def test_get_names_with_skip_and_limit(self, client: AsyncClient, sample_names):
        """Test pagination with skip and limit."""
        # Get first page
        response1 = await client.get("/api/v1/names/?skip=0&limit=3")
        assert response1.status_code == 200
        results1 = response1.json()
        assert len(results1) <= 3

        # Get second page
        response2 = await client.get("/api/v1/names/?skip=3&limit=3")
        assert response2.status_code == 200
        results2 = response2.json()
        assert len(results2) <= 3

        # Results should be different (if we have enough names)
        if len(results1) > 0 and len(results2) > 0:
            assert results1[0]["id"] != results2[0]["id"]

    @pytest.mark.asyncio
    async def test_get_names_filters_empty_names(self, client: AsyncClient, db_session: AsyncSession):
        """Test that names with empty strings are filtered out."""
        # Create a name with empty string
        empty_name = Name(name="", gender="male")
        db_session.add(empty_name)
        await db_session.commit()

        response = await client.get("/api/v1/names/")

        assert response.status_code == 200
        results = response.json()

        # Should not include empty name
        for result in results:
            assert result["name"] != ""
            assert result["name"] is not None

        # Cleanup
        await db_session.delete(empty_name)
        await db_session.commit()


class TestGetNameById:
    """Test suite for get_name endpoint."""

    @pytest.mark.asyncio
    async def test_get_name_by_id_success(self, client: AsyncClient, sample_names):
        """Test getting a name by ID."""
        name_id = sample_names[0].id

        response = await client.get(f"/api/v1/names/{name_id}")

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == name_id
        assert result["name"] == sample_names[0].name

    @pytest.mark.asyncio
    async def test_get_name_by_id_not_found(self, client: AsyncClient):
        """Test getting a non-existent name."""
        response = await client.get("/api/v1/names/999999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateName:
    """Test suite for create_name endpoint."""

    @pytest.mark.asyncio
    async def test_create_name_success(self, client: AsyncClient, cleanup_test_names):
        """Test creating a new name."""
        new_name = {
            "name": "TestName123",
            "gender": "male",
            "meaning": "Test meaning",
            "origin_country": "Test Country"
        }

        response = await client.post("/api/v1/names/", json=new_name)

        assert response.status_code == 201
        result = response.json()

        assert result["name"] == new_name["name"]
        assert result["gender"] == new_name["gender"]
        assert result["meaning"] == new_name["meaning"]
        assert "id" in result

    @pytest.mark.asyncio
    async def test_create_name_duplicate(self, client: AsyncClient, sample_names, cleanup_test_names):
        """Test creating a duplicate name fails."""
        duplicate_name = {
            "name": sample_names[0].name,
            "gender": "male"
        }

        response = await client.post("/api/v1/names/", json=duplicate_name)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


class TestUpdateName:
    """Test suite for update_name endpoint."""

    @pytest.mark.asyncio
    async def test_update_name_success(self, client: AsyncClient, sample_names):
        """Test updating a name."""
        name_id = sample_names[0].id
        update_data = {
            "meaning": "Updated meaning"
        }

        response = await client.put(f"/api/v1/names/{name_id}", json=update_data)

        assert response.status_code == 200
        result = response.json()

        assert result["id"] == name_id
        assert result["meaning"] == update_data["meaning"]

    @pytest.mark.asyncio
    async def test_update_name_not_found(self, client: AsyncClient):
        """Test updating a non-existent name."""
        update_data = {
            "meaning": "Updated meaning"
        }

        response = await client.put("/api/v1/names/999999999", json=update_data)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDeleteName:
    """Test suite for delete_name endpoint."""

    @pytest.mark.asyncio
    async def test_delete_name_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test deleting a name."""
        # Create a test name
        test_name = Name(name="TestNameToDelete", gender="male")
        db_session.add(test_name)
        await db_session.commit()
        await db_session.refresh(test_name)

        name_id = test_name.id

        response = await client.delete(f"/api/v1/names/{name_id}")

        assert response.status_code == 204

        # Verify it's deleted
        result = await db_session.execute(
            select(Name).where(Name.id == name_id)
        )
        deleted_name = result.scalar_one_or_none()
        assert deleted_name is None

    @pytest.mark.asyncio
    async def test_delete_name_not_found(self, client: AsyncClient):
        """Test deleting a non-existent name."""
        response = await client.delete("/api/v1/names/999999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
