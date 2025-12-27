from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.base import Base

if TYPE_CHECKING:
    from db.models.name import Name


class PopularityHistory(Base):
    """Time-series popularity data for names by region and year.

    This table is optimized for time-series queries and can use TimescaleDB
    extension for better performance on large datasets.
    """

    __tablename__ = "popularity_history"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign key
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), index=True)

    # Time dimension
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    # Geographic dimensions
    country: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    state_province: Mapped[str | None] = mapped_column(String(100), index=True)
    city: Mapped[str | None] = mapped_column(String(100), index=True)

    # Popularity metrics
    rank: Mapped[int | None] = mapped_column(Integer)  # 1 = most popular
    count: Mapped[int | None] = mapped_column(Integer)  # Absolute number of babies
    percentage: Mapped[float | None] = mapped_column(
        Numeric(10, 6)
    )  # Percentage of total births
    per_100k: Mapped[float | None] = mapped_column(
        Numeric(10, 2)
    )  # Normalized per 100k births

    # Metadata
    source: Mapped[str | None] = mapped_column(String(100))  # e.g., "SSA", "ONS", "UN"
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    name: Mapped["Name"] = relationship(back_populates="popularity_history")

    # Indexes for time-series queries
    __table_args__ = (
        Index("idx_popularity_time_series", "name_id", "year", "country"),
        Index("idx_popularity_location", "country", "state_province", "year"),
        Index("idx_popularity_rank", "year", "country", "rank"),
    )

    def __repr__(self) -> str:
        return (
            f"<PopularityHistory(name_id={self.name_id}, "
            f"year={self.year}, country='{self.country}', rank={self.rank})>"
        )
