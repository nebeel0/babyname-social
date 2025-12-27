from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_manager import UserManager
from db.base import get_users_db
from db.models.user import User


async def get_user_db(
    session: AsyncSession = Depends(get_users_db),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """Dependency to get user database adapter."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """Dependency to get user manager."""
    yield UserManager(user_db)
