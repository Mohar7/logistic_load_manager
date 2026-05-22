# app/bot/utils/error_handling.py
import functools
import logging
from collections.abc import Callable
from typing import Any

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

logger = logging.getLogger(__name__)


def safe_callback_handler(func: Callable) -> Callable:
    """Decorator for safe callback handling with error management."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception:
            logger.exception("Error in %s", func.__name__)

            # Try to find callback in args
            callback = None
            for arg in args:
                if isinstance(arg, CallbackQuery):
                    callback = arg
                    break

            if callback:
                try:
                    await callback.message.edit_text(
                        "❌ An error occurred while processing your request.\n\n"
                        "Please try again or use /start to return to the main menu.",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="🔙 Back to Menu",
                                        callback_data="back_to_menu",
                                    )
                                ]
                            ]
                        ),
                    )
                    await callback.answer("Error occurred!", show_alert=True)
                except Exception:
                    logger.debug(
                        "Failed to send error fallback message", exc_info=True
                    )

            return None

    return wrapper


def safe_message_handler(func: Callable) -> Callable:
    """Decorator for safe message handling with error management."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception:
            logger.exception("Error in %s", func.__name__)

            # Try to find message in args
            message = None
            for arg in args:
                if isinstance(arg, Message):
                    message = arg
                    break

            if message:
                try:
                    await message.answer(
                        "❌ An error occurred while processing your message.\n\n"
                        "Please try again or use /start to return to the main menu."
                    )
                except Exception:
                    logger.debug(
                        "Failed to send error fallback message", exc_info=True
                    )

            return None

    return wrapper


class CallbackDataValidator:
    """Utility class for validating callback data."""

    @staticmethod
    def validate_callback_data(
        callback_data: str,
        expected_parts: int,
        expected_prefix: str | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate callback data format and return parsed parts.

        Args:
            callback_data: The callback data string.
            expected_parts: Expected number of parts when split by '_'.
            expected_prefix: Expected prefix (optional).

        Returns:
            (is_valid, parts_list)
        """
        try:
            parts = callback_data.split("_")

            if len(parts) < expected_parts:
                logger.warning(
                    "Callback data has insufficient parts: %s", callback_data
                )
                return False, []

            if expected_prefix and not callback_data.startswith(expected_prefix):
                logger.warning(
                    "Callback data has wrong prefix: %s", callback_data
                )
                return False, []

            # Validate that numeric parts are actually numeric. We don't fail
            # on this — some parts are legitimately non-numeric (actions).
            for i, part in enumerate(parts):
                if i > 0:
                    try:
                        int(part)
                    except ValueError:
                        # Non-numeric part is acceptable here.
                        continue

            return True, parts

        except Exception:
            logger.exception(
                "Error validating callback data '%s'", callback_data
            )
            return False, []

    @staticmethod
    def safe_int_conversion(value: str, default: int = 0) -> int:
        """Safely convert string to int with default fallback."""
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(
                "Failed to convert '%s' to int, using default %d", value, default
            )
            return default

    @staticmethod
    def extract_load_id(callback_data: str) -> int:
        """Extract load ID from callback data safely."""
        is_valid, parts = CallbackDataValidator.validate_callback_data(
            callback_data, 3
        )
        if is_valid and len(parts) >= 3:
            return CallbackDataValidator.safe_int_conversion(parts[2])
        return 0

    @staticmethod
    def extract_driver_id(callback_data: str) -> int:
        """Extract driver ID from callback data safely."""
        is_valid, parts = CallbackDataValidator.validate_callback_data(
            callback_data, 4
        )
        if is_valid and len(parts) >= 4:
            return CallbackDataValidator.safe_int_conversion(parts[3])
        return 0

    @staticmethod
    def extract_company_id(callback_data: str) -> int:
        """Extract company ID from callback data safely."""
        is_valid, parts = CallbackDataValidator.validate_callback_data(
            callback_data, 3
        )
        if is_valid and len(parts) >= 3:
            return CallbackDataValidator.safe_int_conversion(parts[2])
        return 0


class DatabaseSessionManager:
    """Utility for safe database session management."""

    @staticmethod
    def safe_db_operation(func: Callable) -> Callable:
        """Decorator for safe database operations with session management."""

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            db = kwargs.get("db")
            try:
                result = await func(*args, **kwargs)

                if db is not None and hasattr(db, "commit"):
                    try:
                        db.commit()
                    except Exception:
                        logger.debug(
                            "DB commit failed (already committed?)",
                            exc_info=True,
                        )

                return result

            except Exception:
                if db is not None and hasattr(db, "rollback"):
                    try:
                        db.rollback()
                    except Exception:
                        logger.debug(
                            "DB rollback failed (already rolled back?)",
                            exc_info=True,
                        )

                logger.exception("Database error in %s", func.__name__)
                raise

        return wrapper


class UserPermissionChecker:
    """Utility for checking user permissions safely."""

    @staticmethod
    def require_role(required_role: str) -> Callable:
        """Decorator to require specific user role."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                user_data = kwargs.get("user_data")

                if not user_data:
                    logger.warning(
                        "No user data provided for %s", func.__name__
                    )
                    return await UserPermissionChecker._handle_access_denied(
                        *args, **kwargs
                    )

                if user_data.get("role") != required_role:
                    logger.warning(
                        "User %s attempted to access %s without %s role",
                        user_data.get("name", "Unknown"),
                        func.__name__,
                        required_role,
                    )
                    return await UserPermissionChecker._handle_access_denied(
                        *args, **kwargs
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    async def _handle_access_denied(*args: Any, **kwargs: Any) -> None:
        """Handle access denied scenarios."""
        callback = None
        for arg in args:
            if isinstance(arg, CallbackQuery):
                callback = arg
                break

        if callback:
            try:
                await callback.answer("Access denied!", show_alert=True)
                return
            except Exception:
                logger.debug(
                    "Failed to send access-denied callback", exc_info=True
                )

        message = None
        for arg in args:
            if isinstance(arg, Message):
                message = arg
                break

        if message:
            try:
                await message.answer(
                    "❌ Access denied! You don't have permission for this action."
                )
                return
            except Exception:
                logger.debug(
                    "Failed to send access-denied message", exc_info=True
                )


# ---------- Helpers ----------


def truncate_text(text: str, max_length: int = 4000) -> str:
    """Truncate text to fit Telegram message limits."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """Split long messages into chunks for Telegram."""
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    current_chunk = ""

    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + "\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
