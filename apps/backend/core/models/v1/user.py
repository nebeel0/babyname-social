from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi_users import schemas
from pydantic import EmailStr


class UserRead(schemas.BaseUser[UUID]):
    """Schema for reading user data."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    country: Optional[str] = None
    state_province: Optional[str] = None
    city: Optional[str] = None
    created_at: datetime


class UserCreate(schemas.BaseUserCreate):
    """Schema for user registration."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    country: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user profile."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    country: Optional[str] = None
    state_province: Optional[str] = None
    city: Optional[str] = None
    age_range: Optional[str] = None
    expected_due_date: Optional[datetime] = None
    profile_visibility: Optional[str] = None
