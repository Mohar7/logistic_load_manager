# app/bot/utils/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


class BotKeyboards:
    """Utility class for creating bot keyboards"""

    @staticmethod
    def create_pagination_keyboard(
        items: List[Dict[str, Any]], current_page: int = 0, items_per_page: int = 5
    ) -> InlineKeyboardMarkup:
        """Create a paginated keyboard for long lists"""
        start_idx = current_page * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]

        buttons = []

        # Add item buttons
        for item in page_items:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=item["text"], callback_data=item["callback_data"]
                    )
                ]
            )

        # Add pagination buttons if needed
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Previous", callback_data=f"page_{current_page - 1}"
                )
            )

        if end_idx < len(items):
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Next ➡️", callback_data=f"page_{current_page + 1}"
                )
            )

        if nav_buttons:
            buttons.append(nav_buttons)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_confirmation_keyboard(
        confirm_callback: str, cancel_callback: str = "cancel"
    ) -> InlineKeyboardMarkup:
        """Create a confirmation keyboard"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Confirm", callback_data=confirm_callback
                    ),
                    InlineKeyboardButton(
                        text="❌ Cancel", callback_data=cancel_callback
                    ),
                ]
            ]
        )
