from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.base import Base

if TYPE_CHECKING:
    from db.models.name import Name


class CulturalContext(Base):
    """Cultural, religious, and mythological significance of names."""

    __tablename__ = "cultural_contexts"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign key
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), index=True)

    # Context type
    context_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # religious, mythological, traditional, saint, nameday

    # Details
    religion: Mapped[str | None] = mapped_column(String(100), index=True)
    culture: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Name day info (for cultures that celebrate name days)
    name_day_month: Mapped[int | None] = mapped_column()  # 1-12
    name_day_day: Mapped[int | None] = mapped_column()  # 1-31

    # Saint info (if applicable)
    saint_name: Mapped[str | None] = mapped_column(String(200))
    saint_feast_day: Mapped[str | None] = mapped_column(String(100))

    # References
    source: Mapped[str | None] = mapped_column(String(200))
    reference_url: Mapped[str | None] = mapped_column(String(500))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    name: Mapped["Name"] = relationship(back_populates="cultural_contexts")

    __table_args__ = (
        Index("idx_cultural_type", "name_id", "context_type"),
        Index("idx_cultural_religion", "religion", "culture"),
    )

    def __repr__(self) -> str:
        return f"<CulturalContext(name_id={self.name_id}, type='{self.context_type}', culture='{self.culture}')>"
