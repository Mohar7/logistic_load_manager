# app/bot/services/chat_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.db.models import TelegramChat, Company
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing Telegram chats"""

    def __init__(self, db: Session):
        self.db = db

    async def add_telegram_chat(
        self,
        chat_id: int,
        chat_title: str,
        chat_type: str,
        company_id: Optional[int] = None,
    ) -> bool:
        """Add a new Telegram chat"""
        try:
            # Check if chat already exists
            existing_chat = (
                self.db.query(TelegramChat)
                .filter(TelegramChat.chat_token == chat_id)
                .first()
            )

            if existing_chat:
                return False

            # Get default company if none specified
            if not company_id:
                company = self.db.query(Company).first()
                company_id = company.id if company else None

            new_chat = TelegramChat(
                group_name=chat_title, chat_token=chat_id, company_id=company_id
            )

            self.db.add(new_chat)
            self.db.commit()
            self.db.refresh(new_chat)

            logger.info(f"Added Telegram chat: {chat_title} (ID: {chat_id})")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error adding Telegram chat: {e}")
            self.db.rollback()
            return False

    async def remove_telegram_chat(self, chat_id: int) -> bool:
        """Remove a Telegram chat"""
        try:
            chat = (
                self.db.query(TelegramChat)
                .filter(TelegramChat.chat_token == chat_id)
                .first()
            )

            if not chat:
                return False

            self.db.delete(chat)
            self.db.commit()

            logger.info(f"Removed Telegram chat: {chat.group_name}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error removing Telegram chat: {e}")
            self.db.rollback()
            return False

    async def get_all_chats(self) -> List[TelegramChat]:
        """Get all Telegram chats"""
        try:
            return self.db.query(TelegramChat).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting chats: {e}")
            return []

    async def get_chat_by_id(self, chat_id: int) -> Optional[TelegramChat]:
        """Get chat by ID"""
        try:
            return (
                self.db.query(TelegramChat)
                .filter(TelegramChat.chat_token == chat_id)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting chat: {e}")
            return None
