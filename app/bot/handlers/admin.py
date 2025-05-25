# app/bot/handlers/admin.py
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from app.bot.services.chat_service import ChatService
import logging

logger = logging.getLogger(__name__)


class AdminHandler:
    """Handler for admin/manager functions"""

    @staticmethod
    async def handle_system_stats(callback: types.CallbackQuery, db: Session):
        """Show system statistics"""
        from app.db.models import Load, Driver, TelegramChat

        try:
            total_loads = db.query(Load).count()
            total_drivers = db.query(Driver).count()
            total_chats = db.query(TelegramChat).count()

            stats_text = f"""
📊 System Statistics

🚛 Total Loads: {total_loads}
👤 Total Drivers: {total_drivers}
💬 Telegram Groups: {total_chats}

Recent Activity:
• Active loads: {db.query(Load).filter(Load.assigned_driver.isnot(None)).count()}
• Unassigned loads: {db.query(Load).filter(Load.assigned_driver.is_(None)).count()}
            """

            await callback.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Back", callback_data="back_to_menu"
                            )
                        ]
                    ]
                ),
            )

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            await callback.message.edit_text(
                "❌ Error retrieving system statistics.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Back", callback_data="back_to_menu"
                            )
                        ]
                    ]
                ),
            )
