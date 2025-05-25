# app/bot/utils/error_handling.py
import logging
import functools
from typing import Callable, Any
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)


def safe_callback_handler(func: Callable) -> Callable:
    """Decorator for safe callback handling with error management"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            
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
                                [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_menu")]
                            ]
                        )
                    )
                    await callback.answer("Error occurred!", show_alert=True)
                except:
                    pass  # If we can't send error message, just log it
            
            return None
    return wrapper


def safe_message_handler(func: Callable) -> Callable:
    """Decorator for safe message handling with error management"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            
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
                except:
                    pass  # If we can't send error message, just log it
            
            return None
    return wrapper


class CallbackDataValidator:
    """Utility class for validating callback data"""
    
    @staticmethod
    def validate_callback_data(callback_data: str, expected_parts: int, expected_prefix: str = None) -> tuple:
        """
        Validate callback data format and return parsed parts
        
        Args:
            callback_data: The callback data string
            expected_parts: Expected number of parts when split by '_'
            expected_prefix: Expected prefix (optional)
            
        Returns:
            tuple: (is_valid, parts_list)
        """
        try:
            parts = callback_data.split("_")
            
            # Check number of parts
            if len(parts) < expected_parts:
                logger.warning(f"Callback data has insufficient parts: {callback_data}")
                return False, []
            
            # Check prefix if specified
            if expected_prefix and not callback_data.startswith(expected_prefix):
                logger.warning(f"Callback data has wrong prefix: {callback_data}")
                return False, []
            
            # Validate that numeric parts are actually numeric
            for i, part in enumerate(parts):
                if i > 0:  # Skip first part (usually the action)
                    try:
                        int(part)
                    except ValueError:
                        # Some parts might not be numeric, that's ok
                        pass
            
            return True, parts
            
        except Exception as e:
            logger.error(f"Error validating callback data '{callback_data}': {e}")
            return False, []
    
    @staticmethod
    def safe_int_conversion(value: str, default: int = 0) -> int:
        """Safely convert string to int with default fallback"""
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert '{value}' to int, using default {default}")
            return default
    
    @staticmethod
    def extract_load_id(callback_data: str) -> int:
        """Extract load ID from callback data safely"""
        is_valid, parts = CallbackDataValidator.validate_callback_data(callback_data, 3)
        if is_valid and len(parts) >= 3:
            return CallbackDataValidator.safe_int_conversion(parts[2])
        return 0
    
    @staticmethod
    def extract_driver_id(callback_data: str) -> int:
        """Extract driver ID from callback data safely"""
        is_valid, parts = CallbackDataValidator.validate_callback_data(callback_data, 4)
        if is_valid and len(parts) >= 4:
            return CallbackDataValidator.safe_int_conversion(parts[3])
        return 0
    
    @staticmethod
    def extract_company_id(callback_data: str) -> int:
        """Extract company ID from callback data safely"""
        is_valid, parts = CallbackDataValidator.validate_callback_data(callback_data, 3)
        if is_valid and len(parts) >= 3:
            return CallbackDataValidator.safe_int_conversion(parts[2])
        return 0


class DatabaseSessionManager:
    """Utility for safe database session management"""
    
    @staticmethod
    def safe_db_operation(func: Callable) -> Callable:
        """Decorator for safe database operations with proper session management"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            db = None
            try:
                # Find db session in kwargs
                if 'db' in kwargs:
                    db = kwargs['db']
                
                result = await func(*args, **kwargs)
                
                # Ensure session is committed if needed
                if db and hasattr(db, 'commit'):
                    try:
                        db.commit()
                    except:
                        pass  # Session might already be committed
                
                return result
                
            except Exception as e:
                # Rollback on error
                if db and hasattr(db, 'rollback'):
                    try:
                        db.rollback()
                    except:
                        pass  # Session might already be rolled back
                
                logger.error(f"Database error in {func.__name__}: {e}")
                raise e
                
        return wrapper


class UserPermissionChecker:
    """Utility for checking user permissions safely"""
    
    @staticmethod
    def require_role(required_role: str):
        """Decorator to require specific user role"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                user_data = kwargs.get('user_data')
                
                if not user_data:
                    logger.warning(f"No user data provided for {func.__name__}")
                    return await UserPermissionChecker._handle_access_denied(*args, **kwargs)
                
                if user_data.get('role') != required_role:
                    logger.warning(f"User {user_data.get('name', 'Unknown')} attempted to access {func.__name__} without {required_role} role")
                    return await UserPermissionChecker._handle_access_denied(*args, **kwargs)
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    async def _handle_access_denied(*args, **kwargs):
        """Handle access denied scenarios"""
        # Try to find callback in args
        callback = None
        for arg in args:
            if isinstance(arg, CallbackQuery):
                callback = arg
                break
        
        if callback:
            try:
                await callback.answer("Access denied!", show_alert=True)
                return
            except:
                pass
        
        # Try to find message in args
        message = None
        for arg in args:
            if isinstance(arg, Message):
                message = arg
                break
        
        if message:
            try:
                await message.answer("❌ Access denied! You don't have permission for this action.")
                return
            except:
                pass


# Additional utility functions
def truncate_text(text: str, max_length: int = 4000) -> str:
    """Truncate text to fit Telegram message limits"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def split_long_message(text: str, max_length: int = 4000) -> list:
    """Split long messages into chunks for Telegram"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks