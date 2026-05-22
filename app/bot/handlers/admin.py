# app/bot/handlers/admin.py
import logging

from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AdminHandler:
    """Handler for admin/manager functions"""

    @staticmethod
    async def handle_system_stats(callback: types.CallbackQuery, db: AsyncSession):
        """Show system statistics"""
        from app.db.models import Driver, Load, TelegramChat

        try:
            total_loads = (await db.execute(select(func.count()).select_from(Load))).scalar_one()
            total_drivers = (
                await db.execute(select(func.count()).select_from(Driver))
            ).scalar_one()
            total_chats = (
                await db.execute(select(func.count()).select_from(TelegramChat))
            ).scalar_one()
            active_loads = (
                await db.execute(
                    select(func.count()).select_from(Load).where(Load.assigned_driver.isnot(None))
                )
            ).scalar_one()
            unassigned_loads = (
                await db.execute(
                    select(func.count()).select_from(Load).where(Load.assigned_driver.is_(None))
                )
            ).scalar_one()

            stats_text = f"""
📊 System Statistics

🚛 Total Loads: {total_loads}
👤 Total Drivers: {total_drivers}
💬 Telegram Groups: {total_chats}

Recent Activity:
• Active loads: {active_loads}
• Unassigned loads: {unassigned_loads}
            """

            await callback.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ]
                ),
            )

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            await callback.message.edit_text(
                "❌ Error retrieving system statistics.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ]
                ),
            )
