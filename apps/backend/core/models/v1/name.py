from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NameBase(BaseModel):
    """Base schema for Name."""

    name: str
    gender: Optional[str] = None
    pronunciation: Optional[str] = None
    origin_country: Optional[str] = None
    origin_culture: Optional[str] = None
    meaning: Optional[str] = None


class NameCreate(NameBase):
    """Schema for creating a name."""

    pass


class NameUpdate(BaseModel):
    """Schema for updating a name."""

    pronunciation: Optional[str] = None
    origin_country: Optional[str] = None
    origin_culture: Optional[str] = None
    meaning: Optional[str] = None
    etymology_description: Optional[str] = None


class NameRead(NameBase):
    """Schema for reading name data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    etymology_description: Optional[str] = None
    first_recorded_year: Optional[int] = None
    avg_rating: Optional[float] = None
    rating_count: int = 0
    trending_score: Optional[float] = None
    created_at: datetime


class PopularityDataPoint(BaseModel):
    """Single popularity data point."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    rank: Optional[int] = None
    count: Optional[int] = None
    percentage: Optional[float] = None


class NameDetailRead(NameRead):
    """Detailed name information with related data."""

    popularity_history: list[PopularityDataPoint] = []
    # We can add more related data later


class UserPreferenceCreate(BaseModel):
    """Schema for creating user preference."""

    name_id: int
    rating: Optional[int] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class UserPreferenceRead(BaseModel):
    """Schema for reading user preference."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name_id: int
    rating: Optional[int] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
