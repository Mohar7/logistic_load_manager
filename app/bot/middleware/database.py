# app/bot/middleware/database.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from app.db.database import SessionLocal


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to provide database session to handlers"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        # Create database session
        db = SessionLocal()
        data["db"] = db

        try:
            # Call the handler
            result = await handler(event, data)
            return result
        finally:
            # Close the session
            db.close()
