from typing import Optional
from uuid import UUID

from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from core.settings import get_settings
from db.models.user import User

settings = get_settings()


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """User manager for fastapi-users with custom logic."""

    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request: Optional[Request] = None) -> None:
        """Called after user registration."""
        print(f"User {user.id} has registered.")
        # TODO: Send welcome email
        # TODO: Track registration analytics

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        """Called after password reset request."""
        print(f"User {user.id} has requested password reset. Token: {token}")
        # TODO: Send password reset email

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        """Called after verification request."""
        print(f"Verification requested for user {user.id}. Token: {token}")
        # TODO: Send verification email
