# app/bot/handlers/dispatcher.py - Updated for cross-company access
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session
from app.bot.services.load_service import LoadBotService
from app.services.notification_service import NotificationService
from app.bot.utils.formatters import escape_markdown
from app.bot.utils.error_handling import (
    safe_callback_handler,
    CallbackDataValidator,
    UserPermissionChecker,
    truncate_text
)
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class NotificationStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_driver_selection = State()
    waiting_for_company_selection = State()
    waiting_for_broadcast_type = State()


class DispatcherHandler:
    """Handler for dispatcher functions with cross-company access"""

    @staticmethod
    @safe_callback_handler
    async def handle_all_loads(callback: types.CallbackQuery, db: Session, user_data: dict):
        """Handle all loads view for dispatchers"""
        if not user_data or user_data["role"] != "dispatcher":
            await callback.answer("Access denied!", show_alert=True)
            return

        load_service = LoadBotService(db)
        loads = await load_service.get_all_loads(limit=20)

        if not loads:
            await callback.message.edit_text(
                "📋 No loads found in the system.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ]
                ),
            )
        else:
            text = f"📋 All Loads ({len(loads)}):\n\n"
            keyboard_buttons = []
            
            for load in loads[:10]:  # Show first 10
                company_name = load.company.name if load.company else "No Company"
                status = "✅ Assigned" if load.assigned_driver else "⏳ Unassigned"
                
                # Escape special characters to prevent markdown issues
                trip_id = escape_markdown(str(load.trip_id))
                company_escaped = escape_markdown(company_name)
                pickup_escaped = escape_markdown(str(load.pickup_address))
                dropoff_escaped = escape_markdown(str(load.dropoff_address))
                
                text += f"🚛 *{trip_id}* ({company_escaped})\n"
                text += f"📍 {pickup_escaped} → {dropoff_escaped}\n"
                text += f"💰 ${float(load.rate):,.2f} | {status}\n"
                if load.assigned_driver:
                    driver_escaped = escape_markdown(str(load.assigned_driver))
                    text += f"👤 {driver_escaped}\n"
                text += "\n"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"📋 {load.trip_id}",
                        callback_data=f"view_load_{load.id}",
                    )
                ])

            if len(loads) > 10:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"➡️ Show More ({len(loads) - 10} remaining)",
                        callback_data="more_loads"
                    )
                ])

            keyboard_buttons.append([
                InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")
            ])

            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                parse_mode="Markdown",
            )

        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_assign_driver(callback: types.CallbackQuery, db: Session):
        """Handle driver assignment to load - UPDATED FOR ALL DRIVERS"""
        # Validate callback data
        is_valid, parts = CallbackDataValidator.validate_callback_data(callback.data, 3, "assign_driver")
        if not is_valid:
            await callback.answer("Invalid request data!", show_alert=True)
            return
            
        load_id = CallbackDataValidator.safe_int_conversion(parts[2])
        if load_id <= 0:
            await callback.answer("Invalid load ID!", show_alert=True)
            return

        load_service = LoadBotService(db)

        # Get ALL drivers across ALL companies
        drivers = await load_service.get_available_drivers()

        if not drivers:
            await callback.answer("No drivers available!", show_alert=True)
            return

        # Group drivers by company for better organization
        drivers_by_company = defaultdict(list)

        for driver in drivers:
            company_name = driver.company.name if driver.company else "No Company"
            drivers_by_company[company_name].append(driver)

        keyboard_buttons = []

        # Add company selection buttons first for better UX
        if len(drivers_by_company) > 3:  # If many companies, show company filter
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="🏢 Filter by Company",
                    callback_data=f"filter_company_{load_id}"
                )
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="👥 Show All Drivers",
                    callback_data=f"show_all_drivers_{load_id}"
                )
            ])

        # Add drivers organized by company (limit display to prevent overflow)
        total_shown = 0
        for company_name, company_drivers in drivers_by_company.items():
            # Add company header for organization
            if len(drivers_by_company) > 1:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🏢 {company_name} ({len(company_drivers)} drivers)",
                        callback_data="company_header"  # Non-functional, just for display
                    )
                ])

            # Add drivers from this company
            for driver in company_drivers[:5]:  # Limit per company to prevent overflow
                if total_shown >= 15:  # Total limit
                    break
                    
                driver_text = f"👤 {driver.name}"
                if driver.chat_id:
                    driver_text += " 📱"  # Telegram available
                
                # Show company if multiple companies
                if len(drivers_by_company) > 1:
                    driver_text += f" ({company_name})"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=driver_text,
                        callback_data=f"select_driver_{load_id}_{driver.id}",
                    )
                ])
                total_shown += 1

            if total_shown >= 15:
                break

        # Add pagination or "show more" if there are many drivers
        if total_shown < len(drivers):
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"➡️ Show More ({len(drivers) - total_shown} remaining)",
                    callback_data=f"show_more_drivers_{load_id}_{total_shown}"
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")
        ])

        message_text = (
            f"🚛 *Select driver for load:*\n\n"
            f"Available drivers from *all companies*:\n"
            f"📱 = Telegram notifications available\n\n"
            f"*Total:* {len(drivers)} drivers from {len(drivers_by_company)} companies"
        )

        await callback.message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    async def handle_filter_by_company(callback: types.CallbackQuery, db: Session):
        """Handle filtering drivers by company"""
        load_id = int(callback.data.split("_")[2])
        
        load_service = LoadBotService(db)
        companies = await load_service.get_all_companies()

        if not companies:
            await callback.answer("No companies found!", show_alert=True)
            return

        keyboard_buttons = []
        for company in companies:
            # Get driver count for this company
            company_drivers = await load_service.get_drivers_by_company(company.id)
            driver_count = len(company_drivers)
            telegram_count = sum(1 for d in company_drivers if d.chat_id)
            
            button_text = f"🏢 {company.name} ({driver_count} drivers"
            if telegram_count > 0:
                button_text += f", {telegram_count} 📱"
            button_text += ")"

            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"company_drivers_{load_id}_{company.id}"
                )
            ])

        keyboard_buttons.extend([
            [InlineKeyboardButton(
                text="👥 Show All Drivers",
                callback_data=f"assign_driver_{load_id}"
            )],
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")]
        ])

        await callback.message.edit_text(
            f"🏢 *Select Company:*\n\nChoose a company to view its drivers:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    async def handle_company_drivers(callback: types.CallbackQuery, db: Session):
        """Handle showing drivers from specific company"""
        parts = callback.data.split("_")
        load_id = int(parts[2])
        company_id = int(parts[3])

        load_service = LoadBotService(db)
        company_drivers = await load_service.get_drivers_by_company(company_id)

        if not company_drivers:
            await callback.answer("No drivers found in this company!", show_alert=True)
            return

        # Get company name
        companies = await load_service.get_all_companies()
        company = next((c for c in companies if c.id == company_id), None)
        company_name = company.name if company else "Unknown Company"

        keyboard_buttons = []
        for driver in company_drivers:
            driver_text = f"👤 {driver.name}"
            if driver.chat_id:
                driver_text += " 📱"

            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=driver_text,
                    callback_data=f"select_driver_{load_id}_{driver.id}",
                )
            ])

        keyboard_buttons.extend([
            [InlineKeyboardButton(
                text="🏢 Other Companies",
                callback_data=f"filter_company_{load_id}"
            )],
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")]
        ])

        company_escaped = escape_markdown(company_name)
        await callback.message.edit_text(
            f"🏢 *{company_escaped} Drivers:*\n\n"
            f"Select a driver from {company_escaped}:\n"
            f"📱 = Telegram notifications available",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    async def handle_load_details(callback: types.CallbackQuery, db: Session):
        """Show detailed load information"""
        load_id = int(callback.data.split("_")[2])

        load_service = LoadBotService(db)
        load_details = await load_service.get_load_details(load_id)

        if not load_details:
            await callback.answer("Load not found!", show_alert=True)
            return

        load = load_details["load"]
        legs = load_details["legs"]

        # Escape markdown characters
        trip_id = escape_markdown(str(load.trip_id))
        pickup_address = escape_markdown(str(load.pickup_address))
        dropoff_address = escape_markdown(str(load.dropoff_address))

        text = f"🚛 *Load Details: {trip_id}*\n\n"
        text += f"*📍 Route:* {pickup_address} → {dropoff_address}\n"
        text += f"*🕐 Start:* {load.start_time_str}\n"
        text += f"*🕐 End:* {load.end_time_str}\n"
        text += f"*💰 Rate:* ${float(load.rate):,.2f}\n"
        text += f"*📏 Distance:* {float(load.distance):,.1f} mi\n"

        # Show company information
        if load.company:
            company_escaped = escape_markdown(load.company.name)
            text += f"*🏢 Company:* {company_escaped}\n"

        if load.assigned_driver:
            # Get driver details to show company
            from app.db.models import Driver
            driver = db.query(Driver).filter(Driver.id == load.driver_id).first()
            driver_company = driver.company.name if driver and driver.company else "Unknown"
            driver_escaped = escape_markdown(str(load.assigned_driver))
            company_escaped = escape_markdown(driver_company)
            text += f"*👤 Driver:* {driver_escaped} ({company_escaped})\n"
        else:
            text += "*👤 Driver:* Not assigned\n"

        if legs:
            text += f"\n*📋 Legs ({len(legs)}):*\n"
            for i, leg in enumerate(legs, 1):
                pickup_facility = escape_markdown(str(leg.pickup_facility_name))
                dropoff_facility = escape_markdown(str(leg.dropoff_facility_name))
                text += f"{i}. {pickup_facility} → {dropoff_facility}\n"
                text += f"   {leg.pickup_time_str} - {leg.dropoff_time_str}\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚛 Assign Driver (All Companies)",
                        callback_data=f"assign_driver_{load.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📢 Notify Driver",
                        callback_data=f"notify_driver_{load.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Load Statistics",
                        callback_data=f"load_stats_{load.id}",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Back", callback_data="all_loads")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_driver_selection(callback: types.CallbackQuery, db: Session):
        """Handle driver selection for load assignment - UPDATED FOR CROSS-COMPANY"""
        # Validate callback data
        is_valid, parts = CallbackDataValidator.validate_callback_data(callback.data, 4, "select_driver")
        if not is_valid:
            await callback.answer("Invalid request data!", show_alert=True)
            return
            
        load_id = CallbackDataValidator.safe_int_conversion(parts[2])
        driver_id = CallbackDataValidator.safe_int_conversion(parts[3])
        
        if load_id <= 0 or driver_id <= 0:
            await callback.answer("Invalid load or driver ID!", show_alert=True)
            return

        try:
            load_service = LoadBotService(db)
            
            # Get driver and load info
            from app.db.repositories.driver_repository import DriverRepository
            driver_repo = DriverRepository(db)
            driver = driver_repo.get_driver_by_id(driver_id)
            load_data = await load_service.get_load_details(load_id)

            if not driver or not load_data:
                await callback.answer("Driver or load not found!", show_alert=True)
                return

            load = load_data["load"]
            
            # Check if this is a cross-company assignment
            is_cross_company = driver.company_id != load.company_id if load.company_id else False
            
            # Update load with driver assignment using the load service
            success = await load_service.assign_driver_to_load(load_id, driver_id)
            
            if success:
                assignment_type = "Cross-company" if is_cross_company else "Same company"
                driver_company = driver.company.name if driver.company else "No Company"
                load_company = load.company.name if load.company else "No Company"
                
                driver_escaped = escape_markdown(driver.name)
                driver_company_escaped = escape_markdown(driver_company)
                load_company_escaped = escape_markdown(load_company)
                trip_id_escaped = escape_markdown(str(load.trip_id))
                
                success_message = f"✅ *Driver Assigned Successfully!*\n\n"
                success_message += f"*Driver:* {driver_escaped}\n"
                success_message += f"*Driver Company:* {driver_company_escaped}\n"
                success_message += f"*Load:* {trip_id_escaped}\n"
                success_message += f"*Load Company:* {load_company_escaped}\n"
                success_message += f"*Assignment Type:* {assignment_type}\n"
                
                if is_cross_company:
                    success_message += f"\n🔄 This is a cross-company assignment!"

                keyboard_buttons = []
                
                # Add notification button if driver has Telegram
                if driver.chat_id:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text="📢 Notify Driver",
                            callback_data=f"notify_driver_{load_id}",
                        )
                    ])
                else:
                    success_message += f"\n⚠️ Driver doesn't have Telegram notifications set up"

                keyboard_buttons.extend([
                    [
                        InlineKeyboardButton(
                            text="📋 View Load Details",
                            callback_data=f"view_load_{load_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Back to Loads", callback_data="all_loads"
                        )
                    ],
                ])

                await callback.message.edit_text(
                    success_message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                    parse_mode="Markdown",
                )
            else:
                await callback.answer("Failed to assign driver!", show_alert=True)

        except Exception as e:
            logger.error(f"Error assigning driver: {e}")
            await callback.answer("Error assigning driver!", show_alert=True)

        await callback.answer()

    @staticmethod
    async def handle_notify_driver(callback: types.CallbackQuery, db: Session):
        """Handle sending notification to driver"""
        load_id = int(callback.data.split("_")[2])

        try:
            notification_service = NotificationService(db)
            success = await notification_service.notify_driver_about_load(load_id)

            if success:
                await callback.answer(
                    "✅ Notification sent successfully!", show_alert=True
                )
            else:
                await callback.answer(
                    "❌ Failed to send notification! Driver may not have Telegram set up.", show_alert=True
                )

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            await callback.answer("❌ Error sending notification!", show_alert=True)

    @staticmethod
    async def handle_broadcast_message(callback: types.CallbackQuery, state: FSMContext):
        """Handle broadcast message setup - UPDATED FOR CROSS-COMPANY"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 All Drivers (All Companies)",
                        callback_data="broadcast_all_drivers"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏢 Drivers by Company",
                        callback_data="broadcast_by_company"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📱 Only Telegram-Enabled Drivers",
                        callback_data="broadcast_telegram_only"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Cancel",
                        callback_data="send_notifications"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "*Broadcast Message*\n\n"
            "Choose the scope of your broadcast:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_all_drivers(callback: types.CallbackQuery, state: FSMContext):
        """Handle broadcast to all drivers across all companies"""
        await state.update_data(broadcast_type="all_drivers")
        await state.set_state(NotificationStates.waiting_for_message)
        
        await callback.message.edit_text(
            "*Broadcast to All Drivers*\n\n"
            "Enter the message you want to send to *all drivers across all companies*:\n\n"
            "⚠️ This will send to ALL drivers with Telegram notifications enabled.",
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_by_company(callback: types.CallbackQuery, state: FSMContext, db: Session):
        """Handle broadcast by company selection"""
        load_service = LoadBotService(db)
        companies = await load_service.get_all_companies()

        if not companies:
            await callback.answer("No companies found!", show_alert=True)
            return

        keyboard_buttons = []
        for company in companies:
            company_drivers = await load_service.get_drivers_by_company(company.id)
            telegram_drivers = sum(1 for d in company_drivers if d.chat_id)
            
            button_text = f"🏢 {company.name} ({telegram_drivers} drivers)"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"broadcast_company_{company.id}"
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back", callback_data="broadcast_message")
        ])

        await state.set_state(NotificationStates.waiting_for_company_selection)
        await callback.message.edit_text(
            "*Select Company for Broadcast:*\n\n"
            "Choose which company's drivers to notify:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_telegram_only(callback: types.CallbackQuery, state: FSMContext):
        """Handle broadcast to only Telegram-enabled drivers"""
        await state.update_data(broadcast_type="telegram_only")
        await state.set_state(NotificationStates.waiting_for_message)
        
        await callback.message.edit_text(
            "*Broadcast to Telegram-Enabled Drivers*\n\n"
            "Enter the message you want to send to *all drivers with Telegram notifications* (across all companies):",
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    async def handle_company_broadcast_selection(callback: types.CallbackQuery, state: FSMContext):
        """Handle company selection for broadcast"""
        company_id = int(callback.data.split("_")[2])
        
        await state.update_data(broadcast_type="company", company_id=company_id)
        await state.set_state(NotificationStates.waiting_for_message)
        
        # Get company name for confirmation
        from app.db.models import Company
        from app.db.database import SessionLocal
        
        db = SessionLocal()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            company_name = company.name if company else "Unknown Company"
        finally:
            db.close()
        
        company_escaped = escape_markdown(company_name)
        await callback.message.edit_text(
            f"*Broadcast to {company_escaped}*\n\n"
            f"Enter the message you want to send to all drivers in *{company_escaped}*:",
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_message_input(
        message: types.Message, state: FSMContext, db: Session, user_data: dict
    ):
        """Handle broadcast message input - UPDATED FOR CROSS-COMPANY"""
        if user_data["role"] != "dispatcher":
            await message.answer("Access denied!")
            return

        state_data = await state.get_data()
        broadcast_text = message.text.strip()
        broadcast_type = state_data.get("broadcast_type", "all_drivers")
        company_id = state_data.get("company_id")

        try:
            from app.db.models import Driver, TelegramChat
            from aiogram import Bot
            from app.config import get_settings

            settings = get_settings()
            bot = Bot(token=settings.telegram_bot_token)

            # Get drivers based on broadcast type
            if broadcast_type == "company" and company_id:
                drivers_query = db.query(Driver).filter(
                    Driver.company_id == company_id,
                    Driver.chat_id.isnot(None)
                )
                scope_text = f"company drivers"
            elif broadcast_type == "telegram_only":
                drivers_query = db.query(Driver).filter(Driver.chat_id.isnot(None))
                scope_text = "Telegram-enabled drivers (all companies)"
            else:  # all_drivers
                drivers_query = db.query(Driver).filter(Driver.chat_id.isnot(None))
                scope_text = "all drivers (all companies)"

            drivers_with_chats = drivers_query.all()

            sent_count = 0
            failed_count = 0
            company_breakdown = defaultdict(int)

            for driver in drivers_with_chats:
                try:
                    chat = (
                        db.query(TelegramChat)
                        .filter(TelegramChat.id == driver.chat_id)
                        .first()
                    )
                    if chat and chat.chat_token:
                        # Include company info in message for cross-company context
                        company_name = driver.company.name if driver.company else "No Company"
                        formatted_message = (
                            f"📢 *Message from {user_data['name']} (Dispatcher)*\n\n"
                            f"{broadcast_text}\n\n"
                            f"---\n"
                            f"Driver: {driver.name} ({company_name})"
                        )
                        await bot.send_message(
                            chat_id=chat.chat_token,
                            text=formatted_message,
                            parse_mode="Markdown"
                        )
                        sent_count += 1
                        company_breakdown[company_name] += 1
                except Exception as e:
                    logger.error(f"Failed to send message to driver {driver.name}: {e}")
                    failed_count += 1

            # Create detailed results message
            result_message = f"*Broadcast Completed!*\n\n"
            result_message += f"*Scope:* {scope_text}\n"
            result_message += f"*✅ Sent:* {sent_count}\n"
            result_message += f"*❌ Failed:* {failed_count}\n\n"
            
            if company_breakdown:
                result_message += "*📊 Company Breakdown:*\n"
                for company, count in sorted(company_breakdown.items()):
                    company_escaped = escape_markdown(company)
                    result_message += f"• {company_escaped}: {count} drivers\n"

            await message.answer(result_message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            await message.answer("❌ Error sending broadcast message!")

        await state.clear()

    @staticmethod
    async def handle_show_more_drivers(callback: types.CallbackQuery, db: Session):
        """Handle showing more drivers with pagination"""
        parts = callback.data.split("_")
        load_id = int(parts[3])
        offset = int(parts[4])

        load_service = LoadBotService(db)
        all_drivers = await load_service.get_available_drivers()

        # Show next batch of drivers
        drivers_to_show = all_drivers[offset:offset + 15]
        
        if not drivers_to_show:
            await callback.answer("No more drivers to show!", show_alert=True)
            return

        keyboard_buttons = []
        
        # Group by company for this batch
        drivers_by_company = defaultdict(list)
        for driver in drivers_to_show:
            company_name = driver.company.name if driver.company else "No Company"
            drivers_by_company[company_name].append(driver)

        for company_name, company_drivers in drivers_by_company.items():
            if len(drivers_by_company) > 1:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🏢 {company_name}",
                        callback_data="company_header"
                    )
                ])

            for driver in company_drivers:
                driver_text = f"👤 {driver.name}"
                if driver.chat_id:
                    driver_text += " 📱"
                if len(drivers_by_company) > 1:
                    driver_text += f" ({company_name})"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=driver_text,
                        callback_data=f"select_driver_{load_id}_{driver.id}",
                    )
                ])

        # Add navigation buttons
        nav_buttons = []
        if offset > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Previous",
                    callback_data=f"show_more_drivers_{load_id}_{max(0, offset - 15)}"
                )
            )

        if offset + 15 < len(all_drivers):
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=f"show_more_drivers_{load_id}_{offset + 15}"
                )
            )

        if nav_buttons:
            keyboard_buttons.append(nav_buttons)

        keyboard_buttons.extend([
            [InlineKeyboardButton(
                text="🏢 Filter by Company",
                callback_data=f"filter_company_{load_id}"
            )],
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")]
        ])

        current_range = f"{offset + 1}-{min(offset + 15, len(all_drivers))}"
        message_text = (
            f"🚛 *Select driver for load:*\n\n"
            f"Showing drivers {current_range} of {len(all_drivers)}\n"
            f"📱 = Telegram notifications available\n\n"
            f"From *all companies*"
        )

        await callback.message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    async def handle_unassigned_loads(callback: types.CallbackQuery, db: Session, user_data: dict):
        """Handle unassigned loads view"""
        if not user_data or user_data["role"] != "dispatcher":
            await callback.answer("Access denied!", show_alert=True)
            return

        load_service = LoadBotService(db)
        unassigned_loads = await load_service.get_unassigned_loads(limit=15)

        if not unassigned_loads:
            await callback.message.edit_text(
                "✅ No unassigned loads!\n\nAll loads have been assigned to drivers.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="📋 View All Loads", callback_data="all_loads")],
                        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ]
                )
            )
        else:
            text = f"⏳ Unassigned Loads ({len(unassigned_loads)}):\n\n"
            keyboard_buttons = []
            
            for load in unassigned_loads:
                company_name = load.company.name if load.company else "No Company"
                
                # Escape special characters
                trip_id = escape_markdown(str(load.trip_id))
                company_escaped = escape_markdown(company_name)
                pickup_escaped = escape_markdown(str(load.pickup_address))
                dropoff_escaped = escape_markdown(str(load.dropoff_address))
                
                text += f"🚛 *{trip_id}* ({company_escaped})\n"
                text += f"📍 {pickup_escaped} → {dropoff_escaped}\n"
                text += f"💰 ${float(load.rate):,.2f}\n"
                text += f"📅 {load.start_time_str}\n\n"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🚛 Assign {load.trip_id}",
                        callback_data=f"assign_driver_{load.id}",
                    )
                ])

            keyboard_buttons.append([
                InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")
            ])

            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                parse_mode="Markdown",
            )

        await callback.answer()

    @staticmethod
    async def handle_all_drivers(callback: types.CallbackQuery, db: Session, user_data: dict):
        """Handle all drivers view across companies"""
        if not user_data or user_data["role"] != "dispatcher":
            await callback.answer("Access denied!", show_alert=True)
            return

        load_service = LoadBotService(db)
        drivers_info = await load_service.get_drivers_with_company_info()

        if not drivers_info:
            await callback.message.edit_text(
                "👤 No drivers found in the system.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ]
                ),
            )
        else:
            text = f"👥 All Drivers ({len(drivers_info)}):\n\n"
            
            # Group by company for display
            current_company = None
            telegram_count = 0
            
            for driver_info in drivers_info[:20]:  # Show first 20
                driver = driver_info["driver"]
                company_name = driver_info["company_name"]
                
                if company_name != current_company:
                    if current_company is not None:
                        text += "\n"
                    company_escaped = escape_markdown(company_name)
                    text += f"*🏢 {company_escaped}:*\n"
                    current_company = company_name
                
                telegram_indicator = " 📱" if driver_info["has_telegram"] else ""
                driver_escaped = escape_markdown(driver.name)
                text += f"• {driver_escaped}{telegram_indicator}\n"
                
                if driver_info["has_telegram"]:
                    telegram_count += 1

            text += f"\n*📊 Summary:*\n"
            text += f"• Total Drivers: {len(drivers_info)}\n"
            text += f"• With Telegram: {telegram_count}\n"
            text += f"• Companies: {len(set(d['company_name'] for d in drivers_info))}\n"

            keyboard_buttons = [
                [
                    InlineKeyboardButton(text="📢 Broadcast Message", callback_data="broadcast_message"),
                    InlineKeyboardButton(text="🏢 By Company", callback_data="drivers_by_company")
                ],
                [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
            ]

            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                parse_mode="Markdown",
            )

        await callback.answer()

    @staticmethod
    async def handle_all_companies(callback: types.CallbackQuery, db: Session, user_data: dict):
        """Handle all companies view"""
        if not user_data or user_data["role"] != "dispatcher":
            await callback.answer("Access denied!", show_alert=True)
            return

        load_service = LoadBotService(db)
        company_stats = await load_service.get_company_statistics()

        if not company_stats:
            await callback.message.edit_text(
                "🏢 No companies found in the system.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ]
                ),
            )
        else:
            text = f"🏢 All Companies ({len(company_stats)}):\n\n"
            keyboard_buttons = []
            
            for stat in company_stats:
                company = stat["company"]
                company_escaped = escape_markdown(company.name)
                
                text += f"*{company_escaped}*\n"
                text += f"• Drivers: {stat['total_drivers']} ({stat['drivers_with_telegram']} 📱)\n"
                text += f"• Loads: {stat['total_loads']} ({stat['unassigned_loads']} unassigned)\n"
                text += f"• DOT: {company.usdot} | MC: {company.mc}\n\n"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🏢 {company.name}",
                        callback_data=f"company_details_{company.id}"
                    )
                ])

            keyboard_buttons.append([
                InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")
            ])

            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                parse_mode="Markdown",
            )

        await callback.answer()

    @staticmethod
    @safe_callback_handler
    async def handle_company_details(callback: types.CallbackQuery, db: Session):
        """Handle company details view"""
        # Validate callback data
        is_valid, parts = CallbackDataValidator.validate_callback_data(callback.data, 3, "company_details")
        if not is_valid:
            await callback.answer("Invalid request data!", show_alert=True)
            return
            
        company_id = CallbackDataValidator.safe_int_conversion(parts[2])
        if company_id <= 0:
            await callback.answer("Invalid company ID!", show_alert=True)
            return
        
        load_service = LoadBotService(db)
        
        # Get company details
        companies = await load_service.get_all_companies()
        company = next((c for c in companies if c.id == company_id), None)
        
        if not company:
            await callback.answer("Company not found!", show_alert=True)
            return

        # Get company drivers and loads
        drivers = await load_service.get_drivers_by_company(company_id)
        loads = await load_service.get_loads_by_company(company_id)
        
        drivers_with_telegram = sum(1 for d in drivers if d.chat_id)
        unassigned_loads = sum(1 for l in loads if not l.driver_id)

        company_escaped = escape_markdown(company.name)
        
        text = f"🏢 *{company_escaped} Details*\n\n"
        text += f"*Company Info:*\n"
        text += f"• DOT Number: {company.usdot}\n"
        text += f"• MC Number: {company.mc}\n"
        text += f"• Carrier ID: {escape_markdown(company.carrier_identifier)}\n\n"
        
        text += f"*Statistics:*\n"
        text += f"• Total Drivers: {len(drivers)}\n"
        text += f"• Telegram-Enabled: {drivers_with_telegram}\n"
        text += f"• Total Loads: {len(loads)}\n"
        text += f"• Unassigned Loads: {unassigned_loads}\n\n"
        
        if drivers:
            text += f"*Recent Drivers:*\n"
            for driver in drivers[:5]:
                telegram_indicator = " 📱" if driver.chat_id else ""
                driver_escaped = escape_markdown(driver.name)
                text += f"• {driver_escaped}{telegram_indicator}\n"
            
            if len(drivers) > 5:
                text += f"... and {len(drivers) - 5} more\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"📋 View Loads ({len(loads)})",
                        callback_data=f"company_loads_{company_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"👥 View Drivers ({len(drivers)})",
                        callback_data=f"company_drivers_list_{company_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📢 Broadcast to Company",
                        callback_data=f"broadcast_company_{company_id}"
                    )
                ],
                [InlineKeyboardButton(text="🔙 Back", callback_data="all_companies")]
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    @staticmethod
    async def handle_system_stats(callback: types.CallbackQuery, db: Session, user_data: dict):
        """Handle system statistics view"""
        if not user_data or user_data["role"] != "dispatcher":
            await callback.answer("Access denied!", show_alert=True)
            return

        try:
            from app.db.models import Load, Driver, Company, Dispatchers

            total_loads = db.query(Load).count()
            total_drivers = db.query(Driver).count()
            total_companies = db.query(Company).count()
            total_dispatchers = db.query(Dispatchers).count()

            unassigned_loads = db.query(Load).filter(Load.driver_id.is_(None)).count()
            assigned_loads = db.query(Load).filter(Load.driver_id.isnot(None)).count()
            telegram_drivers = db.query(Driver).filter(Driver.chat_id.isnot(None)).count()

            stats_text = f"""
