from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Float, Index, Integer, String, Text, ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from db.base import Base

if TYPE_CHECKING:
    from db.models.name import Name


class NamePrefixTree(Base):
    """Prefix tree nodes for efficient name exploration."""

    __tablename__ = "name_prefix_tree"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Prefix information
    prefix: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    prefix_length: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_complete_name: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    name_id: Mapped[int | None] = mapped_column(BigInteger, index=True)

    # Tree structure
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, index=True
    )
    child_count: Mapped[int] = mapped_column(Integer, default=0)
    total_descendants: Mapped[int] = mapped_column(Integer, default=0)

    # Filtering metadata
    gender_counts: Mapped[dict] = mapped_column(
        JSONB,
        default={"male": 0, "female": 0, "unisex": 0, "neutral": 0}
    )
    origin_countries: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    popularity_range: Mapped[dict] = mapped_column(
        JSONB,
        default={"min": 0.0, "max": 0.0, "avg": 0.0}
    )

    # Highlighting support
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_highlighted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    highlight_reason: Mapped[str | None] = mapped_column(String(100))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    # name: Mapped["Name"] = relationship("Name", foreign_keys=[name_id])

    def __repr__(self) -> str:
        return f"<NamePrefixTree(id={self.id}, prefix='{self.prefix}', is_name={self.is_complete_name})>"
