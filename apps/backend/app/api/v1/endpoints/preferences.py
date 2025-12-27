from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth.auth import current_active_user
from core.models.v1.name import UserPreferenceCreate, UserPreferenceRead
from db.base import get_users_db
from db.models.user import User
from db.models.user_preference import UserNamePreference

router = APIRouter()


@router.get("/", response_model=list[UserPreferenceRead])
async def get_user_preferences(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_users_db),
):
    """Get all preferences for the current user."""
    result = await session.execute(
        select(UserNamePreference).where(UserNamePreference.user_id == current_user.id)
    )
    preferences = result.scalars().all()
    return preferences


@router.post("/", response_model=UserPreferenceRead, status_code=201)
async def create_preference(
    preference_data: UserPreferenceCreate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_users_db),
):
    """Create or update a user preference (rating/favorite)."""
    # Check if preference already exists
    result = await session.execute(
        select(UserNamePreference).where(
            UserNamePreference.user_id == current_user.id,
            UserNamePreference.name_id == preference_data.name_id,
        )
    )
    existing_pref = result.scalar_one_or_none()

    if existing_pref:
        # Update existing preference
        update_data = preference_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "name_id":  # Don't update name_id
                setattr(existing_pref, field, value)

        await session.commit()
        await session.refresh(existing_pref)
        return existing_pref

    # Create new preference
    preference = UserNamePreference(
        user_id=current_user.id, **preference_data.model_dump()
    )
    session.add(preference)
    await session.commit()
    await session.refresh(preference)

    return preference


@router.delete("/{preference_id}", status_code=204)
async def delete_preference(
    preference_id: int,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_users_db),
):
    """Delete a user preference."""
    result = await session.execute(
        select(UserNamePreference).where(
            UserNamePreference.id == preference_id,
            UserNamePreference.user_id == current_user.id,
        )
    )
    preference = result.scalar_one_or_none()

    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")

    await session.delete(preference)
    await session.commit()

    return None
