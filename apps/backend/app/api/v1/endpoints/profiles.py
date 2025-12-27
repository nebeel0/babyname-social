"""API endpoints for user profiles (personalization)"""
from fastapi import APIRouter, Depends, HTTPException
import asyncpg

from core.models.v1.user_profile import UserProfileCreate, UserProfileRead, UserProfileUpdate
from db.base import get_names_db_raw

router = APIRouter()


async def get_user_profile_by_user_id(user_id: str, conn: asyncpg.Connection) -> dict | None:
    """Get user profile by user_id"""
    result = await conn.fetchrow(
        "SELECT * FROM user_profiles WHERE user_id = $1",
        user_id
    )
    return dict(result) if result else None


@router.get("/{user_id}", response_model=UserProfileRead)
async def get_profile(
    user_id: str,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Get user profile by user_id"""
    profile = await get_user_profile_by_user_id(user_id, conn)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Convert timestamps to strings
    profile['created_at'] = profile['created_at'].isoformat()
    profile['updated_at'] = profile['updated_at'].isoformat()
    return profile


@router.post("/", response_model=UserProfileRead, status_code=201)
async def create_profile(
    profile_data: UserProfileCreate,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Create a new user profile"""
    # Check if profile already exists
    existing = await get_user_profile_by_user_id(profile_data.user_id, conn)
    if existing:
        raise HTTPException(status_code=400, detail="User profile already exists")

    # Insert new profile within a transaction
    async with conn.transaction():
        result = await conn.fetchrow("""
            INSERT INTO user_profiles (
                user_id, ethnicity, age, current_state, current_city, planned_state, planned_city,
                country, partner_ethnicity, existing_children_names, family_surnames,
                cultural_importance, uniqueness_preference, traditional_vs_modern,
                nickname_friendly, religious_significance, avoid_discrimination_risk,
                pronunciation_simplicity, preferred_name_length, preferred_origins, disliked_sounds
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21
            )
            RETURNING *
        """,
            profile_data.user_id,
            profile_data.ethnicity,
            profile_data.age,
            profile_data.current_state,
            profile_data.current_city,
            profile_data.planned_state,
            profile_data.planned_city,
            profile_data.country,
            profile_data.partner_ethnicity,
            profile_data.existing_children_names,
            profile_data.family_surnames,
            profile_data.cultural_importance,
            profile_data.uniqueness_preference,
            profile_data.traditional_vs_modern,
            profile_data.nickname_friendly,
            profile_data.religious_significance,
            profile_data.avoid_discrimination_risk,
            profile_data.pronunciation_simplicity,
            profile_data.preferred_name_length,
            profile_data.preferred_origins,
            profile_data.disliked_sounds,
        )

    profile = dict(result)
    profile['created_at'] = profile['created_at'].isoformat()
    profile['updated_at'] = profile['updated_at'].isoformat()
    return profile


@router.put("/{user_id}", response_model=UserProfileRead)
async def update_profile(
    user_id: str,
    profile_data: UserProfileUpdate,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Update user profile"""
    # Check if profile exists
    existing = await get_user_profile_by_user_id(user_id, conn)
    if not existing:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Build update query dynamically based on provided fields
    updates = profile_data.model_dump(exclude_unset=True)
    if not updates:
        # No changes, return existing
        existing['created_at'] = existing['created_at'].isoformat()
        existing['updated_at'] = existing['updated_at'].isoformat()
        return existing

    # Build SET clause
    set_clauses = []
    values = []
    param_num = 1

    for key, value in updates.items():
        set_clauses.append(f"{key} = ${param_num}")
        values.append(value)
        param_num += 1

    set_clause = ", ".join(set_clauses)
    values.append(user_id)  # For WHERE clause

    query = f"""
        UPDATE user_profiles
        SET {set_clause}, updated_at = NOW()
        WHERE user_id = ${param_num}
        RETURNING *
    """

    # Execute update within a transaction
    async with conn.transaction():
        result = await conn.fetchrow(query, *values)
    profile = dict(result)
    profile['created_at'] = profile['created_at'].isoformat()
    profile['updated_at'] = profile['updated_at'].isoformat()
    return profile


@router.delete("/{user_id}", status_code=204)
async def delete_profile(
    user_id: str,
    conn: asyncpg.Connection = Depends(get_names_db_raw),
):
    """Delete user profile"""
    # Execute delete within a transaction
    async with conn.transaction():
        result = await conn.execute(
            "DELETE FROM user_profiles WHERE user_id = $1",
            user_id
        )

    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="User profile not found")

    return None
