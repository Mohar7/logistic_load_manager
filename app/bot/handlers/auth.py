# app/bot/handlers/auth.py
import logging

from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuthHandler:
    """Handler for authentication-related commands"""

    @staticmethod
    async def handle_registration_status(message: types.Message, db: AsyncSession, user_data: dict):
        """Check registration status"""
        if user_data:
            await message.answer(
                f"✅ You are registered as: {user_data['role'].title()}\n"
                f"Name: {user_data['name']}"
            )
        else:
            await message.answer("❌ You are not registered. Use /start to register.")
