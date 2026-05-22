# app/bot/main.py - Updated with unified management
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.admin import AdminHandler

# Handlers - Updated imports
from app.bot.handlers.dispatcher import DispatcherHandler, NotificationStates
from app.bot.handlers.management import ManagementStates, UnifiedManagementHandler

# Middleware
from app.bot.middleware.auth import AuthMiddleware
from app.bot.middleware.database import DatabaseMiddleware

# Services
from app.bot.services.user_service import UserService

# Utils
from app.bot.utils.formatters import escape_markdown

# Config and database
from app.config import get_settings
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()

# Bot initialization
bot = Bot(token=settings.telegram_bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# States for bot conversations
class RegistrationStates(StatesGroup):
    waiting_for_role = State()
    waiting_for_name = State()
    waiting_for_company_selection = State()
    waiting_for_admin_approval = State()


# Middleware setup
dp.message.middleware(DatabaseMiddleware())
dp.callback_query.middleware(DatabaseMiddleware())
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())


# Enhanced main menu functions
def get_enhanced_dispatcher_menu() -> InlineKeyboardMarkup:
    """Enhanced dispatcher menu with cross-company features"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 All Loads", callback_data="all_loads")],
            [InlineKeyboardButton(text="🚛 Unassigned Loads", callback_data="unassigned_loads")],
            [
                InlineKeyboardButton(text="👥 All Drivers", callback_data="all_drivers"),
                InlineKeyboardButton(text="🏢 Companies", callback_data="all_companies")
            ],
            [
                InlineKeyboardButton(text="📢 Notifications", callback_data="send_notifications"),
                InlineKeyboardButton(text="📊 Statistics", callback_data="system_stats")
            ],
            [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")]
        ]
    )


def get_main_menu(user_role: str) -> InlineKeyboardMarkup:
    """Generate main menu based on user role"""
    buttons = []

    if user_role == "manager":
        buttons.extend([
            [InlineKeyboardButton(text="💬 Manage Chats", callback_data="manage_groups")],
            [InlineKeyboardButton(text="👤 Manage Drivers", callback_data="manage_drivers")],
            [InlineKeyboardButton(text="👥 Manage Users", callback_data="manage_users")],
            [InlineKeyboardButton(text="🏢 Manage Companies", callback_data="manage_companies")],
            [InlineKeyboardButton(text="📊 View Statistics", callback_data="view_stats")],
        ])
    elif user_role == "dispatcher":
        # Use enhanced dispatcher menu with cross-company access
        return get_enhanced_dispatcher_menu()

    buttons.append([InlineKeyboardButton(text="ℹ️ Help", callback_data="help")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===================== BASIC COMMAND HANDLERS =====================


@dp.message(Command("start"))
async def start_command(message: types.Message, db: AsyncSession, user_data: dict):
    """Handle /start command"""
    if user_data:
        # User is already registered
        await message.answer(
            f"Welcome back, {user_data['name']}!\n"
            f"Role: {user_data['role'].title()}\n\n"
            "Choose an option:",
            reply_markup=get_main_menu(user_data["role"]),
        )
    else:
        # New user registration
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👤 Register as Dispatcher", callback_data="register_dispatcher")],
                [InlineKeyboardButton(text="👑 Register as Manager", callback_data="register_manager")],
            ]
        )

        await message.answer(
            "Welcome to the Logistics Bot! 🚛\n\n"
            "To get started, please select your role:",
            reply_markup=keyboard,
        )


@dp.message(Command("help"))
async def help_command(message: types.Message, user_data: dict):
    """Handle /help command"""
    help_text = """
🤖 Logistics Bot Help

**Available Commands:**
/start - Main menu
/help - Show this help message

**For Managers:**
💬 Manage Chats - Add/manage Telegram chats
👤 Manage Drivers - Add drivers and assign chats
👥 Manage Users - Manage user accounts
🏢 Manage Companies - Company management
📊 View Statistics - System statistics

**For Dispatchers:**
📋 All Loads - View all loads across companies
🚛 Unassigned Loads - Quick access to unassigned loads
👥 All Drivers - View all drivers (cross-company access)
🏢 Companies - View all companies and statistics
📢 Notifications - Send messages to drivers
📊 Statistics - System-wide statistics

