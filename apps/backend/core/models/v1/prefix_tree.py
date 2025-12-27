from typing import Optional
from pydantic import BaseModel, ConfigDict

from core.models.v1.name import NameRead


class GenderCounts(BaseModel):
    """Gender distribution in a prefix subtree."""

    male: int = 0
    female: int = 0
    unisex: int = 0
    neutral: int = 0


class PopularityRange(BaseModel):
    """Popularity range for names in a prefix subtree."""

    min: float = 0.0
    max: float = 0.0
    avg: float = 0.0


class PrefixNodeRead(BaseModel):
    """Schema for reading a prefix tree node."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prefix: str
    prefix_length: int
    is_complete_name: bool
    name_id: Optional[int] = None

    # Tree structure
    parent_id: Optional[int] = None
    child_count: int = 0
    total_descendants: int = 0

    # Filtering metadata
    gender_counts: dict = {}
    origin_countries: Optional[list[str]] = None
    popularity_range: dict = {}

    # Highlighting support
    match_score: float = 0.0
    is_highlighted: bool = False
    highlight_reason: Optional[str] = None

    # Optional: Include the actual name if this is a complete name
    name: Optional[NameRead] = None

    # Optional: Include children nodes
    children: Optional[list["PrefixNodeRead"]] = None


class PrefixTreeResponse(BaseModel):
    """Response for prefix tree query with filtering."""

    prefix: str
    total_nodes: int
    total_names: int
    max_depth: int

    # Filters applied
    filters_applied: dict = {}

    # Root nodes
    nodes: list[PrefixNodeRead]

    # Optional: Names list if requested
    names: Optional[list[NameRead]] = None


class PrefixTreeFilters(BaseModel):
    """Query filters for prefix tree."""

    # Prefix to start from
    prefix: str = ""

    # Tree depth control
    max_depth: int = 3
    include_children: bool = True

    # Filtering
    gender: Optional[str] = None  # "male", "female", "unisex", "neutral"
    origin_country: Optional[str] = None
    min_popularity: Optional[float] = None
    max_popularity: Optional[float] = None

    # Highlighting
    highlight_prefixes: list[str] = []
    highlight_name_ids: list[int] = []

    # Response control
    include_names: bool = False  # Include full name objects
    names_limit: int = 100  # Limit names returned


class PrefixNamesResponse(BaseModel):
    """Response for getting all names with a specific prefix."""

    prefix: str
    total_count: int
    names: list[NameRead]

    # Metadata about the names
    gender_distribution: GenderCounts
    top_origins: list[str]
    popularity_stats: PopularityRange
