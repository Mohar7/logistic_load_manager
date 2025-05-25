# app/bot/middleware/auth.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.orm import Session
from app.bot.services.user_service import UserService


class AuthMiddleware(BaseMiddleware):
    """Middleware to handle user authentication and authorization"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        db: Session = data.get("db")
        if not db:
            return await handler(event, data)

        user_service = UserService(db)
        user_data = await user_service.get_user_by_telegram_id(event.from_user.id)

        # Add user data to handler data
        data["user_data"] = user_data

        # Call the handler
        return await handler(event, data)