**Key Features:**
• One chat per driver system
• Cross-company driver assignments
• Real-time notifications
• Comprehensive management tools

**Support:**
If you need assistance, contact your system administrator.
    """

    if user_data:
        await message.answer(help_text, reply_markup=get_main_menu(user_data["role"]))
    else:
        await message.answer(help_text)


# ===================== REGISTRATION HANDLERS =====================


@dp.callback_query(F.data.startswith("register_"))
async def handle_registration(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Handle role registration"""
    role = callback.data.split("_")[1]

    await state.update_data(role=role)
    await state.set_state(RegistrationStates.waiting_for_name)

    await callback.message.edit_text(
        f"You selected: {role.title()}\n\nPlease enter your full name:"
    )
    await callback.answer()


@dp.message(StateFilter(RegistrationStates.waiting_for_name))
async def handle_name_input(message: types.Message, state: FSMContext, db: AsyncSession):
    """Handle name input during registration"""
    user_service = UserService(db)
    state_data = await state.get_data()

    try:
        # Create user registration request
        success = await user_service.create_user_registration(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=message.text.strip(),
            role=state_data["role"],
        )

        if success:
            if state_data["role"] == "manager":
                await message.answer(
                    "✅ Manager registration completed!\n\n"
                    "You now have manager access. Use /start to begin."
                )
            else:
                companies = await user_service.get_companies()
                if companies:
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text=company.name, callback_data=f"company_{company.id}")]
                            for company in companies
                        ]
                    )

                    await state.set_state(RegistrationStates.waiting_for_company_selection)
                    await message.answer(
                        "Please select your primary company (for reference - you'll have access to all companies):",
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(
                        "✅ Dispatcher registration completed!\n\n"
                        "You now have cross-company access to all loads and drivers. Use /start to begin."
                    )
                    await state.clear()
        else:
            await message.answer(
                "❌ Registration failed. You may already be registered or there was an error."
            )
            await state.clear()

    except Exception as e:
        logger.error(f"Registration error: {e}")
        await message.answer(
            "❌ An error occurred during registration. Please try again later."
        )
        await state.clear()


@dp.callback_query(F.data.startswith("company_"), StateFilter(RegistrationStates.waiting_for_company_selection))
async def handle_company_selection(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    """Handle company selection during dispatcher registration"""
    company_id = int(callback.data.split("_")[1])
    state_data = await state.get_data()

    user_service = UserService(db)

    try:
        success = await user_service.complete_dispatcher_registration(
            telegram_id=callback.from_user.id,
            company_id=company_id,
            name=state_data.get("name", callback.from_user.full_name),
        )

        if success:
            await callback.message.edit_text(
                "✅ Registration completed successfully!\n\n"
                "You now have **cross-company access** to all loads and drivers in the system.\n"
                "Use /start to begin managing loads across all companies.",
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text("❌ Registration failed. Please try again later.")

    except Exception as e:
        logger.error(f"Company selection error: {e}")
        await callback.message.edit_text("❌ An error occurred during registration. Please try again later.")

    await state.clear()
    await callback.answer()


# ===================== MAIN MENU HANDLERS =====================


@dp.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery, user_data: dict):
    """Handle back to main menu"""
    if not user_data:
        await callback.message.edit_text("❌ You are not registered. Use /start to register.")
        return

    await callback.message.edit_text(
        f"Welcome back, {user_data['name']}!\n"
        f"Role: {user_data['role'].title()}\n\n"
        "Choose an option:",
        reply_markup=get_main_menu(user_data["role"]),
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def handle_help(callback: CallbackQuery, user_data: dict):
    """Handle help command"""
    help_text = """
🤖 Logistics Bot Help

**Available Commands:**
/start - Main menu
/help - Show this help message

**For Managers:**
💬 Manage Chats - Add/manage Telegram chats
👤 Manage Drivers - Add drivers and assign chats
👥 Manage Users - Manage user accounts
🏢 Manage Companies - Company management
📊 View Statistics - System statistics

**For Dispatchers:**
📋 All Loads - View all loads across companies
🚛 Unassigned Loads - Quick access to unassigned loads
👥 All Drivers - View all drivers (cross-company access)
🏢 Companies - View all companies and statistics
📢 Notifications - Send messages to drivers
📊 Statistics - System-wide statistics

**Key Features:**
• One chat per driver system
• Cross-company driver assignments
• Real-time notifications
• Comprehensive management tools

**Support:**
If you need assistance, contact your system administrator.
    """

    await callback.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]]
        ),
    )
    await callback.answer()


