# app/bot/handlers/management.py - Unified Group and Driver Management
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.bot.services.chat_service import ChatService
from app.bot.utils.formatters import escape_markdown
from app.bot.utils.error_handling import safe_callback_handler, safe_message_handler
from app.db.models import Driver, TelegramChat, Company
import logging

logger = logging.getLogger(__name__)


class ManagementStates(StatesGroup):
    # Group management states
    waiting_for_username = State()
    waiting_for_chat_id = State()
    waiting_for_forward = State()
    confirming_chat_selection = State()
    
    # Driver management states
    waiting_for_driver_name = State()
    waiting_for_company_selection = State()
    confirming_driver_creation = State()
    selecting_chat_for_driver = State()
    confirming_driver_chat_assignment = State()


class UnifiedManagementHandler:
    """Unified handler for both group and driver management"""

    # ==================== GROUP MANAGEMENT ====================
    
    @staticmethod
    @safe_callback_handler
    async def handle_add_group_menu(callback: CallbackQuery, state: FSMContext, user_data: dict):
        """Show different methods to add a group"""
        if not user_data or user_data["role"] != "manager":
            await callback.answer("Access denied!", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Search by Username", callback_data="add_by_username")],
                [InlineKeyboardButton(text="🆔 Enter Chat ID", callback_data="add_by_chat_id")],
                [InlineKeyboardButton(text="📨 Forward Message", callback_data="add_by_forward")],
                [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")],
            ]
        )

        await callback.message.edit_text(
            "➕ *Add New Group/Chat*\n\n"
            "Choose how you want to add a Telegram group or chat:\n\n"
            "🔍 *Search by Username* - Find groups by @username\n"
            "🆔 *Enter Chat ID* - Add by numeric chat ID\n"
            "📨 *Forward Message* - Forward any message from the group\n\n"
            "💡 *Note:* Each chat will be assigned to one driver",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_add_by_username(callback: CallbackQuery, state: FSMContext):
        """Handle adding group by username"""
        await state.set_state(ManagementStates.waiting_for_username)
        await callback.message.edit_text(
            "🔍 *Add Chat by Username*\n\n"
            "Enter the chat username (with or without @):\n\n"
            "*Examples:*\n"
            "• `@driverchat123`\n"
            "• `johndriver_chat`\n\n"
            "*Cancel:* Send /cancel",
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_add_by_chat_id(callback: CallbackQuery, state: FSMContext):
        """Handle adding group by chat ID"""
        await state.set_state(ManagementStates.waiting_for_chat_id)
        await callback.message.edit_text(
            "🆔 *Add Chat by Chat ID*\n\n"
            "Enter the numeric chat ID:\n\n"
            "*Examples:*\n"
            "• `-1001234567890` (group/supergroup)\n"
            "• `123456789` (private chat)\n\n"
            "*How to find Chat ID:*\n"
            "1. Add `@userinfobot` to the chat\n"
            "2. Send `/start`\n"
            "3. Copy the chat ID\n\n"
            "*Cancel:* Send /cancel",
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_add_by_forward(callback: CallbackQuery, state: FSMContext):
        """Handle adding group by forwarding message"""
        await state.set_state(ManagementStates.waiting_for_forward)
        await callback.message.edit_text(
            "📨 *Add Chat by Forward*\n\n"
            "*Instructions:*\n"
            "1. Go to the chat you want to add\n"
            "2. Forward ANY message from that chat to this bot\n"
            "3. Bot will automatically detect the chat info\n\n"
            "*Cancel:* Send /cancel",
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_message_handler
    async def handle_username_input(message: types.Message, state: FSMContext, db: Session):
        """Handle username input for chat addition"""
        if message.text.lower() in ["/cancel", "cancel"]:
            await state.clear()
            await message.answer("❌ Operation cancelled. Use /start to return to menu.")
            return

        username = message.text.strip()
        if not username.startswith("@"):
            username = "@" + username

        try:
            from aiogram import Bot
            from app.config import get_settings

            settings = get_settings()
            bot_instance = Bot(token=settings.telegram_bot_token)

            try:
                chat = await bot_instance.get_chat(username)
                await bot_instance.session.close()

                # Store chat info for confirmation
                await state.update_data(
                    chat_id=chat.id,
                    chat_title=chat.title or chat.first_name or chat.username,
                    chat_username=username,
                    chat_type=chat.type,
                )
                await state.set_state(ManagementStates.confirming_chat_selection)

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Add This Chat", callback_data="confirm_add_chat")],
                        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add_chat")],
                    ]
                )

                chat_name = chat.title or chat.first_name or chat.username
                chat_name_escaped = escape_markdown(chat_name)
                username_escaped = escape_markdown(username)
                
                confirmation_text = (
                    f"🔍 *Found Chat:*\n\n"
                    f"*Name:* {chat_name_escaped}\n"
                    f"*Username:* {username_escaped}\n"
                    f"*Type:* {chat.type.title()}\n"
                    f"*Chat ID:* `{chat.id}`\n\n"
                    f"Add this chat to the system?"
                )

                await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="Markdown")

            except Exception as e:
                await bot_instance.session.close()
                error_msg = str(e)
                if "chat not found" in error_msg.lower():
                    reason = "Chat doesn't exist or username is incorrect"
                elif "forbidden" in error_msg.lower():
                    reason = "Bot doesn't have access to this chat"
                else:
                    reason = f"Error: {error_msg[:100]}"

                await message.answer(
                    f"❌ Cannot find chat: {username}\n\n"
                    f"*Reason:* {reason}\n\n"
                    f"*To fix this:*\n"
                    f"1. Check the username is correct\n"
                    f"2. Add the bot to the chat first\n"
                    f"3. Try using chat ID method instead",
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error in username input: {e}")
            await message.answer("❌ An error occurred while searching. Please try again.")

    @staticmethod
    @safe_message_handler
    async def handle_chat_id_input(message: types.Message, state: FSMContext, db: Session):
        """Handle chat ID input for chat addition"""
        if message.text.lower() in ["/cancel", "cancel"]:
            await state.clear()
            await message.answer("❌ Operation cancelled. Use /start to return to menu.")
            return

        try:
            chat_id = int(message.text.strip())
            
            from aiogram import Bot
            from app.config import get_settings

            settings = get_settings()
            bot_instance = Bot(token=settings.telegram_bot_token)

            try:
                chat = await bot_instance.get_chat(chat_id)
                await bot_instance.session.close()

                # Store chat info for confirmation
                await state.update_data(
                    chat_id=chat.id,
                    chat_title=chat.title or chat.first_name or f"Chat_{chat.id}",
                    chat_username=getattr(chat, "username", None),
                    chat_type=chat.type,
                )
                await state.set_state(ManagementStates.confirming_chat_selection)

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Add This Chat", callback_data="confirm_add_chat")],
                        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add_chat")],
                    ]
                )

                chat_name = chat.title or chat.first_name or f"Chat_{chat.id}"
                chat_name_escaped = escape_markdown(chat_name)
                username_text = f"@{chat.username}" if getattr(chat, "username", None) else "No username"

                confirmation_text = (
                    f"🆔 *Found Chat:*\n\n"
                    f"*Name:* {chat_name_escaped}\n"
                    f"*Username:* {username_text}\n"
                    f"*Type:* {chat.type.title()}\n"
                    f"*Chat ID:* `{chat.id}`\n\n"
                    f"Add this chat to the system?"
                )

                await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="Markdown")

            except Exception as e:
                await bot_instance.session.close()
                error_msg = str(e)
                if "chat not found" in error_msg.lower():
                    error_reason = "Chat ID doesn't exist or is invalid"
                elif "forbidden" in error_msg.lower():
                    error_reason = "Bot doesn't have access to this chat"
                else:
                    error_reason = f"{error_msg[:100]}"

                await message.answer(
                    f"❌ Cannot access chat ID: {chat_id}\n\n"
                    f"*Reason:* {error_reason}\n\n"
                    f"*To fix this:*\n"
                    f"1. Make sure the bot has access to the chat\n"
                    f"2. Try forwarding a message instead\n"
                    f"3. Double-check the chat ID is correct",
                    parse_mode="Markdown"
                )

        except ValueError:
            await message.answer(
                "❌ *Invalid chat ID format*\n\n"
                "Chat ID must be a number.\n\n"
                "*Examples:*\n"
                "• `-1001234567890` (group)\n"
                "• `123456789` (private chat)",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in chat ID input: {e}")
            await message.answer("❌ An error occurred while checking chat ID. Please try again.")

    @staticmethod
    @safe_message_handler
    async def handle_forward_message(message: types.Message, state: FSMContext, db: Session):
        """Handle forwarded message for chat addition"""
        if message.text and message.text.lower() in ["/cancel", "cancel"]:
            await state.clear()
            await message.answer("❌ Operation cancelled. Use /start to return to menu.")
            return

        chat_info = None

        # Check various ways to detect chat information
        if message.forward_from_chat:
            chat_info = message.forward_from_chat
        elif message.sender_chat:
            chat_info = message.sender_chat
        elif message.forward_date:
            await message.answer(
                "🔍 *Forwarded Message Detected*\n\n"
                "The message is forwarded, but privacy settings prevent seeing chat info.\n\n"
                "*Please use:*\n"
                "1. Get chat ID with @userinfobot\n"
                "2. Use 'Enter Chat ID' method",
                parse_mode="Markdown"
            )
            return

        if not chat_info:
            await message.answer(
                "❌ *Cannot detect chat information*\n\n"
                "*Please try:*\n"
                "1. Forward a message from the target chat\n"
                "2. Use 'Enter Chat ID' method\n"
                "3. Use username method if available",
                parse_mode="Markdown"
            )
            return

        # Store chat info for confirmation
        await state.update_data(
            chat_id=chat_info.id,
            chat_title=chat_info.title or getattr(chat_info, 'first_name', f"Chat_{chat_info.id}"),
            chat_username=getattr(chat_info, "username", None),
            chat_type=chat_info.type,
        )
        await state.set_state(ManagementStates.confirming_chat_selection)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Add This Chat", callback_data="confirm_add_chat")],
                [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add_chat")],
            ]
        )

        chat_name = chat_info.title or getattr(chat_info, 'first_name', f"Chat_{chat_info.id}")
        chat_name_escaped = escape_markdown(chat_name)
        username_text = f"@{chat_info.username}" if getattr(chat_info, "username", None) else "No username"

        confirmation_text = (
            f"📨 *Chat Detected:*\n\n"
            f"*Name:* {chat_name_escaped}\n"
            f"*Username:* {username_text}\n"
            f"*Type:* {chat_info.type.title()}\n"
            f"*Chat ID:* `{chat_info.id}`\n\n"
            f"Add this chat to the system?"
        )

        await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="Markdown")

    @staticmethod
    @safe_callback_handler
    async def handle_confirm_add_chat(callback: CallbackQuery, state: FSMContext, db: Session):
        """Confirm and add the selected chat"""
        try:
            state_data = await state.get_data()
            chat_service = ChatService(db)

            success = await chat_service.add_telegram_chat(
                chat_id=state_data["chat_id"],
                chat_title=state_data["chat_title"],
                chat_type=state_data["chat_type"],
            )

            if success:
                chat_name_escaped = escape_markdown(state_data['chat_title'])
                await callback.message.edit_text(
                    f"✅ *Chat Added Successfully!*\n\n"
                    f"*Name:* {chat_name_escaped}\n"
                    f"*Chat ID:* `{state_data['chat_id']}`\n"
                    f"*Type:* {state_data['chat_type'].title()}\n\n"
                    f"🎉 The chat is now in the system!\n"
                    f"You can now assign it to a driver.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="👤 Assign to Driver", callback_data="assign_chat_to_driver")],
                            [InlineKeyboardButton(text="📋 View All Chats", callback_data="list_groups")],
                            [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")],
                        ]
                    ),
                    parse_mode="Markdown",
                )
            else:
                await callback.message.edit_text(
                    f"❌ *Failed to Add Chat*\n\n"
                    f"Chat may already exist in the system.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")]
                        ]
                    ),
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error confirming chat addition: {e}")
            await callback.message.edit_text(
                "❌ *Error Adding Chat*\n\nAn error occurred. Please try again.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")]
                    ]
                ),
                parse_mode="Markdown"
            )

        await state.clear()
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_cancel_add_chat(callback: CallbackQuery, state: FSMContext):
        """Cancel chat addition"""
        await state.clear()
        await callback.message.edit_text(
            "❌ *Chat Addition Cancelled*\n\nNo changes were made.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Try Again", callback_data="add_group")],
                    [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")],
                ]
            ),
            parse_mode="Markdown"
        )
        await callback.answer()

    # ==================== DRIVER MANAGEMENT ====================
    
    @staticmethod
    @safe_callback_handler
    async def handle_manage_drivers(callback: CallbackQuery, user_data: dict, db: Session):
        """Main driver management menu"""
        if not user_data or user_data["role"] != "manager":
            await callback.answer("Access denied!", show_alert=True)
            return

        # Get driver statistics
        total_drivers = db.query(Driver).count()
        drivers_with_chats = db.query(Driver).filter(Driver.chat_id.isnot(None)).count()
        unassigned_chats = db.query(TelegramChat).filter(
            ~TelegramChat.id.in_(db.query(Driver.chat_id).filter(Driver.chat_id.isnot(None)))
        ).count()

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Add New Driver", callback_data="add_driver")],
                [InlineKeyboardButton(text="👤 View All Drivers", callback_data="list_drivers")],
                [InlineKeyboardButton(text="🔗 Assign Driver to Chat", callback_data="assign_driver_to_chat")],
                [InlineKeyboardButton(text="📊 Driver Statistics", callback_data="driver_stats")],
                [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_menu")],
            ]
        )

        stats_text = (
            f"👥 *Driver Management*\n\n"
            f"*Current Statistics:*\n"
            f"• Total Drivers: {total_drivers}\n"
            f"• With Chats: {drivers_with_chats}\n"
            f"• Unassigned Chats: {unassigned_chats}\n\n"
            f"Choose an action:"
        )

        await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_add_driver(callback: CallbackQuery, state: FSMContext):
        """Start driver addition process"""
        await state.set_state(ManagementStates.waiting_for_driver_name)
        await callback.message.edit_text(
            "➕ *Add New Driver*\n\n"
            "Enter the driver's full name:\n\n"
            "*Example:* John Smith\n\n"
            "*Cancel:* Send /cancel",
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    @safe_message_handler
    async def handle_driver_name_input(message: types.Message, state: FSMContext, db: Session):
        """Handle driver name input"""
        if message.text.lower() in ["/cancel", "cancel"]:
            await state.clear()
            await message.answer("❌ Operation cancelled. Use /start to return to menu.")
            return

        driver_name = message.text.strip()
        if len(driver_name) < 2:
            await message.answer("❌ Please enter a valid driver name (at least 2 characters).")
            return

        # Store driver name and show company selection
        await state.update_data(driver_name=driver_name)
        
        # Get available companies
        companies = db.query(Company).all()
        
        if not companies:
            await message.answer("❌ No companies found. Please add a company first.")
            await state.clear()
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=company.name, callback_data=f"select_company_{company.id}")]
                for company in companies
            ] + [[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add_driver")]]
        )

        await state.set_state(ManagementStates.waiting_for_company_selection)
        driver_name_escaped = escape_markdown(driver_name)
        await message.answer(
            f"👤 *Adding Driver: {driver_name_escaped}*\n\n"
            f"Select the company for this driver:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    @staticmethod
    @safe_callback_handler
    async def handle_company_selection(callback: CallbackQuery, state: FSMContext, db: Session):
        """Handle company selection for driver"""
        if not callback.data.startswith("select_company_"):
            await callback.answer("Invalid selection!", show_alert=True)
            return

        company_id = int(callback.data.split("_")[2])
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            await callback.answer("Company not found!", show_alert=True)
            return

        state_data = await state.get_data()
        await state.update_data(company_id=company_id, company_name=company.name)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Create Driver", callback_data="confirm_create_driver")],
                [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add_driver")],
            ]
        )

        driver_name_escaped = escape_markdown(state_data['driver_name'])
        company_name_escaped = escape_markdown(company.name)
        
        await callback.message.edit_text(
            f"👤 *Confirm Driver Creation*\n\n"
            f"*Name:* {driver_name_escaped}\n"
            f"*Company:* {company_name_escaped}\n\n"
            f"Create this driver?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_confirm_create_driver(callback: CallbackQuery, state: FSMContext, db: Session):
        """Confirm and create the driver"""
        try:
            state_data = await state.get_data()
            
            # Create the driver
            new_driver = Driver(
                name=state_data['driver_name'],
                company_id=state_data['company_id'],
                chat_id=None  # Will be assigned later
            )
            
            db.add(new_driver)
            db.commit()
            db.refresh(new_driver)

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 Assign Chat Now", callback_data=f"assign_chat_to_driver_{new_driver.id}")],
                    [InlineKeyboardButton(text="➕ Add Another Driver", callback_data="add_driver")],
                    [InlineKeyboardButton(text="👤 View All Drivers", callback_data="list_drivers")],
                    [InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")],
                ]
            )

            driver_name_escaped = escape_markdown(state_data['driver_name'])
            company_name_escaped = escape_markdown(state_data['company_name'])
            
            await callback.message.edit_text(
                f"✅ *Driver Created Successfully!*\n\n"
                f"*Name:* {driver_name_escaped}\n"
                f"*Company:* {company_name_escaped}\n"
                f"*ID:* {new_driver.id}\n\n"
                f"🎉 Driver added to the system!\n"
                f"You can now assign a chat to this driver.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

        except SQLAlchemyError as e:
            logger.error(f"Error creating driver: {e}")
            db.rollback()
            await callback.message.edit_text(
                "❌ *Error Creating Driver*\n\nDatabase error occurred. Please try again.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")]
                    ]
                ),
                parse_mode="Markdown"
            )

        await state.clear()
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_cancel_add_driver(callback: CallbackQuery, state: FSMContext):
        """Cancel driver addition"""
        await state.clear()
        await callback.message.edit_text(
            "❌ *Driver Addition Cancelled*\n\nNo changes were made.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")]
                ]
            ),
            parse_mode="Markdown"
        )
        await callback.answer()

    # ==================== DRIVER-CHAT ASSIGNMENT ====================
    
    @staticmethod
    @safe_callback_handler
    async def handle_assign_driver_to_chat(callback: CallbackQuery, db: Session):
        """Show drivers without chats for assignment"""
        # Get drivers without chat assignments
        drivers_without_chats = db.query(Driver).filter(Driver.chat_id.is_(None)).all()
        
        if not drivers_without_chats:
            await callback.message.edit_text(
                "✅ *All Drivers Have Chats*\n\n"
                "All drivers are already assigned to chats.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="👤 View All Drivers", callback_data="list_drivers")],
                        [InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")],
                    ]
                ),
                parse_mode="Markdown"
            )
            return

        keyboard_buttons = []
        text = f"🔗 *Assign Chat to Driver*\n\n"
        text += f"Select a driver to assign a chat to:\n\n"

        for driver in drivers_without_chats[:10]:  # Limit to 10 for display
            company_name = driver.company.name if driver.company else "No Company"
            driver_escaped = escape_markdown(driver.name)
            company_escaped = escape_markdown(company_name)
            
            text += f"• {driver_escaped} ({company_escaped})\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"👤 {driver.name} ({company_name})",
                    callback_data=f"select_driver_for_chat_{driver.id}"
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")
        ])

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_select_driver_for_chat(callback: CallbackQuery, db: Session):
        """Select available chat for driver"""
        driver_id = int(callback.data.split("_")[4])
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        
        if not driver:
            await callback.answer("Driver not found!", show_alert=True)
            return

        # Get unassigned chats
        unassigned_chats = db.query(TelegramChat).filter(
            ~TelegramChat.id.in_(db.query(Driver.chat_id).filter(Driver.chat_id.isnot(None)))
        ).all()

        if not unassigned_chats:
            await callback.message.edit_text(
                "❌ *No Available Chats*\n\n"
                "All chats are already assigned to drivers.\n"
                "Please add new chats first.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Add New Chat", callback_data="add_group")],
                        [InlineKeyboardButton(text="🔙 Back", callback_data="assign_driver_to_chat")],
                    ]
                ),
                parse_mode="Markdown"
            )
            return

        keyboard_buttons = []
        driver_name_escaped = escape_markdown(driver.name)
        company_name = driver.company.name if driver.company else "No Company"
        company_escaped = escape_markdown(company_name)
        
        text = f"🔗 *Assign Chat to {driver_name_escaped}*\n\n"
        text += f"*Driver:* {driver_name_escaped}\n"
        text += f"*Company:* {company_escaped}\n\n"
        text += f"Select a chat to assign:\n\n"

        for chat in unassigned_chats[:10]:  # Limit to 10
            chat_name_escaped = escape_markdown(chat.group_name)
            text += f"• {chat_name_escaped} (`{chat.chat_token}`)\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"💬 {chat.group_name}",
                    callback_data=f"confirm_assign_chat_{driver.id}_{chat.id}"
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back", callback_data="assign_driver_to_chat")
        ])

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_confirm_assign_chat(callback: CallbackQuery, db: Session):
        """Confirm and assign chat to driver"""
        parts = callback.data.split("_")
        driver_id = int(parts[3])
        chat_id = int(parts[4])

        try:
            driver = db.query(Driver).filter(Driver.id == driver_id).first()
            chat = db.query(TelegramChat).filter(TelegramChat.id == chat_id).first()

            if not driver or not chat:
                await callback.answer("Driver or chat not found!", show_alert=True)
                return

            # Check if chat is already assigned
            existing_assignment = db.query(Driver).filter(Driver.chat_id == chat_id).first()
            if existing_assignment:
                await callback.answer("Chat is already assigned to another driver!", show_alert=True)
                return

            # Assign chat to driver
            driver.chat_id = chat_id
            db.commit()

            driver_name_escaped = escape_markdown(driver.name)
            chat_name_escaped = escape_markdown(chat.group_name)
            company_name = driver.company.name if driver.company else "No Company"
            company_escaped = escape_markdown(company_name)

            await callback.message.edit_text(
                f"✅ *Chat Assignment Successful!*\n\n"
                f"*Driver:* {driver_name_escaped}\n"
                f"*Company:* {company_escaped}\n"
                f"*Chat:* {chat_name_escaped}\n"
                f"*Chat ID:* `{chat.chat_token}`\n\n"
                f"🎉 Driver can now receive notifications!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔗 Assign Another", callback_data="assign_driver_to_chat")],
                        [InlineKeyboardButton(text="👤 View All Drivers", callback_data="list_drivers")],
                        [InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")],
                    ]
                ),
                parse_mode="Markdown"
            )

        except SQLAlchemyError as e:
            logger.error(f"Error assigning chat to driver: {e}")
            db.rollback()
            await callback.answer("Error assigning chat!", show_alert=True)

        await callback.answer()

    # ==================== LIST VIEWS ====================
    
    @staticmethod
    @safe_callback_handler
    async def handle_list_drivers(callback: CallbackQuery, db: Session):
        """List all drivers with their chat assignments"""
        drivers = db.query(Driver).join(Company, Driver.company_id == Company.id, isouter=True).all()
        
        if not drivers:
            await callback.message.edit_text(
                "👤 *No Drivers Found*\n\nNo drivers in the system yet.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Add Driver", callback_data="add_driver")],
                        [InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")],
                    ]
                ),
                parse_mode="Markdown"
            )
            return

        text = f"👥 *All Drivers ({len(drivers)})*\n\n"
        
        # Group by company
        current_company = None
        for driver in drivers:
            company_name = driver.company.name if driver.company else "No Company"
            
            if company_name != current_company:
                if current_company is not None:
                    text += "\n"
                company_escaped = escape_markdown(company_name)
                text += f"*🏢 {company_escaped}:*\n"
                current_company = company_name
            
            driver_name_escaped = escape_markdown(driver.name)
            chat_status = "📱" if driver.chat_id else "❌"
            text += f"• {driver_name_escaped} {chat_status}\n"

        text += f"\n*Legend:*\n📱 = Has chat assigned\n❌ = No chat assigned"

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Add Driver", callback_data="add_driver")],
                    [InlineKeyboardButton(text="🔗 Assign Chats", callback_data="assign_driver_to_chat")],
                    [InlineKeyboardButton(text="🔙 Back", callback_data="manage_drivers")],
                ]
            ),
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_list_groups(callback: CallbackQuery, db: Session, user_data: dict):
        """List all chats with their driver assignments"""
        if not user_data or user_data["role"] != "manager":
            await callback.answer("Access denied!", show_alert=True)
            return

        chats = db.query(TelegramChat).all()
        
        if not chats:
            await callback.message.edit_text(
                "📋 *No Chats Found*\n\nNo chats in the system yet.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Add Chat", callback_data="add_group")],
                        [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")],
                    ]
                ),
                parse_mode="Markdown"
            )
            return

        text = f"📋 *All Chats ({len(chats)})*\n\n"

        for i, chat in enumerate(chats, 1):
            # Find driver assigned to this chat
            assigned_driver = db.query(Driver).filter(Driver.chat_id == chat.id).first()
            
            chat_name_escaped = escape_markdown(chat.group_name)
            text += f"{i}. *{chat_name_escaped}*\n"
            text += f"   ID: `{chat.chat_token}`\n"
            
            if assigned_driver:
                driver_name_escaped = escape_markdown(assigned_driver.name)
                text += f"   👤 Driver: {driver_name_escaped}\n"
            else:
                text += f"   ❌ Unassigned\n"
            text += "\n"

        keyboard_buttons = [
            [InlineKeyboardButton(text="➕ Add Chat", callback_data="add_group")],
            [InlineKeyboardButton(text="🔗 Assign to Drivers", callback_data="assign_driver_to_chat")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")],
        ]

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()