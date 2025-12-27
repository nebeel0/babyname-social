"""Pydantic models for user profiles (personalization data)"""
from typing import Optional
from pydantic import BaseModel, Field


class UserProfileBase(BaseModel):
    """Base user profile fields"""
    ethnicity: Optional[str] = Field(None, description="User's ethnicity")
    age: Optional[int] = Field(None, ge=13, le=100)

    # Location
    current_state: Optional[str] = Field(None, max_length=2)
    current_city: Optional[str] = Field(None, max_length=100)
    planned_state: Optional[str] = Field(None, max_length=2)
    planned_city: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="US", max_length=2)

    # Family context
    partner_ethnicity: Optional[str] = None
    existing_children_names: Optional[list[str]] = Field(default_factory=list)
    family_surnames: Optional[list[str]] = Field(default_factory=list)

    # Preferences (1-5 scale)
    cultural_importance: int = Field(default=3, ge=1, le=5)
    uniqueness_preference: int = Field(default=3, ge=1, le=5)
    traditional_vs_modern: int = Field(default=3, ge=1, le=5)
    pronunciation_simplicity: int = Field(default=3, ge=1, le=5)

    # Boolean preferences
    nickname_friendly: bool = True
    religious_significance: bool = False
    avoid_discrimination_risk: bool = True

    # Additional preferences
    preferred_name_length: Optional[str] = Field(None, description="short, medium, long, or any")
    preferred_origins: Optional[list[str]] = Field(default_factory=list)
    disliked_sounds: Optional[list[str]] = Field(default_factory=list)


class UserProfileCreate(UserProfileBase):
    """Create a new user profile"""
    user_id: str = Field(..., description="User ID (session or account)")


class UserProfileUpdate(UserProfileBase):
    """Update user profile (all fields optional)"""
    pass


class UserProfileRead(UserProfileBase):
    """User profile response"""
    id: int
    user_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