# ===================== MANAGER HANDLERS =====================


@dp.callback_query(F.data == "manage_groups")
async def handle_manage_groups(callback: CallbackQuery, user_data: dict):
    """Handle chat management menu"""
    if not user_data or user_data["role"] != "manager":
        await callback.answer("Access denied!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add Chat", callback_data="add_group")],
            [InlineKeyboardButton(text="📋 List Chats", callback_data="list_groups")],
            [InlineKeyboardButton(text="🔗 Assign Chat to Driver", callback_data="assign_chat_to_driver")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")],
        ]
    )

    await callback.message.edit_text("💬 Chat Management\n\nChoose an action:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "manage_drivers")
async def handle_manage_drivers(callback: CallbackQuery, user_data: dict, db: AsyncSession):
    """Handle driver management menu"""
    if not user_data or user_data["role"] != "manager":
        await callback.answer("Access denied!", show_alert=True)
        return

    await UnifiedManagementHandler.handle_manage_drivers(callback, user_data, db)


@dp.callback_query(F.data == "manage_users")
async def handle_manage_users(callback: CallbackQuery, user_data: dict, db: AsyncSession):
    """Handle user management"""
    if not user_data or user_data["role"] != "manager":
        await callback.answer("Access denied!", show_alert=True)
        return

    try:
        from app.db.models import Dispatchers

        result = await db.execute(select(Dispatchers))
        users = list(result.scalars().all())

        if not users:
            text = "👤 No users found."
        else:
            managers = [u for u in users if u.role == "manager"]
            dispatchers = [u for u in users if u.role == "dispatcher"]

            text = "*Registered Users:*\n\n"

            if managers:
                text += "*👑 Managers:*\n"
                for manager in managers:
                    name_escaped = escape_markdown(manager.name)
                    text += f"• {name_escaped} (ID: {manager.telegram_id})\n"
                text += "\n"

            if dispatchers:
                text += "*👤 Dispatchers:*\n"
                for dispatcher in dispatchers:
                    name_escaped = escape_markdown(dispatcher.name)
                    text += f"• {name_escaped} (ID: {dispatcher.telegram_id})\n"
                text += "\n"

            text += f"*Total:* {len(users)} users ({len(managers)} managers, {len(dispatchers)} dispatchers)"

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]]
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Error managing users: {e}")
        await callback.message.edit_text(
            "❌ Error retrieving users.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]]
            ),
        )

    await callback.answer()


@dp.callback_query(F.data == "manage_companies")
async def handle_manage_companies(callback: CallbackQuery, user_data: dict, db: AsyncSession):
    """Handle company management"""
    if not user_data or user_data["role"] != "manager":
        await callback.answer("Access denied!", show_alert=True)
        return

    try:
        from app.db.models import Company

        result = await db.execute(select(Company))
        companies = list(result.scalars().all())

        text = "🏢 *Companies:*\n\n"
        for company in companies:
            company_escaped = escape_markdown(company.name)
            carrier_escaped = escape_markdown(company.carrier_identifier)

            text += f"*{company_escaped}*\n"
            text += f"• DOT: {company.usdot}\n"
            text += f"• MC: {company.mc}\n"
            text += f"• Identifier: {carrier_escaped}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]]
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Error managing companies: {e}")
        await callback.message.edit_text(
            "❌ Error retrieving companies.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]]
            ),
        )

    await callback.answer()


@dp.callback_query(F.data == "view_stats")
async def handle_stats_callback(callback: CallbackQuery, db: AsyncSession, user_data: dict):
    """Handle view statistics callback"""
    if not user_data or user_data["role"] != "manager":
        await callback.answer("Access denied!", show_alert=True)
        return

    await AdminHandler.handle_system_stats(callback, db)


# ===================== UNIFIED MANAGEMENT HANDLERS =====================

# Chat Management Handlers
@dp.callback_query(F.data == "add_group")
async def handle_add_group(callback: CallbackQuery, state: FSMContext, user_data: dict):
    await UnifiedManagementHandler.handle_add_group_menu(callback, state, user_data)

