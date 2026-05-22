# app/bot/services/chat_service.py
import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, TelegramChat

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing Telegram chats"""

    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def add_telegram_chat(
        self,
        chat_id: int,
        chat_title: str,
        chat_type: str,
        company_id: int | None = None,
    ) -> bool:
        """Add a new Telegram chat"""
        try:
            # Check if chat already exists
            existing_chat = (
                await self.db.execute(
                    select(TelegramChat).where(TelegramChat.chat_token == chat_id)
                )
            ).scalar_one_or_none()

            if existing_chat:
                return False

            # Get default company if none specified
            if not company_id:
                company = (
                    await self.db.execute(select(Company))
                ).scalars().first()
                company_id = company.id if company else None

            new_chat = TelegramChat(
                group_name=chat_title, chat_token=chat_id, company_id=company_id
            )

            self.db.add(new_chat)
            await self.db.commit()
            await self.db.refresh(new_chat)

            logger.info(f"Added Telegram chat: {chat_title} (ID: {chat_id})")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error adding Telegram chat: {e}")
            await self.db.rollback()
            return False

    async def remove_telegram_chat(self, chat_id: int) -> bool:
        """Remove a Telegram chat"""
        try:
            chat = (
                await self.db.execute(
                    select(TelegramChat).where(TelegramChat.chat_token == chat_id)
                )
            ).scalar_one_or_none()

            if not chat:
                return False

            await self.db.delete(chat)
            await self.db.commit()

            logger.info(f"Removed Telegram chat: {chat.group_name}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error removing Telegram chat: {e}")
            await self.db.rollback()
            return False

    async def get_all_chats(self) -> list[TelegramChat]:
        """Get all Telegram chats"""
        try:
            result = await self.db.execute(select(TelegramChat))
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting chats: {e}")
            return []

    async def get_chat_by_id(self, chat_id: int) -> TelegramChat | None:
        """Get chat by ID"""
        try:
            return (
                await self.db.execute(
                    select(TelegramChat).where(TelegramChat.chat_token == chat_id)
                )
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting chat: {e}")
            return None
