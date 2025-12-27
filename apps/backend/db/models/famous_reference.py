from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.base import Base

if TYPE_CHECKING:
    from db.models.name import Name


class FamousReference(Base):
    """Famous people, characters, or historical figures with this name."""

    __tablename__ = "famous_references"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign key
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), index=True)

    # Reference details
    person_name: Mapped[str] = mapped_column(String(300), nullable=False)
    reference_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # historical, celebrity, fictional, royal, religious
    category: Mapped[str | None] = mapped_column(
        String(100)
    )  # actor, musician, politician, character, etc.

    # Biographical info
    birth_year: Mapped[int | None] = mapped_column(Integer, index=True)
    death_year: Mapped[int | None] = mapped_column(Integer)
    nationality: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    achievements: Mapped[str | None] = mapped_column(Text)

    # Source/media info (for fictional characters)
    source_media: Mapped[str | None] = mapped_column(
        String(200)
    )  # Book, Movie, TV show, Game, etc.
    source_title: Mapped[str | None] = mapped_column(String(300))  # Title of the work
    source_year: Mapped[int | None] = mapped_column(Integer)

    # External references
    wikipedia_url: Mapped[str | None] = mapped_column(String(500))
    imdb_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    name: Mapped["Name"] = relationship(back_populates="famous_references")

    __table_args__ = (
        Index("idx_reference_type", "name_id", "reference_type"),
        Index("idx_reference_year", "birth_year"),
    )

    def __repr__(self) -> str:
        return f"<FamousReference(name_id={self.name_id}, person='{self.person_name}', type='{self.reference_type}')>"
