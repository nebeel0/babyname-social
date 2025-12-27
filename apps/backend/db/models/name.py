from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.base import Base

if TYPE_CHECKING:
    from db.models.cultural_context import CulturalContext
    from db.models.famous_reference import FamousReference
    from db.models.name_variant import NameVariant
    from db.models.popularity_history import PopularityHistory
    from db.models.user_preference import UserNamePreference, Comment


class Name(Base):
    """Core name entity with comprehensive metadata."""

    __tablename__ = "names"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    gender: Mapped[str | None] = mapped_column(
        String(20), index=True
    )  # male, female, unisex, neutral
    pronunciation: Mapped[str | None] = mapped_column(String(200))  # IPA notation
    pronunciation_audio_url: Mapped[str | None] = mapped_column(String(500))

    # Etymology
    origin_country: Mapped[str | None] = mapped_column(String(100), index=True)
    origin_culture: Mapped[str | None] = mapped_column(String(100), index=True)
    language_family: Mapped[str | None] = mapped_column(String(100))
    root_words: Mapped[str | None] = mapped_column(Text)  # JSON array of root words
    meaning: Mapped[str | None] = mapped_column(Text)
    etymology_description: Mapped[str | None] = mapped_column(Text)

    # Historical data
    first_recorded_year: Mapped[int | None] = mapped_column()
    peak_popularity_year: Mapped[int | None] = mapped_column()
    peak_popularity_rank: Mapped[int | None] = mapped_column()

    # Aggregate statistics (denormalized for performance)
    total_users_count: Mapped[int] = mapped_column(default=0)  # How many users have this name
    avg_rating: Mapped[float | None] = mapped_column()
    rating_count: Mapped[int] = mapped_column(default=0)
    trending_score: Mapped[float | None] = mapped_column()  # Calculated velocity metric

    # Phonetic characteristics
    syllable_count: Mapped[int | None] = mapped_column()
    name_length: Mapped[int | None] = mapped_column()

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    popularity_history: Mapped[list["PopularityHistory"]] = relationship(
        back_populates="name", cascade="all, delete-orphan"
    )
    variants: Mapped[list["NameVariant"]] = relationship(
        back_populates="name", cascade="all, delete-orphan"
    )
    famous_references: Mapped[list["FamousReference"]] = relationship(
        back_populates="name", cascade="all, delete-orphan"
    )
    cultural_contexts: Mapped[list["CulturalContext"]] = relationship(
        back_populates="name", cascade="all, delete-orphan"
    )
    user_preferences: Mapped[list["UserNamePreference"]] = relationship(
        back_populates="name", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="name", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_name_search", "name"),
        Index("idx_name_origin", "origin_country", "origin_culture"),
        Index("idx_name_gender", "gender"),
        Index("idx_name_trending", "trending_score"),
    )

    def __repr__(self) -> str:
        return f"<Name(id={self.id}, name='{self.name}', gender='{self.gender}')>"
