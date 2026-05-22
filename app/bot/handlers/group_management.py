# app/bot/handlers/group_management.py - COMPLETE UNIFIED VERSION
import logging

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.services.chat_service import ChatService
from app.bot.utils.error_handling import safe_callback_handler, safe_message_handler
from app.bot.utils.formatters import escape_markdown

logger = logging.getLogger(__name__)


class GroupManagementStates(StatesGroup):
    selecting_chat_method = State()
    waiting_for_username = State()
    waiting_for_chat_id = State()
    confirming_chat_selection = State()
    waiting_for_forward = State()


class GroupManagementHandler:
    """Complete unified handler for group management with all functionality"""

    @staticmethod
    @safe_callback_handler
    async def handle_add_group_menu(
        callback: CallbackQuery, state: FSMContext, user_data: dict
    ):
        """Show different methods to add a group"""
        if not user_data or user_data["role"] != "manager":
            await callback.answer("Access denied!", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔍 Search by Username", callback_data="add_by_username"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🆔 Enter Chat ID", callback_data="add_by_chat_id"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📨 Forward Message", callback_data="add_by_forward"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 My Active Chats", callback_data="show_my_chats"
                    )
                ],
                [InlineKeyboardButton(text="🔙 Back", callback_data="manage_groups")],
            ]
        )

        await callback.message.edit_text(
            "➕ *Add New Group*\n\n"
            "Choose how you want to add a Telegram group:\n\n"
            "🔍 *Search by Username* - Find groups by @username\n"
            "🆔 *Enter Chat ID* - Add by numeric chat ID\n"
            "📨 *Forward Message* - Forward any message from the group\n"
            "📋 *My Active Chats* - Select from your current chats\n\n"
            "💡 *Tip:* The bot must be added to the group first!",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_add_by_username(callback: CallbackQuery, state: FSMContext):
        """Handle adding group by username"""
        await state.set_state(GroupManagementStates.waiting_for_username)

        await callback.message.edit_text(
            "🔍 *Add Group by Username*\n\n"
            "Enter the group username (with or without @):\n\n"
            "*Examples:*\n"
            "• `@mylogisticsgroup`\n"
            "• `mylogisticsgroup`\n"
            "• `MyCompanyDrivers`\n\n"
            "*Cancel:* Send /cancel",
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_add_by_chat_id(callback: CallbackQuery, state: FSMContext):
        """Handle adding group by chat ID"""
        await state.set_state(GroupManagementStates.waiting_for_chat_id)

        await callback.message.edit_text(
            "🆔 *Add Group by Chat ID*\n\n"
            "Enter the numeric chat ID:\n\n"
            "*Examples:*\n"
            "• `-1001234567890` (supergroup)\n"
            "• `-123456789` (regular group)\n\n"
            "*How to find Chat ID:*\n"
            "1. Add `@userinfobot` to your group\n"
            "2. Send `/start` in the group\n"
            "3. Bot will show the chat ID\n\n"
            "*Cancel:* Send /cancel",
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_add_by_forward(callback: CallbackQuery, state: FSMContext):
        """Handle adding group by forwarding message"""
        await state.set_state(GroupManagementStates.waiting_for_forward)

        await callback.message.edit_text(
            "📨 *Add Group by Forward*\n\n"
            "*Instructions:*\n"
            "1. Go to the group you want to add\n"
            "2. Forward ANY message from that group to this chat\n"
            "3. Bot will automatically detect the group info\n\n"
            "*Tips:*\n"
            "• You can forward any message (text, photo, etc.)\n"
            "• The bot must be added to the group first\n"
            "• Works with both public and private groups\n\n"
            "*Alternative if forwarding doesn't work:*\n"
            "• Copy the group's chat ID using @userinfobot\n"
            "• Use the 'Enter Chat ID' method instead\n\n"
            "*Cancel:* Send /cancel",
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_show_my_chats(callback: CallbackQuery, db: AsyncSession):
        """Show user's active chats that can be added"""
        try:
            await callback.message.edit_text(
                "📋 *Your Active Chats*\n\n"
                "🚫 *Telegram API Limitation:*\n"
                "Due to Telegram's privacy policy, bots cannot directly access your chat list.\n\n"
                "*Alternative Methods:*\n\n"
                "*Method 1: Find Chat ID*\n"
                "1. Add `@userinfobot` to your group\n"
                "2. Send `/start` in the group\n"
                "3. Copy the chat ID shown\n"
                "4. Use 'Enter Chat ID' option\n\n"
                "*Method 2: Forward Method*\n"
                "1. Forward any message from your group\n"
                "2. Bot will extract group information\n\n"
                "*Method 3: Username Method*\n"
                "1. Use the group's @username\n"
                "2. Works only for public groups",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Back to Add Group", callback_data="add_group"
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing my chats: {e}")
            await callback.answer("Error accessing chat information", show_alert=True)

        await callback.answer()

    @staticmethod
    @safe_message_handler
    async def handle_username_input(message: types.Message, state: FSMContext, db: AsyncSession):
        """Handle username input for group addition"""
        if message.text.lower() in ["/cancel", "cancel"]:
            await state.clear()
            await message.answer("❌ Operation cancelled. Use /start to return to menu.")
            return

        username = message.text.strip()

        # Add @ if not present
        if not username.startswith("@"):
            username = "@" + username

        try:
            from aiogram import Bot

            from app.config import get_settings

            settings = get_settings()
            bot_instance = Bot(token=settings.telegram_bot_token)

            try:
                # Try to get chat info by username
                chat = await bot_instance.get_chat(username)
                await bot_instance.session.close()

                if chat.type not in ["group", "supergroup"]:
                    await message.answer(
                        f"❌ {username} is not a group or supergroup.\n"
                        f"Found: {chat.type.title()}"
                    )
                    return

                # Store chat info in state for confirmation
                await state.update_data(
                    chat_id=chat.id,
                    chat_title=chat.title,
                    chat_username=username,
                    chat_type=chat.type,
                    member_count=getattr(chat, "member_count", "Unknown"),
                )
                await state.set_state(GroupManagementStates.confirming_chat_selection)

                # Show confirmation
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✅ Add This Group", callback_data="confirm_add_group"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Cancel", callback_data="cancel_add_group"
                            )
                        ],
                    ]
                )

                group_name_escaped = escape_markdown(chat.title)
                username_escaped = escape_markdown(username)

                confirmation_text = (
                    f"🔍 *Found Group:*\n\n"
                    f"*Name:* {group_name_escaped}\n"
                    f"*Username:* {username_escaped}\n"
                    f"*Type:* {chat.type.title()}\n"
                    f"*Chat ID:* `{chat.id}`\n"
                    f"*Members:* {getattr(chat, 'member_count', 'Unknown')}\n\n"
                    f"Add this group to the system?"
                )

                await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="Markdown")

            except Exception as e:
                await bot_instance.session.close()
                error_msg = str(e)

                if "chat not found" in error_msg.lower():
                    reason = "Group doesn't exist or username is incorrect"
                elif "forbidden" in error_msg.lower():
                    reason = "Bot is not added to the group or group is private"
                else:
                    reason = f"Error: {error_msg[:100]}"

                await message.answer(
                    f"❌ Cannot find group: {username}\n\n"
                    f"*Reason:* {reason}\n\n"
                    f"*To fix this:*\n"
                    f"1. Check the username is correct\n"
                    f"2. Make sure it's a public group\n"
                    f"3. Add the bot to the group first\n"
                    f"4. Try using chat ID method instead",
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error in username input: {e}")
            await message.answer("❌ An error occurred while searching. Please try again.")

    @staticmethod
    @safe_message_handler
    async def handle_chat_id_input(message: types.Message, state: FSMContext, db: AsyncSession):
        """Handle chat ID input for group addition"""
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
                # Try to get chat info by ID
                chat = await bot_instance.get_chat(chat_id)
                await bot_instance.session.close()

                if chat.type not in ["group", "supergroup"]:
                    await message.answer(
                        f"❌ Chat ID {chat_id} is not a group.\nFound: {chat.type.title()}"
                    )
                    return

                # Store chat info in state for confirmation
                await state.update_data(
                    chat_id=chat.id,
                    chat_title=chat.title,
                    chat_username=getattr(chat, "username", None),
                    chat_type=chat.type,
                    member_count=getattr(chat, "member_count", "Unknown"),
                )
                await state.set_state(GroupManagementStates.confirming_chat_selection)

                # Show confirmation
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✅ Add This Group", callback_data="confirm_add_group"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Cancel", callback_data="cancel_add_group"
                            )
                        ],
                    ]
                )

                group_name_escaped = escape_markdown(chat.title)
                username_text = f"@{chat.username}" if chat.username else "No username"

                confirmation_text = (
                    f"🆔 *Found Group:*\n\n"
                    f"*Name:* {group_name_escaped}\n"
                    f"*Username:* {username_text}\n"
                    f"*Type:* {chat.type.title()}\n"
                    f"*Chat ID:* `{chat.id}`\n"
                    f"*Members:* {getattr(chat, 'member_count', 'Unknown')}\n\n"
                    f"Add this group to the system?"
                )

                await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="Markdown")

            except Exception as e:
                await bot_instance.session.close()
                error_msg = str(e)

                if "chat not found" in error_msg.lower():
                    error_reason = "Chat ID doesn't exist or is invalid"
                elif (
                    "bot is not a member" in error_msg.lower()
                    or "forbidden" in error_msg.lower()
                ):
                    error_reason = "Bot is not added to the group or lacks permissions"
                elif "bad request" in error_msg.lower():
                    error_reason = "Invalid chat ID format or access denied"
                else:
                    error_reason = f"{error_msg[:100]}"

                await message.answer(
                    f"❌ Cannot access chat ID: {chat_id}\n\n"
                    f"*Reason:* {error_reason}\n\n"
                    f"*To fix this:*\n"
                    f"1. Make sure the bot is added to the group\n"
                    f"2. Give the bot admin permissions (or at least 'Read Messages')\n"
                    f"3. Try forwarding a message instead\n"
                    f"4. Double-check the chat ID is correct",
                    parse_mode="Markdown"
                )

        except ValueError:
            await message.answer(
                "❌ *Invalid chat ID format*\n\n"
                "Chat ID must be a number (usually negative for groups).\n\n"
                "*Examples:*\n"
                "• `-1001234567890`\n"
                "• `-123456789`",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error in chat ID input: {e}")
            await message.answer(
                "❌ An error occurred while checking chat ID. Please try again."
            )

    @staticmethod
    @safe_message_handler
    async def handle_forward_message(message: types.Message, state: FSMContext, db: AsyncSession):
        """Handle forwarded message for group addition"""
        if message.text and message.text.lower() in ["/cancel", "cancel"]:
            await state.clear()
            await message.answer("❌ Operation cancelled. Use /start to return to menu.")
            return

        # Check multiple ways a message might indicate it's from a group
        chat_info = None

        # Method 1: Standard forward_from_chat (works most of the time)
        if message.forward_from_chat:
            chat_info = message.forward_from_chat
            logger.info(
                f"Detected forwarded message via forward_from_chat: {chat_info.title}"
            )

        # Method 2: Check if message has forward_date but no forward_from_chat (privacy protected)
        elif message.forward_date:
            await message.answer(
                "🔍 *Message Detected as Forwarded*\n\n"
                "The message appears to be forwarded, but Telegram privacy settings "
                "prevent me from seeing the original chat information.\n\n"
                "*Please use one of these methods instead:*\n\n"
                "*Option 1: Get Chat ID*\n"
                "1. Add @userinfobot to your group\n"
                "2. Send /start in the group\n"
                "3. Copy the chat ID\n"
                "4. Use 'Enter Chat ID' method\n\n"
                "*Option 2: Use Group Username*\n"
                "1. If your group has a username (@groupname)\n"
                "2. Use 'Search by Username' method\n\n"
                "*Option 3: Manual Input*\n"
                "• Send me the chat ID directly as a number\n"
                "• Example: `-1001234567890`",
                parse_mode="Markdown"
            )
            return

        # Method 3: Check message sender_chat (for messages sent by group admins)
        elif message.sender_chat and message.sender_chat.type in ["group", "supergroup"]:
            chat_info = message.sender_chat
            logger.info(f"Detected group message via sender_chat: {chat_info.title}")

        # Method 4: If user sends a chat ID directly as text
        elif message.text and message.text.strip().lstrip("-").isdigit():
            try:
                chat_id = int(message.text.strip())
                if chat_id < 0:  # Group chat IDs are negative
                    await GroupManagementHandler.handle_chat_id_input(message, state, db)
                    return
            except ValueError:
                pass

        if not chat_info:
            await message.answer(
                "❌ *Cannot detect group information*\n\n"
                "*What I received:* Regular message (not forwarded from a group)\n\n"
                "*Please try one of these:*\n\n"
                "*Method 1: Forward Properly*\n"
                "1. Go to your group\n"
                "2. Find ANY message in the group\n"
                "3. Tap and hold the message\n"
                "4. Select 'Forward'\n"
                "5. Choose this bot chat\n"
                "6. Send the forwarded message\n\n"
                "*Method 2: Use Chat ID*\n"
                "1. Add @userinfobot to your group\n"
                "2. Send /start in your group\n"
                "3. Copy the chat ID (like -1001234567890)\n"
                "4. Send that number to me here\n\n"
                "*Method 3: Cancel and try different method*\n"
                "Send /cancel and use 'Enter Chat ID' option",
                parse_mode="Markdown"
            )
            return

        # Validate it's actually a group
        if chat_info.type not in ["group", "supergroup"]:
            await message.answer(
                f"❌ *Not a group message*\n\n"
                f"*Detected chat type:* {chat_info.type.title()}\n"
                f"Please forward a message from a GROUP or SUPERGROUP.",
                parse_mode="Markdown"
            )
            return

        # Store chat info in state for confirmation
        await state.update_data(
            chat_id=chat_info.id,
            chat_title=chat_info.title,
            chat_username=getattr(chat_info, "username", None),
            chat_type=chat_info.type,
        )
        await state.set_state(GroupManagementStates.confirming_chat_selection)

        # Show confirmation
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Add This Group", callback_data="confirm_add_group"
                    )
                ],
                [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_add_group")],
            ]
        )

        group_name_escaped = escape_markdown(chat_info.title)
        username_text = (
            f"@{chat_info.username}"
            if getattr(chat_info, "username", None)
            else "No public username"
        )

        confirmation_text = (
            f"📨 *Group Detected:*\n\n"
            f"*Name:* {group_name_escaped}\n"
            f"*Username:* {username_text}\n"
            f"*Type:* {chat_info.type.title()}\n"
            f"*Chat ID:* `{chat_info.id}`\n\n"
            f"Add this group to the system?"
        )

        await message.answer(confirmation_text, reply_markup=keyboard, parse_mode="Markdown")

    @staticmethod
    @safe_callback_handler
    async def handle_confirm_add_group(callback: CallbackQuery, state: FSMContext, db: AsyncSession):
        """Confirm and add the selected group"""
        try:
            state_data = await state.get_data()
            chat_service = ChatService(db)

            success = await chat_service.add_telegram_chat(
                chat_id=state_data["chat_id"],
                chat_title=state_data["chat_title"],
                chat_type=state_data["chat_type"],
            )

            if success:
                group_name_escaped = escape_markdown(state_data['chat_title'])
                username_text = ""
                if state_data.get("chat_username"):
                    username_escaped = escape_markdown(state_data['chat_username'])
                    username_text = f"\n*Username:* {username_escaped}"

                await callback.message.edit_text(
                    f"✅ *Group Added Successfully!*\n\n"
                    f"*Name:* {group_name_escaped}\n"
                    f"*Chat ID:* `{state_data['chat_id']}`{username_text}\n"
                    f"*Type:* {state_data['chat_type'].title()}\n\n"
                    f"🎉 The group is now registered in the system!\n"
                    f"You can now link drivers to this group.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="📋 View All Groups",
                                    callback_data="list_groups",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="➕ Add Another", callback_data="add_group"
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="🔙 Back to Menu",
                                    callback_data="manage_groups",
                                )
                            ],
                        ]
                    ),
                    parse_mode="Markdown",
                )
            else:
                group_name_escaped = escape_markdown(state_data['chat_title'])
                await callback.message.edit_text(
                    f"❌ *Failed to Add Group*\n\n"
                    f"*Reason:* Group may already exist in the system.\n\n"
                    f"*Group:* {group_name_escaped}\n"
                    f"*Chat ID:* `{state_data['chat_id']}`",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="📋 View All Groups",
                                    callback_data="list_groups",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="🔙 Back", callback_data="manage_groups"
                                )
                            ],
                        ]
                    ),
                    parse_mode="Markdown",
                )

        except Exception as e:
            logger.error(f"Error confirming group addition: {e}")
            await callback.message.edit_text(
                "❌ *Error Adding Group*\n\n"
                "An unexpected error occurred. Please try again.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Back", callback_data="manage_groups"
                            )
                        ]
                    ]
                ),
                parse_mode="Markdown"
            )

        await state.clear()
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_cancel_add_group(callback: CallbackQuery, state: FSMContext):
        """Cancel group addition"""
        await state.clear()

        await callback.message.edit_text(
            "❌ *Group Addition Cancelled*\n\nNo changes were made to the system.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ Try Again", callback_data="add_group"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Back", callback_data="manage_groups"
                        )
                    ],
                ]
            ),
            parse_mode="Markdown"
        )
        await callback.answer()
