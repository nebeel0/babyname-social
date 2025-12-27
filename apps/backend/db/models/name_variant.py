from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.base import Base

if TYPE_CHECKING:
    from db.models.name import Name


class NameVariant(Base):
    """Spelling variations, diminutives, and translations of names."""

    __tablename__ = "name_variants"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign key
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), index=True)

    # Variant details
    variant_name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    variant_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # spelling, diminutive, translation, nickname
    language: Mapped[str | None] = mapped_column(String(100))  # Language of the variant
    region: Mapped[str | None] = mapped_column(String(100))  # Geographic region

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    name: Mapped["Name"] = relationship(back_populates="variants")

    __table_args__ = (
        Index("idx_variant_search", "variant_name"),
        Index("idx_variant_type", "name_id", "variant_type"),
    )

    def __repr__(self) -> str:
        return f"<NameVariant(name_id={self.name_id}, variant='{self.variant_name}', type='{self.variant_type}')>"
