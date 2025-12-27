from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.base import Base

if TYPE_CHECKING:
    from db.models.name import Name


class UserNamePreference(Base):
    """User preferences for names (favorites, ratings, custom lists).

    Note: user_id is a UUID from the users_db, stored here for reference.
    We can't use a foreign key since it's in a different database.
    """

    __tablename__ = "user_name_preferences"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), index=True, nullable=False
    )  # References users table in users_db
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), index=True)

    # Preference data
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5 stars
    category: Mapped[str | None] = mapped_column(
        String(50), index=True
    )  # top_picks, maybe, rejected, shortlist
    notes: Mapped[str | None] = mapped_column(Text)  # Personal notes
    tags: Mapped[str | None] = mapped_column(Text)  # Comma-separated tags for organization

    # Sharing
    is_shared: Mapped[bool] = mapped_column(default=False)  # Shared with partner
    partner_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True)
    )  # Partner's user_id if shared

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    name: Mapped["Name"] = relationship(back_populates="user_preferences")

    __table_args__ = (
        Index("idx_user_preferences", "user_id", "name_id", unique=True),
        Index("idx_user_category", "user_id", "category"),
        Index("idx_user_rating", "user_id", "rating"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )

    def __repr__(self) -> str:
        return f"<UserNamePreference(user_id={self.user_id}, name_id={self.name_id}, rating={self.rating})>"


class Comment(Base):
    """User comments and reviews on names."""

    __tablename__ = "comments"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), index=True, nullable=False
    )  # References users table in users_db
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), index=True)

    # Comment data
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_public: Mapped[bool] = mapped_column(default=True)  # Public or private note

    # Moderation
    is_flagged: Mapped[bool] = mapped_column(default=False)
    is_approved: Mapped[bool] = mapped_column(default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    name: Mapped["Name"] = relationship(back_populates="comments")

    __table_args__ = (
        Index("idx_comment_user", "user_id", "created_at"),
        Index("idx_comment_name", "name_id", "created_at"),
        Index("idx_comment_public", "is_public", "is_approved", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, user_id={self.user_id}, name_id={self.name_id})>"
