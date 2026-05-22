# app/bot/middleware/database.py
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.db.database import AsyncSessionLocal


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to provide database session to handlers"""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as db:
            data["db"] = db
            return await handler(event, data)
