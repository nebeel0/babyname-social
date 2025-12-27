"""Pydantic models for enhanced name data (ethnicity, nicknames, etc.)"""
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class EthnicityProbability(BaseModel):
    """Ethnicity probability distribution for a name"""
    name_id: int
    white_probability: Decimal = Field(default=0, ge=0, le=1)
    black_probability: Decimal = Field(default=0, ge=0, le=1)
    hispanic_probability: Decimal = Field(default=0, ge=0, le=1)
    asian_probability: Decimal = Field(default=0, ge=0, le=1)
    other_probability: Decimal = Field(default=0, ge=0, le=1)

    sample_size: Optional[int] = None
    data_source: str = "Harvard Dataverse 2023"
    confidence_level: Optional[str] = Field(None, description="high, medium, or low")

    class Config:
        from_attributes = True


class NicknameInfo(BaseModel):
    """Nickname/diminutive information"""
    nickname: str
    is_diminutive: bool = True
    popularity_rank: Optional[int] = None

    class Config:
        from_attributes = True


class NameWithEnhancements(BaseModel):
    """Name with all enhancements (ethnicity, nicknames, perception)"""
    id: int
    name: str
    gender: Optional[str] = None
    origin_country: Optional[str] = None
    meaning: Optional[str] = None

    # Enhancements
    ethnicity_data: Optional[EthnicityProbability] = None
    nicknames: Optional[list[NicknameInfo]] = Field(default_factory=list)
    nickname_count: int = 0

    # Flags
    has_ethnicity_data: bool = False
    has_nicknames: bool = False
    has_perception_data: bool = False

    class Config:
        from_attributes = True


class CulturalFitScore(BaseModel):
    """Cultural fit score for a name given user's ethnicity"""
    name_id: int
    name: str
    user_ethnicity: str
    fit_score: float = Field(..., ge=0, le=100, description="0-100 percentage")
    match_probability: float = Field(..., description="Probability for user's ethnicity")

    # Distribution for display
    white_probability: float
    black_probability: float
    hispanic_probability: float
    asian_probability: float
    other_probability: float


class FeatureDescription(BaseModel):
    """Feature description for tooltips"""
    feature_key: str
    display_name: str
    short_description: str
    detailed_explanation: Optional[str] = None
    data_source: Optional[str] = None
    display_order: int

    class Config:
        from_attributes = True