@dp.callback_query(F.data == "add_by_username")
async def handle_add_by_username(callback: CallbackQuery, state: FSMContext):
    await UnifiedManagementHandler.handle_add_by_username(callback, state)

@dp.callback_query(F.data == "add_by_chat_id")
async def handle_add_by_chat_id(callback: CallbackQuery, state: FSMContext):
    await UnifiedManagementHandler.handle_add_by_chat_id(callback, state)

@dp.callback_query(F.data == "add_by_forward")
async def handle_add_by_forward(callback: CallbackQuery, state: FSMContext):
    await UnifiedManagementHandler.handle_add_by_forward(callback, state)

@dp.callback_query(F.data == "confirm_add_chat")
async def handle_confirm_add_chat(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    await UnifiedManagementHandler.handle_confirm_add_chat(callback, state, db)

@dp.callback_query(F.data == "cancel_add_chat")
async def handle_cancel_add_chat(callback: CallbackQuery, state: FSMContext):
    await UnifiedManagementHandler.handle_cancel_add_chat(callback, state)

@dp.callback_query(F.data == "list_groups")
async def handle_list_groups(callback: CallbackQuery, db: AsyncSession, user_data: dict):
    await UnifiedManagementHandler.handle_list_groups(callback, db, user_data)

# Driver Management Handlers
@dp.callback_query(F.data == "add_driver")
async def handle_add_driver(callback: CallbackQuery, state: FSMContext):
    await UnifiedManagementHandler.handle_add_driver(callback, state)

@dp.callback_query(F.data.startswith("select_company_"))
async def handle_company_selection_for_driver(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    await UnifiedManagementHandler.handle_company_selection(callback, state, db)

@dp.callback_query(F.data == "confirm_create_driver")
async def handle_confirm_create_driver(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    await UnifiedManagementHandler.handle_confirm_create_driver(callback, state, db)

@dp.callback_query(F.data == "cancel_add_driver")
async def handle_cancel_add_driver(callback: CallbackQuery, state: FSMContext):
    await UnifiedManagementHandler.handle_cancel_add_driver(callback, state)

@dp.callback_query(F.data == "list_drivers")
async def handle_list_drivers(callback: CallbackQuery, db: AsyncSession):
    await UnifiedManagementHandler.handle_list_drivers(callback, db)

# Driver-Chat Assignment Handlers
@dp.callback_query(F.data == "assign_driver_to_chat")
async def handle_assign_driver_to_chat(callback: CallbackQuery, db: AsyncSession):
    await UnifiedManagementHandler.handle_assign_driver_to_chat(callback, db)

@dp.callback_query(F.data.startswith("select_driver_for_chat_"))
async def handle_select_driver_for_chat(callback: CallbackQuery, db: AsyncSession):
    await UnifiedManagementHandler.handle_select_driver_for_chat(callback, db)

@dp.callback_query(F.data.startswith("confirm_assign_chat_"))
async def handle_confirm_assign_chat(callback: CallbackQuery, db: AsyncSession):
    await UnifiedManagementHandler.handle_confirm_assign_chat(callback, db)

@dp.callback_query(F.data.startswith("assign_chat_to_driver_"))
async def handle_assign_chat_to_specific_driver(callback: CallbackQuery, db: AsyncSession):
    # Extract driver ID and redirect to chat selection
    driver_id = int(callback.data.split("_")[4])
    # Modify callback data to match expected format
    callback.data = f"select_driver_for_chat_{driver_id}"
    await UnifiedManagementHandler.handle_select_driver_for_chat(callback, db)

# Message handlers for management states
@dp.message(StateFilter(ManagementStates.waiting_for_username))
async def handle_username_message(message: types.Message, state: FSMContext, db: AsyncSession):
    await UnifiedManagementHandler.handle_username_input(message, state, db)

@dp.message(StateFilter(ManagementStates.waiting_for_chat_id))
async def handle_chat_id_message(message: types.Message, state: FSMContext, db: AsyncSession):
    await UnifiedManagementHandler.handle_chat_id_input(message, state, db)

@dp.message(StateFilter(ManagementStates.waiting_for_forward))
async def handle_forward_message_input(message: types.Message, state: FSMContext, db: AsyncSession):
    await UnifiedManagementHandler.handle_forward_message(message, state, db)

@dp.message(StateFilter(ManagementStates.waiting_for_driver_name))
async def handle_driver_name_message(message: types.Message, state: FSMContext, db: AsyncSession):
    await UnifiedManagementHandler.handle_driver_name_input(message, state, db)


# ===================== DISPATCHER MENU HANDLERS =====================


@dp.callback_query(F.data == "all_loads")
async def handle_all_loads(callback: CallbackQuery, db: AsyncSession, user_data: dict):
    await DispatcherHandler.handle_all_loads(callback, db, user_data)

@dp.callback_query(F.data == "unassigned_loads")
async def handle_unassigned_loads(callback: CallbackQuery, db: AsyncSession, user_data: dict):
    await DispatcherHandler.handle_unassigned_loads(callback, db, user_data)

@dp.callback_query(F.data == "all_drivers")
async def handle_all_drivers(callback: CallbackQuery, db: AsyncSession, user_data: dict):
    await DispatcherHandler.handle_all_drivers(callback, db, user_data)

@dp.callback_query(F.data == "all_companies")
async def handle_all_companies(callback: CallbackQuery, db: AsyncSession, user_data: dict):
    await DispatcherHandler.handle_all_companies(callback, db, user_data)

@dp.callback_query(F.data.startswith("company_details_"))
async def handle_company_details(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_company_details(callback, db)

@dp.callback_query(F.data == "system_stats")
async def handle_system_stats(callback: CallbackQuery, db: AsyncSession, user_data: dict):
    await DispatcherHandler.handle_system_stats(callback, db, user_data)

@dp.callback_query(F.data == "send_notifications")
async def handle_send_notifications(callback: CallbackQuery, user_data: dict):
    await DispatcherHandler.handle_send_notifications(callback, user_data)

@dp.callback_query(F.data == "send_to_driver")
async def handle_send_to_driver(callback: CallbackQuery, user_data: dict, db: AsyncSession):
    await DispatcherHandler.handle_send_to_driver(callback, user_data, db)


# ===================== DETAILED DISPATCHER HANDLERS =====================


@dp.callback_query(F.data.startswith("view_load_"))
async def handle_view_load(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_load_details(callback, db)

@dp.callback_query(F.data.startswith("assign_driver_"))
async def handle_assign_driver_callback(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_assign_driver(callback, db)

@dp.callback_query(F.data.startswith("filter_company_"))
async def handle_filter_company_callback(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_filter_by_company(callback, db)

@dp.callback_query(F.data.startswith("company_drivers_"))
async def handle_company_drivers_callback(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_company_drivers(callback, db)

@dp.callback_query(F.data.startswith("show_more_drivers_"))
async def handle_show_more_drivers_callback(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_show_more_drivers(callback, db)

@dp.callback_query(F.data.startswith("select_driver_"))
async def handle_select_driver(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_driver_selection(callback, db)

@dp.callback_query(F.data.startswith("notify_driver_"))
async def handle_notify_driver_callback(callback: CallbackQuery, db: AsyncSession):
    await DispatcherHandler.handle_notify_driver(callback, db)

@dp.callback_query(F.data == "broadcast_message")
async def handle_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    await DispatcherHandler.handle_broadcast_message(callback, state)

@dp.callback_query(F.data == "broadcast_all_drivers")
async def handle_broadcast_all_drivers_callback(callback: CallbackQuery, state: FSMContext):
    await DispatcherHandler.handle_broadcast_all_drivers(callback, state)

@dp.callback_query(F.data == "broadcast_by_company")
async def handle_broadcast_by_company_callback(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
    await DispatcherHandler.handle_broadcast_by_company(callback, state, db)

@dp.callback_query(F.data == "broadcast_telegram_only")
async def handle_broadcast_telegram_only_callback(callback: CallbackQuery, state: FSMContext):
    await DispatcherHandler.handle_broadcast_telegram_only(callback, state)

@dp.callback_query(F.data.startswith("broadcast_company_"))
async def handle_broadcast_company_callback(callback: CallbackQuery, state: FSMContext):
    await DispatcherHandler.handle_company_broadcast_selection(callback, state)

@dp.message(StateFilter(NotificationStates.waiting_for_message))
async def handle_broadcast_input(message: types.Message, state: FSMContext, db: AsyncSession, user_data: dict):
    await DispatcherHandler.handle_broadcast_message_input(message, state, db, user_data)


# ===================== GLOBAL HANDLERS =====================


@dp.message(F.text.lower().in_(["/cancel", "cancel"]))
async def handle_global_cancel(message: types.Message, state: FSMContext):
    """Handle cancel command in any state"""
    await state.clear()
    await message.answer(
        "❌ *Operation Cancelled*\n\n"
        "All pending operations have been cancelled.\n"
        "Use /start to return to the main menu.",
        parse_mode="Markdown",
    )


# ===================== ERROR HANDLER =====================


@dp.error()
async def error_handler(event, exception_info):
    """Global error handler"""
    exception = exception_info.exception
    logger.error(f"Bot error: {exception}")
    logger.error(f"Event: {event}")

    try:
        if hasattr(event, "message") and event.message:
            await event.message.answer(
                "❌ An error occurred\n\n"
                "Something went wrong. Please try again or use /start to return to the main menu."
            )
        elif hasattr(event, "callback_query") and event.callback_query and event.callback_query.message:
            await event.callback_query.message.edit_text(
                "❌ An error occurred\n\n"
                "Something went wrong. Please try again or use /start to return to the main menu."
            )
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

    return True


# ===================== MAIN FUNCTION =====================


async def main():
    """Main bot function"""
    logger.info("Starting Logistics Bot...")

    try:
        # Test bot token and configuration
        me = await bot.get_me()
        logger.info(f"Bot started successfully: @{me.username} ({me.first_name})")
        logger.info(f"Bot ID: {me.id}")
        logger.info(f"Can join groups: {me.can_join_groups}")
        logger.info(f"Can read all group messages: {me.can_read_all_group_messages}")

        # Test database connection
        try:
            from app.db.models import Dispatchers

            async with AsyncSessionLocal() as db:
                user_count = (
                    await db.execute(select(func.count()).select_from(Dispatchers))
                ).scalar_one()
            logger.info(f"Database connected successfully. Users in system: {user_count}")
        except Exception as db_error:
            logger.error(f"Database connection error: {db_error}")
            raise

        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(
            bot,
            polling_timeout=30,
            handle_as_tasks=True,
            allowed_updates=["message", "callback_query"],
        )

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
    finally:
        logger.info("Closing bot session...")
        await bot.session.close()


# ===================== STARTUP FUNCTIONS =====================


def setup_logging():
    """Setup logging configuration"""
    import os

    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("logs/bot.log"), logging.StreamHandler()],
    )

    # Set specific log levels for different modules
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def check_environment():
    """Check environment variables and configuration"""
    required_vars = ["telegram_bot_token", "db_host", "db_user", "db_password", "db_name"]
    missing_vars = []

    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var.upper())

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise ValueError(f"Missing environment variables: {missing_vars}")

    if settings.telegram_bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("Telegram bot token is not set properly")
        raise ValueError("Please set a valid TELEGRAM_BOT_TOKEN")

    logger.info("Environment configuration check passed")


async def test_integrations():
    """Test integrations before starting the bot"""
    try:
        # Test bot token
        test_bot = Bot(token=settings.telegram_bot_token)
        me = await test_bot.get_me()
        await test_bot.session.close()
        logger.info(f"✅ Bot token valid: @{me.username}")

        # Test database
        from app.db.models import Company

        async with AsyncSessionLocal() as db:
            company_count = (
                await db.execute(select(func.count()).select_from(Company))
            ).scalar_one()
        logger.info(f"✅ Database connection valid: {company_count} companies")

        return True

    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False


# ===================== MAIN EXECUTION =====================

if __name__ == "__main__":

    # Setup logging
    setup_logging()

    logger.info("=" * 50)
    logger.info("🤖 LOGISTICS TELEGRAM BOT STARTING")
    logger.info("=" * 50)

    try:
        # Check environment
        check_environment()

        # Test integrations
        if not asyncio.run(test_integrations()):
            logger.error("❌ Integration tests failed. Exiting.")
            exit(1)

        logger.info("🚀 All checks passed. Starting bot...")

        # Run the bot
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        exit(1)
    finally:
        logger.info("👋 Bot shutdown complete")
