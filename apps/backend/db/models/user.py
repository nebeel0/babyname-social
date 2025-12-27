from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from db.base import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model for authentication and profile.

    Inherits from fastapi-users base class which provides:
    - id (UUID, primary key)
    - email (unique)
    - hashed_password
    - is_active
    - is_superuser
    - is_verified
    """

    __tablename__ = "users"

    # Profile fields
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True)

    # Demographics
    country: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    state_province: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    age_range: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # 18-24, 25-34, 35-44, etc.

    # Baby planning (optional)
    expected_due_date: Mapped[Optional[datetime]] = mapped_column()
    partner_user_id: Mapped[Optional[UUID]] = mapped_column()  # Link to partner's account

    # Privacy settings
    profile_visibility: Mapped[str] = mapped_column(
        String(20), default="public"
    )  # public, friends, private
    share_preferences: Mapped[bool] = mapped_column(default=False)  # Share name preferences

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column()

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
