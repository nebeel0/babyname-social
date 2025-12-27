"""Unit tests for user profile endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from datetime import datetime
import asyncpg

from app.api.v1.endpoints.profiles import (
    get_profile,
    create_profile,
    update_profile,
    delete_profile,
    get_user_profile_by_user_id,
)
from core.models.v1.user_profile import UserProfileCreate, UserProfileUpdate


@pytest.fixture
def mock_conn():
    """Create a mock asyncpg connection."""
    conn = AsyncMock(spec=asyncpg.Connection)
    # Mock transaction context manager
    transaction = AsyncMock()
    transaction.__aenter__ = AsyncMock(return_value=transaction)
    transaction.__aexit__ = AsyncMock(return_value=None)
    conn.transaction.return_value = transaction
    return conn


@pytest.fixture
def sample_profile():
    """Sample user profile data."""
    return {
        "user_id": "test-user-123",
        "ethnicity": "White",
        "age": 30,
        "current_state": "CA",
        "current_city": "San Francisco",
        "planned_state": None,
        "planned_city": None,
        "country": "USA",
        "partner_ethnicity": "Asian",
        "existing_children_names": ["Alice", "Bob"],
        "family_surnames": ["Smith", "Johnson"],
        "cultural_importance": 7,
        "uniqueness_preference": 5,
        "traditional_vs_modern": 6,
        "nickname_friendly": True,
        "religious_significance": False,
        "avoid_discrimination_risk": True,
        "pronunciation_simplicity": 8,
        "preferred_name_length": "medium",
        "preferred_origins": ["English", "French"],
        "disliked_sounds": ["harsh-k"],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.mark.asyncio
async def test_get_user_profile_by_user_id_success(mock_conn, sample_profile):
    """Test getting a user profile by user_id."""
    mock_conn.fetchrow.return_value = sample_profile

    result = await get_user_profile_by_user_id("test-user-123", mock_conn)

    assert result == sample_profile
    mock_conn.fetchrow.assert_called_once_with(
        "SELECT * FROM user_profiles WHERE user_id = $1", "test-user-123"
    )


@pytest.mark.asyncio
async def test_get_user_profile_by_user_id_not_found(mock_conn):
    """Test getting a non-existent user profile."""
    mock_conn.fetchrow.return_value = None

    result = await get_user_profile_by_user_id("non-existent", mock_conn)

    assert result is None


@pytest.mark.asyncio
async def test_create_profile_success(mock_conn, sample_profile):
    """Test creating a new user profile."""
    profile_create = UserProfileCreate(
        user_id="test-user-123",
        ethnicity="White",
        age=30,
        current_state="CA",
        current_city="San Francisco",
        country="US",
        partner_ethnicity="Asian",
        existing_children_names=["Alice", "Bob"],
        family_surnames=["Smith", "Johnson"],
        cultural_importance=4,
        uniqueness_preference=5,
        traditional_vs_modern=3,
        nickname_friendly=True,
        religious_significance=False,
        avoid_discrimination_risk=True,
        pronunciation_simplicity=5,
        preferred_name_length="medium",
        preferred_origins=["English", "French"],
        disliked_sounds=["harsh-k"],
    )

    # Mock no existing profile
    existing_check = AsyncMock()
    existing_check.fetchrow = AsyncMock(return_value=None)

    # Mock successful insert
    mock_conn.fetchrow.side_effect = [
        None,  # No existing profile
        sample_profile,  # Returned profile after insert
    ]

    result = await create_profile(profile_create, mock_conn)

    # Verify transaction was used
    mock_conn.transaction.assert_called_once()

    # Verify result
    assert result["user_id"] == "test-user-123"
    assert result["ethnicity"] == "White"


@pytest.mark.asyncio
async def test_create_profile_already_exists(mock_conn, sample_profile):
    """Test creating a profile that already exists."""
    from fastapi import HTTPException

    profile_create = UserProfileCreate(
        user_id="test-user-123",
        ethnicity="White",
        age=30,
    )

    # Mock existing profile
    mock_conn.fetchrow.return_value = sample_profile

    with pytest.raises(HTTPException) as exc_info:
        await create_profile(profile_create, mock_conn)

    assert exc_info.value.status_code == 400
    assert "already exists" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_profile_success(mock_conn, sample_profile):
    """Test updating an existing profile."""
    profile_update = UserProfileUpdate(
        age=31,
        current_city="Los Angeles",
    )

    updated_profile = sample_profile.copy()
    updated_profile["age"] = 31
    updated_profile["current_city"] = "Los Angeles"

    # Mock existing profile check and update
    mock_conn.fetchrow.side_effect = [
        sample_profile,  # Existing profile check
        updated_profile,  # Updated profile after UPDATE
    ]

    result = await update_profile("test-user-123", profile_update, mock_conn)

    # Verify transaction was used
    mock_conn.transaction.assert_called_once()

    # Verify update
    assert result["age"] == 31
    assert result["current_city"] == "Los Angeles"


@pytest.mark.asyncio
async def test_update_profile_not_found(mock_conn):
    """Test updating a non-existent profile."""
    from fastapi import HTTPException

    profile_update = UserProfileUpdate(age=31)

    # Mock no existing profile
    mock_conn.fetchrow.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await update_profile("non-existent", profile_update, mock_conn)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_profile_no_changes(mock_conn, sample_profile):
    """Test updating a profile with no changes."""
    profile_update = UserProfileUpdate()

    # Mock existing profile
    mock_conn.fetchrow.return_value = sample_profile

    result = await update_profile("test-user-123", profile_update, mock_conn)

    # Should return existing profile without calling UPDATE
    assert result["user_id"] == "test-user-123"
    # Transaction should not be called when no updates
    mock_conn.transaction.assert_not_called()


@pytest.mark.asyncio
async def test_delete_profile_success(mock_conn, sample_profile):
    """Test deleting a profile."""
    # Mock existing profile check
    mock_conn.fetchrow.return_value = sample_profile
    mock_conn.execute.return_value = "DELETE 1"

    result = await delete_profile("test-user-123", mock_conn)

    # Verify transaction was used
    mock_conn.transaction.assert_called_once()

    # Verify delete was called
    mock_conn.execute.assert_called_once()
    assert result is None


@pytest.mark.asyncio
async def test_delete_profile_not_found(mock_conn):
    """Test deleting a non-existent profile."""
    from fastapi import HTTPException

    # Mock no existing profile
    mock_conn.fetchrow.return_value = None
    mock_conn.execute.return_value = "DELETE 0"

    with pytest.raises(HTTPException) as exc_info:
        await delete_profile("non-existent", mock_conn)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_transaction_rollback_on_error(mock_conn):
    """Test that transaction rolls back on error."""
    profile_create = UserProfileCreate(
        user_id="test-user-123",
        ethnicity="White",
        age=30,
    )

    # Mock no existing profile
    mock_conn.fetchrow.return_value = None

    # Mock insert failure
    mock_conn.fetchrow.side_effect = [
        None,  # No existing profile
        Exception("Database error"),  # Insert fails
    ]

    with pytest.raises(Exception, match="Database error"):
        await create_profile(profile_create, mock_conn)

    # Verify transaction was started (cleanup is automatic via context manager)
    mock_conn.transaction.assert_called_once()