📊 *System Statistics*

*📋 Load Statistics:*
• Total Loads: {total_loads}
• Assigned Loads: {assigned_loads}
• Unassigned Loads: {unassigned_loads}

*👥 Driver Statistics:*
• Total Drivers: {total_drivers}
• Telegram-Enabled: {telegram_drivers}
• Coverage: {(telegram_drivers/total_drivers*100):.1f}% if total_drivers else 0%

*🏢 Company Statistics:*
• Total Companies: {total_companies}
• Total Dispatchers: {total_dispatchers}

*🔄 Cross-Company Status:*
• Cross-Company Access: ✅ Enabled
• Multi-Company Operations: ✅ Active
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
                parse_mode="Markdown"
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

        await callback.answer()

    @staticmethod
    async def handle_send_to_driver(callback: types.CallbackQuery, user_data: dict, db: Session):
        """Handle send message to specific driver"""
        if not user_data or user_data["role"] != "dispatcher":
            await callback.answer("Access denied!", show_alert=True)
            return

        try:
            from app.db.models import Driver

            drivers = db.query(Driver).filter(Driver.chat_id.isnot(None)).all()

            if not drivers:
                await callback.message.edit_text(
                    "❌ No drivers connected to Telegram.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🔙 Back", callback_data="send_notifications"
                                )
                            ]
                        ]
                    ),
                )
            else:
                text = "👤 Select Driver:\n\n"
                keyboard_buttons = []

                for driver in drivers[:10]:  # Limit to 10 drivers
                    company_name = driver.company.name if driver.company else "No Company"
                    driver_escaped = escape_markdown(driver.name)
                    company_escaped = escape_markdown(company_name)
                    
                    text += f"• {driver_escaped} ({company_escaped})\n"
                    keyboard_buttons.append(
                        [
                            InlineKeyboardButton(
                                text=f"👤 {driver.name} ({company_name})",
                                callback_data=f"select_driver_msg_{driver.id}",
                            )
                        ]
                    )

                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text="🔙 Back", callback_data="send_notifications"
                        )
                    ]
                )

                await callback.message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"Error in send to driver: {e}")
            await callback.message.edit_text(
                "❌ Error retrieving drivers.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Back", callback_data="send_notifications"
                            )
                        ]
                    ]
                ),
            )

        await callback.answer()

    @staticmethod
    async def handle_assign_driver(callback: types.CallbackQuery, db: Session):
        """Handle driver assignment to load - UPDATED FOR CROSS-COMPANY ACCESS"""
        load_id = int(callback.data.split("_")[2])

        load_service = LoadBotService(db)

        # Get ALL drivers across ALL companies
        drivers = await load_service.get_available_drivers()

        if not drivers:
            await callback.answer("No drivers available!", show_alert=True)
            return

        # Group drivers by company for better organization
        drivers_by_company = defaultdict(list)

        for driver in drivers:
            company_name = driver.company.name if driver.company else "No Company"
            drivers_by_company[company_name].append(driver)

        keyboard_buttons = []

        # Add company selection buttons first for better UX
        if len(drivers_by_company) > 3:  # If many companies, show company filter
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="🏢 Filter by Company",
                    callback_data=f"filter_company_{load_id}"
                )
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="👥 Show All Drivers",
                    callback_data=f"show_all_drivers_{load_id}"
                )
            ])

        # Add drivers organized by company (limit display to prevent overflow)
        total_shown = 0
        for company_name, company_drivers in drivers_by_company.items():
            # Add company header for organization
            if len(drivers_by_company) > 1:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🏢 {company_name} ({len(company_drivers)} drivers)",
                        callback_data="company_header"  # Non-functional, just for display
                    )
                ])

            # Add drivers from this company
            for driver in company_drivers[:5]:  # Limit per company to prevent overflow
                if total_shown >= 15:  # Total limit
                    break
                    
                driver_text = f"👤 {driver.name}"
                if driver.chat_id:
                    driver_text += " 📱"  # Telegram available
                
                # Show company if multiple companies
                if len(drivers_by_company) > 1:
                    driver_text += f" ({company_name})"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=driver_text,
                        callback_data=f"select_driver_{load_id}_{driver.id}",
                    )
                ])
                total_shown += 1

            if total_shown >= 15:
                break

        # Add pagination or "show more" if there are many drivers
        if total_shown < len(drivers):
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"➡️ Show More ({len(drivers) - total_shown} remaining)",
                    callback_data=f"show_more_drivers_{load_id}_{total_shown}"
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")
        ])

        message_text = (
            f"🚛 **Select driver for load:**\n\n"
            f"Available drivers from **all companies**:\n"
            f"📱 = Telegram notifications available\n\n"
            f"**Total:** {len(drivers)} drivers from {len(drivers_by_company)} companies"
        )

        await callback.message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    async def handle_filter_by_company(callback: types.CallbackQuery, db: Session):
        """Handle filtering drivers by company"""
        load_id = int(callback.data.split("_")[2])
        
        load_service = LoadBotService(db)
        companies = await load_service.get_all_companies()

        if not companies:
            await callback.answer("No companies found!", show_alert=True)
            return

        keyboard_buttons = []
        for company in companies:
            # Get driver count for this company
            company_drivers = await load_service.get_drivers_by_company(company.id)
            driver_count = len(company_drivers)
            telegram_count = sum(1 for d in company_drivers if d.chat_id)
            
            button_text = f"🏢 {company.name} ({driver_count} drivers"
            if telegram_count > 0:
                button_text += f", {telegram_count} 📱"
            button_text += ")"

            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"company_drivers_{load_id}_{company.id}"
                )
            ])

        keyboard_buttons.extend([
            [InlineKeyboardButton(
                text="👥 Show All Drivers",
                callback_data=f"assign_driver_{load_id}"
            )],
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")]
        ])

        await callback.message.edit_text(
            f"🏢 **Select Company:**\n\nChoose a company to view its drivers:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    async def handle_company_drivers(callback: types.CallbackQuery, db: Session):
        """Handle showing drivers from specific company"""
        parts = callback.data.split("_")
        load_id = int(parts[2])
        company_id = int(parts[3])

        load_service = LoadBotService(db)
        company_drivers = await load_service.get_drivers_by_company(company_id)

        if not company_drivers:
            await callback.answer("No drivers found in this company!", show_alert=True)
            return

        # Get company name
        companies = await load_service.get_all_companies()
        company = next((c for c in companies if c.id == company_id), None)
        company_name = company.name if company else "Unknown Company"

        keyboard_buttons = []
        for driver in company_drivers:
            driver_text = f"👤 {driver.name}"
            if driver.chat_id:
                driver_text += " 📱"

            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=driver_text,
                    callback_data=f"select_driver_{load_id}_{driver.id}",
                )
            ])

        keyboard_buttons.extend([
            [InlineKeyboardButton(
                text="🏢 Other Companies",
                callback_data=f"filter_company_{load_id}"
            )],
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")]
        ])

        await callback.message.edit_text(
            f"🏢 **{company_name} Drivers:**\n\n"
            f"Select a driver from {company_name}:\n"
            f"📱 = Telegram notifications available",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()

    @staticmethod
    async def handle_load_details(callback: types.CallbackQuery, db: Session):
        """Show detailed load information"""
        load_id = int(callback.data.split("_")[2])

        load_service = LoadBotService(db)
        load_details = await load_service.get_load_details(load_id)

        if not load_details:
            await callback.answer("Load not found!", show_alert=True)
            return

        load = load_details["load"]
        legs = load_details["legs"]

        text = f"🚛 **Load Details: {load.trip_id}**\n\n"
        text += f"**📍 Route:** {load.pickup_address} → {load.dropoff_address}\n"
        text += f"**🕐 Start:** {load.start_time_str}\n"
        text += f"**🕐 End:** {load.end_time_str}\n"
        text += f"**💰 Rate:** ${float(load.rate):,.2f}\n"
        text += f"**📏 Distance:** {float(load.distance):,.1f} mi\n"

        # Show company information
        if load.company:
            text += f"**🏢 Company:** {load.company.name}\n"

        if load.assigned_driver:
            # Get driver details to show company
            from app.db.models import Driver
            driver = db.query(Driver).filter(Driver.id == load.driver_id).first()
            driver_company = driver.company.name if driver and driver.company else "Unknown"
            text += f"**👤 Driver:** {load.assigned_driver} ({driver_company})\n"
        else:
            text += "**👤 Driver:** Not assigned\n"

        if legs:
            text += f"\n**📋 Legs ({len(legs)}):**\n"
            for i, leg in enumerate(legs, 1):
                text += f"{i}. {leg.pickup_facility_name} → {leg.dropoff_facility_name}\n"
                text += f"   {leg.pickup_time_str} - {leg.dropoff_time_str}\n"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚛 Assign Driver (All Companies)",
                        callback_data=f"assign_driver_{load.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📢 Notify Driver",
                        callback_data=f"notify_driver_{load.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Load Statistics",
                        callback_data=f"load_stats_{load.id}",
                    )
                ],
                [InlineKeyboardButton(text="🔙 Back", callback_data="my_loads")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    @staticmethod
    async def handle_driver_selection(callback: types.CallbackQuery, db: Session):
        """Handle driver selection for load assignment - UPDATED FOR CROSS-COMPANY"""
        parts = callback.data.split("_")
        load_id = int(parts[2])
        driver_id = int(parts[3])

        try:
            load_service = LoadBotService(db)
            
            # Get driver and load info
            from app.db.repositories.driver_repository import DriverRepository
            driver_repo = DriverRepository(db)
            driver = driver_repo.get_driver_by_id(driver_id)
            load_data = load_service.get_load_details(load_id)

            if not driver or not load_data:
                await callback.answer("Driver or load not found!", show_alert=True)
                return

            load = load_data["load"]
            
            # Check if this is a cross-company assignment
            is_cross_company = driver.company_id != load.company_id if load.company_id else False
            
            # Update load with driver assignment using the load service
            success = await load_service.assign_driver_to_load(load_id, driver_id)
            
            if success:
                assignment_type = "Cross-company" if is_cross_company else "Same company"
                driver_company = driver.company.name if driver.company else "No Company"
                load_company = load.company.name if load.company else "No Company"
                
                success_message = f"✅ **Driver Assigned Successfully!**\n\n"
                success_message += f"**Driver:** {driver.name}\n"
                success_message += f"**Driver Company:** {driver_company}\n"
                success_message += f"**Load:** {load.trip_id}\n"
                success_message += f"**Load Company:** {load_company}\n"
                success_message += f"**Assignment Type:** {assignment_type}\n"
                
                if is_cross_company:
                    success_message += f"\n🔄 This is a cross-company assignment!"

                keyboard_buttons = []
                
                # Add notification button if driver has Telegram
                if driver.chat_id:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text="📢 Notify Driver",
                            callback_data=f"notify_driver_{load_id}",
                        )
                    ])
                else:
                    success_message += f"\n⚠️ Driver doesn't have Telegram notifications set up"

                keyboard_buttons.extend([
                    [
                        InlineKeyboardButton(
                            text="📋 View Load Details",
                            callback_data=f"view_load_{load_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔙 Back to Loads", callback_data="my_loads"
                        )
                    ],
                ])

                await callback.message.edit_text(
                    success_message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
                    parse_mode="Markdown",
                )
            else:
                await callback.answer("Failed to assign driver!", show_alert=True)

        except Exception as e:
            logger.error(f"Error assigning driver: {e}")
            await callback.answer("Error assigning driver!", show_alert=True)

        await callback.answer()

    @staticmethod
    async def handle_notify_driver(callback: types.CallbackQuery, db: Session):
        """Handle sending notification to driver"""
        load_id = int(callback.data.split("_")[2])

        try:
            notification_service = NotificationService(db)
            success = await notification_service.notify_driver_about_load(load_id)

            if success:
                await callback.answer(
                    "✅ Notification sent successfully!", show_alert=True
                )
            else:
                await callback.answer(
                    "❌ Failed to send notification! Driver may not have Telegram set up.", show_alert=True
                )

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            await callback.answer("❌ Error sending notification!", show_alert=True)

        await callback.answer()

    @staticmethod
    async def handle_broadcast_message(callback: types.CallbackQuery, state: FSMContext):
        """Handle broadcast message setup - UPDATED FOR CROSS-COMPANY"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 All Drivers (All Companies)",
                        callback_data="broadcast_all_drivers"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏢 Drivers by Company",
                        callback_data="broadcast_by_company"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📱 Only Telegram-Enabled Drivers",
                        callback_data="broadcast_telegram_only"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Cancel",
                        callback_data="send_notifications"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            "📢 **Broadcast Message**\n\n"
            "Choose the scope of your broadcast:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_all_drivers(callback: types.CallbackQuery, state: FSMContext):
        """Handle broadcast to all drivers across all companies"""
        await state.update_data(broadcast_type="all_drivers")
        await state.set_state(NotificationStates.waiting_for_message)
        
        await callback.message.edit_text(
            "📢 **Broadcast to All Drivers**\n\n"
            "Enter the message you want to send to **all drivers across all companies**:\n\n"
            "⚠️ This will send to ALL drivers with Telegram notifications enabled."
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_by_company(callback: types.CallbackQuery, state: FSMContext, db: Session):
        """Handle broadcast by company selection"""
        load_service = LoadBotService(db)
        companies = await load_service.get_all_companies()

        if not companies:
            await callback.answer("No companies found!", show_alert=True)
            return

        keyboard_buttons = []
        for company in companies:
            company_drivers = await load_service.get_drivers_by_company(company.id)
            telegram_drivers = sum(1 for d in company_drivers if d.chat_id)
            
            button_text = f"🏢 {company.name} ({telegram_drivers} drivers)"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"broadcast_company_{company.id}"
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Back", callback_data="broadcast_message")
        ])

        await state.set_state(NotificationStates.waiting_for_company_selection)
        await callback.message.edit_text(
            "🏢 **Select Company for Broadcast:**\n\n"
            "Choose which company's drivers to notify:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown"
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_telegram_only(callback: types.CallbackQuery, state: FSMContext):
        """Handle broadcast to only Telegram-enabled drivers"""
        await state.update_data(broadcast_type="telegram_only")
        await state.set_state(NotificationStates.waiting_for_message)
        
        await callback.message.edit_text(
            "📱 **Broadcast to Telegram-Enabled Drivers**\n\n"
            "Enter the message you want to send to **all drivers with Telegram notifications** (across all companies):"
        )
        await callback.answer()

    @staticmethod
    async def handle_broadcast_message_input(
        message: types.Message, state: FSMContext, db: Session, user_data: dict
    ):
        """Handle broadcast message input - UPDATED FOR CROSS-COMPANY"""
        if user_data["role"] != "dispatcher":
            await message.answer("Access denied!")
            return

        state_data = await state.get_data()
        broadcast_text = message.text.strip()
        broadcast_type = state_data.get("broadcast_type", "all_drivers")
        company_id = state_data.get("company_id")

        try:
            from app.db.models import Driver, TelegramChat
            from aiogram import Bot
            from app.config import get_settings

            settings = get_settings()
            bot = Bot(token=settings.telegram_bot_token)

            # Get drivers based on broadcast type
            if broadcast_type == "company" and company_id:
                drivers_query = db.query(Driver).filter(
                    Driver.company_id == company_id,
                    Driver.chat_id.isnot(None)
                )
                scope_text = f"company drivers"
            elif broadcast_type == "telegram_only":
                drivers_query = db.query(Driver).filter(Driver.chat_id.isnot(None))
                scope_text = "Telegram-enabled drivers (all companies)"
            else:  # all_drivers
                drivers_query = db.query(Driver).filter(Driver.chat_id.isnot(None))
                scope_text = "all drivers (all companies)"

            drivers_with_chats = drivers_query.all()

            sent_count = 0
            failed_count = 0
            company_breakdown = defaultdict(int)

            for driver in drivers_with_chats:
                try:
                    chat = (
                        db.query(TelegramChat)
                        .filter(TelegramChat.id == driver.chat_id)
                        .first()
                    )
                    if chat and chat.chat_token:
                        # Include company info in message for cross-company context
                        company_name = driver.company.name if driver.company else "No Company"
                        formatted_message = (
                            f"📢 **Message from {user_data['name']} (Dispatcher)**\n\n"
                            f"{broadcast_text}\n\n"
                            f"---\n"
                            f"Driver: {driver.name} ({company_name})"
                        )
                        await bot.send_message(
                            chat_id=chat.chat_token,
                            text=formatted_message,
                            parse_mode="Markdown"
                        )
                        sent_count += 1
                        company_breakdown[company_name] += 1
                except Exception as e:
                    logger.error(f"Failed to send message to driver {driver.name}: {e}")
                    failed_count += 1

            # Create detailed results message
            result_message = f"📢 **Broadcast Completed!**\n\n"
            result_message += f"**Scope:** {scope_text}\n"
            result_message += f"**✅ Sent:** {sent_count}\n"
            result_message += f"**❌ Failed:** {failed_count}\n\n"
            
            if company_breakdown:
                result_message += "**📊 Company Breakdown:**\n"
                for company, count in sorted(company_breakdown.items()):
                    result_message += f"• {company}: {count} drivers\n"

            await message.answer(result_message, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            await message.answer("❌ Error sending broadcast message!")

        await state.clear()

    @staticmethod
    async def handle_driver_statistics(callback: types.CallbackQuery, db: Session):
        """Show driver statistics across all companies"""
        try:
            load_service = LoadBotService(db)
            company_stats = await load_service.get_company_statistics()
            
            if not company_stats:
                await callback.answer("No statistics available!", show_alert=True)
                return

            text = "📊 **Driver Statistics (All Companies)**\n\n"
            
            total_drivers = 0
            total_telegram = 0
            total_loads = 0
            total_unassigned = 0
            
            for stat in company_stats:
                company = stat["company"]
                text += f"**🏢 {company.name}**\n"
                text += f"• Drivers: {stat['total_drivers']}\n"
                text += f"• With Telegram: {stat['drivers_with_telegram']}\n"
                text += f"• Loads: {stat['total_loads']}\n"
                text += f"• Unassigned Loads: {stat['unassigned_loads']}\n\n"
                
                total_drivers += stat['total_drivers']
                total_telegram += stat['drivers_with_telegram']
                total_loads += stat['total_loads']
                total_unassigned += stat['unassigned_loads']
            
            text += f"**📈 System Totals:**\n"
            text += f"• Total Drivers: {total_drivers}\n"
            text += f"• Telegram-Enabled: {total_telegram}\n"
            text += f"• Total Loads: {total_loads}\n"
            text += f"• Unassigned Loads: {total_unassigned}\n"

            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_menu")]
                    ]
                ),
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error showing driver statistics: {e}")
            await callback.answer("Error retrieving statistics!", show_alert=True)

        await callback.answer()

    @staticmethod
    async def handle_company_broadcast_selection(callback: types.CallbackQuery, state: FSMContext):
        """Handle company selection for broadcast"""
        company_id = int(callback.data.split("_")[2])
        
        await state.update_data(broadcast_type="company", company_id=company_id)
        await state.set_state(NotificationStates.waiting_for_message)
        
        # Get company name for confirmation
        from app.db.models import Company
        from app.db.database import SessionLocal
        
        db = SessionLocal()
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            company_name = company.name if company else "Unknown Company"
        finally:
            db.close()
        
        await callback.message.edit_text(
            f"🏢 **Broadcast to {company_name}**\n\n"
            f"Enter the message you want to send to all drivers in **{company_name}**:"
        )
        await callback.answer()

    @staticmethod
    async def handle_show_more_drivers(callback: types.CallbackQuery, db: Session):
        """Handle showing more drivers with pagination"""
        parts = callback.data.split("_")
        load_id = int(parts[3])
        offset = int(parts[4])

        load_service = LoadBotService(db)
        all_drivers = await load_service.get_available_drivers()

        # Show next batch of drivers
        drivers_to_show = all_drivers[offset:offset + 15]
        
        if not drivers_to_show:
            await callback.answer("No more drivers to show!", show_alert=True)
            return

        keyboard_buttons = []
        
        # Group by company for this batch
        drivers_by_company = defaultdict(list)
        for driver in drivers_to_show:
            company_name = driver.company.name if driver.company else "No Company"
            drivers_by_company[company_name].append(driver)

        for company_name, company_drivers in drivers_by_company.items():
            if len(drivers_by_company) > 1:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🏢 {company_name}",
                        callback_data="company_header"
                    )
                ])

            for driver in company_drivers:
                driver_text = f"👤 {driver.name}"
                if driver.chat_id:
                    driver_text += " 📱"
                if len(drivers_by_company) > 1:
                    driver_text += f" ({company_name})"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=driver_text,
                        callback_data=f"select_driver_{load_id}_{driver.id}",
                    )
                ])

        # Add navigation buttons
        nav_buttons = []
        if offset > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Previous",
                    callback_data=f"show_more_drivers_{load_id}_{max(0, offset - 15)}"
                )
            )

        if offset + 15 < len(all_drivers):
            nav_buttons.append(
                InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=f"show_more_drivers_{load_id}_{offset + 15}"
                )
            )

        if nav_buttons:
            keyboard_buttons.append(nav_buttons)

        keyboard_buttons.extend([
            [InlineKeyboardButton(
                text="🏢 Filter by Company",
                callback_data=f"filter_company_{load_id}"
            )],
            [InlineKeyboardButton(text="🔙 Back", callback_data=f"view_load_{load_id}")]
        ])

        current_range = f"{offset + 1}-{min(offset + 15, len(all_drivers))}"
        message_text = (
            f"🚛 **Select driver for load:**\n\n"
            f"Showing drivers {current_range} of {len(all_drivers)}\n"
            f"📱 = Telegram notifications available\n\n"
            f"From **all companies**"
        )

        await callback.message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
            parse_mode="Markdown",
        )
        await callback.answer()