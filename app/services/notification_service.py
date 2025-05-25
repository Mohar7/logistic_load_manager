# app/services/notification_service.py - Updated for cross-company support
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.repositories.load_repository import LoadRepository
from app.db.models import Driver, TelegramChat, Company
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    """
    Service for sending notifications to drivers via Telegram with cross-company support.
    """

    def __init__(self, db: Session):
        self.db = db
        self.load_repository = LoadRepository(db)
        self.base_url = "https://api.telegram.org/bot{token}/sendMessage"

    async def notify_driver_about_load(
        self, load_id: int, driver_id: Optional[int] = None
    ) -> bool:
        """
        Notify a driver about a load assignment via Telegram.
        Now supports cross-company assignments.

        Args:
            load_id (int): ID of the load to notify about
            driver_id (int, optional): ID of the driver to notify. If None, uses the driver assigned to the load.

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # Get load information
            load = self.load_repository.get_load_by_id(load_id)
            if not load:
                logger.error(f"Load with ID {load_id} not found")
                return False

            # Get the driver
            target_driver_id = driver_id if driver_id is not None else load.driver_id
            if not target_driver_id:
                logger.error(
                    f"No driver assigned to load {load_id} and no driver ID provided"
                )
                return False

            driver = self.db.query(Driver).filter(Driver.id == target_driver_id).first()
            if not driver:
                logger.error(f"Driver with ID {target_driver_id} not found")
                return False

            # Check if driver has a Telegram chat
            if not driver.chat_id:
                logger.error(
                    f"Driver {driver.name} does not have a Telegram chat assigned"
                )
                return False

            chat = (
                self.db.query(TelegramChat)
                .filter(TelegramChat.id == driver.chat_id)
                .first()
            )
            if not chat or not chat.chat_token:
                logger.error(
                    f"Telegram chat for driver {driver.name} not found or has no token"
                )
                return False

            # Get legs for the load
            legs = self.load_repository.get_legs_for_load(load_id)

            # Create enhanced message with cross-company information
            message = self._create_load_notification_message(load, legs, driver)

            # Send notification
            return await self._send_telegram_message(chat.chat_token, message)

        except Exception as e:
            logger.error(f"Error in notify_driver_about_load: {str(e)}")
            return False

    def _create_load_notification_message(self, load, legs, driver) -> str:
        """
        Create a formatted notification message for a load assignment with cross-company info.

        Args:
            load: Load object
            legs: List of Leg objects
            driver: Driver object

        Returns:
            str: Formatted message
        """
        # Get company information for cross-company context
        driver_company = driver.company.name if driver.company else "No Company"
        load_company = load.company.name if load.company else "No Company"
        is_cross_company = (
            driver.company_id != load.company_id if load.company_id else False
        )

        message = f"🚚 **NEW LOAD ASSIGNMENT** 🚚\n\n"
        message += f"Hello **{driver.name}**,\n\n"
        message += f"You have been assigned to load **{load.trip_id}**:\n\n"

        message += f"📍 **Pickup:** {load.pickup_address}\n"
        message += f"🕐 **Pickup Time:** {load.start_time_str}\n\n"

        message += f"🏁 **Dropoff:** {load.dropoff_address}\n"
        message += f"🕐 **Dropoff Time:** {load.end_time_str}\n\n"

        message += f"💰 **Rate:** ${float(load.rate):,.2f}\n"
        message += f"📏 **Distance:** {float(load.distance):,.1f} mi\n\n"

        # Add company information for transparency
        message += f"**📋 Assignment Details:**\n"
        message += f"• **Your Company:** {driver_company}\n"
        message += f"• **Load Company:** {load_company}\n"

        if is_cross_company:
            message += f"• **Type:** Cross-Company Assignment 🔄\n"
        else:
            message += f"• **Type:** Same Company Assignment ✅\n"

        if legs:
            message += f"\n**📦 Load Details ({len(legs)} legs):**\n"
            for i, leg in enumerate(legs, 1):
                message += f"\n**Leg {i}:**\n"
                message += (
                    f"📍 {leg.pickup_facility_name} → {leg.dropoff_facility_name}\n"
                )
                message += f"🕐 {leg.pickup_time_str} - {leg.dropoff_time_str}\n"
                message += f"📏 {float(leg.distance):,.1f} mi\n"

        message += f"\n**⚠️ Please confirm receipt of this assignment.**\n"
        message += f"Contact your dispatcher if you have any questions."

        return message

    async def _send_telegram_message(self, chat_token: int, message: str) -> bool:
        """
        Send a message via Telegram API.

        Args:
            chat_token (int): Telegram chat token
            message (str): Message to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        bot_token = (
            settings.telegram_bot_token
            if hasattr(settings, "telegram_bot_token")
            else "YOUR_TELEGRAM_BOT_TOKEN"
        )

        url = self.base_url.format(token=bot_token)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    json={
                        "chat_id": chat_token,
                        "text": message,
                        "parse_mode": "Markdown",
                    },
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("ok", False)
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Telegram API error: {response.status} - {error_text}"
                        )
                        return False
            except Exception as e:
                logger.error(f"Error sending Telegram message: {str(e)}")
                return False

    async def notify_multiple_drivers(
        self, load_id: int, driver_ids: list
    ) -> Dict[int, bool]:
        """
        Notify multiple drivers about a load (useful for cross-company broadcasts).

        Args:
            load_id (int): ID of the load to notify about
            driver_ids (list): List of driver IDs to notify

        Returns:
            Dict[int, bool]: Dictionary mapping driver IDs to notification success status
        """
        results = {}

        for driver_id in driver_ids:
            results[driver_id] = await self.notify_driver_about_load(load_id, driver_id)

        return results

    async def broadcast_message_to_all_drivers(
        self, message: str, sender_name: str, filter_by_telegram: bool = True
    ) -> Dict[str, Any]:
        """
        Broadcast a message to all drivers across all companies.

        Args:
            message (str): Message to broadcast
            sender_name (str): Name of the sender
            filter_by_telegram (bool): Only send to drivers with Telegram enabled

        Returns:
            Dict[str, Any]: Results of the broadcast
        """
        try:
            # Get all drivers across all companies
            if filter_by_telegram:
                drivers = (
                    self.db.query(Driver)
                    .filter(Driver.chat_id.isnot(None))
                    .join(Company, Driver.company_id == Company.id, isouter=True)
                    .all()
                )
            else:
                drivers = (
                    self.db.query(Driver)
                    .join(Company, Driver.company_id == Company.id, isouter=True)
                    .all()
                )

            sent_count = 0
            failed_count = 0
            company_breakdown = {}

            for driver in drivers:
                if not driver.chat_id:
                    continue

                try:
                    chat = (
                        self.db.query(TelegramChat)
                        .filter(TelegramChat.id == driver.chat_id)
                        .first()
                    )

                    if chat and chat.chat_token:
                        company_name = (
                            driver.company.name if driver.company else "No Company"
                        )

                        # Enhanced broadcast message with company context
                        formatted_message = (
                            f"📢 **Broadcast Message**\n\n"
                            f"**From:** {sender_name} (Dispatcher)\n"
                            f"**To:** {driver.name} ({company_name})\n\n"
                            f"**Message:**\n{message}\n\n"
                            f"---\n"
                            f"This message was sent to drivers across all companies."
                        )

                        success = await self._send_telegram_message(
                            chat.chat_token, formatted_message
                        )

                        if success:
                            sent_count += 1
                            company_breakdown[company_name] = (
                                company_breakdown.get(company_name, 0) + 1
                            )
                        else:
                            failed_count += 1

                except Exception as e:
                    logger.error(
                        f"Failed to send broadcast to driver {driver.name}: {e}"
                    )
                    failed_count += 1

            return {
                "sent_count": sent_count,
                "failed_count": failed_count,
                "company_breakdown": company_breakdown,
                "total_drivers": len(drivers),
            }

        except Exception as e:
            logger.error(f"Error in broadcast_message_to_all_drivers: {str(e)}")
            return {
                "sent_count": 0,
                "failed_count": 0,
                "company_breakdown": {},
                "total_drivers": 0,
                "error": str(e),
            }

    async def broadcast_message_to_company(
        self, message: str, sender_name: str, company_id: int
    ) -> Dict[str, Any]:
        """
        Broadcast a message to all drivers in a specific company.

        Args:
            message (str): Message to broadcast
            sender_name (str): Name of the sender
            company_id (int): ID of the company

        Returns:
            Dict[str, Any]: Results of the broadcast
        """
        try:
            # Get company info
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return {
                    "sent_count": 0,
                    "failed_count": 0,
                    "error": "Company not found",
                }

            # Get drivers from specific company with Telegram
            drivers = (
                self.db.query(Driver)
                .filter(Driver.company_id == company_id, Driver.chat_id.isnot(None))
                .all()
            )

            sent_count = 0
            failed_count = 0

            for driver in drivers:
                try:
                    chat = (
                        self.db.query(TelegramChat)
                        .filter(TelegramChat.id == driver.chat_id)
                        .first()
                    )

                    if chat and chat.chat_token:
                        formatted_message = (
                            f"📢 **Company Message**\n\n"
                            f"**From:** {sender_name} (Dispatcher)\n"
                            f"**To:** {driver.name}\n"
                            f"**Company:** {company.name}\n\n"
                            f"**Message:**\n{message}\n\n"
                            f"---\n"
                            f"This message was sent to all {company.name} drivers."
                        )

                        success = await self._send_telegram_message(
                            chat.chat_token, formatted_message
                        )

                        if success:
                            sent_count += 1
                        else:
                            failed_count += 1

                except Exception as e:
                    logger.error(
                        f"Failed to send company broadcast to driver {driver.name}: {e}"
                    )
                    failed_count += 1

            return {
                "sent_count": sent_count,
                "failed_count": failed_count,
                "company_name": company.name,
                "total_drivers": len(drivers),
            }

        except Exception as e:
            logger.error(f"Error in broadcast_message_to_company: {str(e)}")
            return {"sent_count": 0, "failed_count": 0, "error": str(e)}

    async def notify_cross_company_assignment(
        self, load_id: int, driver_id: int, dispatcher_name: str
    ) -> bool:
        """
        Send special notification for cross-company assignments.

        Args:
            load_id (int): ID of the load
            driver_id (int): ID of the driver
            dispatcher_name (str): Name of the dispatcher making the assignment

        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Get load and driver info
            load = self.load_repository.get_load_by_id(load_id)
            driver = self.db.query(Driver).filter(Driver.id == driver_id).first()

            if not load or not driver:
                return False

            # Check if it's actually a cross-company assignment
            is_cross_company = (
                driver.company_id != load.company_id if load.company_id else False
            )

            if not is_cross_company:
                # Use regular notification for same-company assignments
                return await self.notify_driver_about_load(load_id, driver_id)

            # Send special cross-company notification
            if not driver.chat_id:
                logger.warning(f"Driver {driver.name} doesn't have Telegram enabled")
                return False

            chat = (
                self.db.query(TelegramChat)
                .filter(TelegramChat.id == driver.chat_id)
                .first()
            )

            if not chat or not chat.chat_token:
                return False

            driver_company = driver.company.name if driver.company else "No Company"
            load_company = load.company.name if load.company else "No Company"

            message = (
                f"🔄 **CROSS-COMPANY ASSIGNMENT** 🔄\n\n"
                f"Hello **{driver.name}**,\n\n"
                f"You have been assigned to a cross-company load by **{dispatcher_name}**.\n\n"
                f"**📋 Assignment Details:**\n"
                f"• **Load ID:** {load.trip_id}\n"
                f"• **Your Company:** {driver_company}\n"
                f"• **Load Company:** {load_company}\n\n"
                f"**🚛 Load Information:**\n"
                f"• **Route:** {load.pickup_address} → {load.dropoff_address}\n"
                f"• **Start:** {load.start_time_str}\n"
                f"• **End:** {load.end_time_str}\n"
                f"• **Rate:** ${float(load.rate):,.2f}\n"
                f"• **Distance:** {float(load.distance):,.1f} mi\n\n"
                f"**⚠️ Important:**\n"
                f"This is a cross-company assignment. Please coordinate with both companies if needed.\n\n"
                f"Please confirm receipt and contact the dispatcher if you have questions."
            )

            return await self._send_telegram_message(chat.chat_token, message)

        except Exception as e:
            logger.error(f"Error in notify_cross_company_assignment: {str(e)}")
            return False

    async def get_notification_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about notification capabilities across companies.

        Returns:
            Dict[str, Any]: Notification statistics
        """
        try:
            # Get all drivers
            all_drivers = (
                self.db.query(Driver)
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .all()
            )

            # Get drivers with Telegram
            telegram_drivers = [d for d in all_drivers if d.chat_id]

            # Group by company
            company_stats = {}
            for driver in all_drivers:
                company_name = driver.company.name if driver.company else "No Company"
                if company_name not in company_stats:
                    company_stats[company_name] = {
                        "total_drivers": 0,
                        "telegram_enabled": 0,
                    }

                company_stats[company_name]["total_drivers"] += 1
                if driver.chat_id:
                    company_stats[company_name]["telegram_enabled"] += 1

            return {
                "total_drivers": len(all_drivers),
                "telegram_enabled_drivers": len(telegram_drivers),
                "notification_coverage": (
                    len(telegram_drivers) / len(all_drivers) * 100
                )
                if all_drivers
                else 0,
                "company_breakdown": company_stats,
                "cross_company_capable": len(telegram_drivers) > 0,
            }

        except Exception as e:
            logger.error(f"Error getting notification statistics: {str(e)}")
            return {
                "total_drivers": 0,
                "telegram_enabled_drivers": 0,
                "notification_coverage": 0,
                "company_breakdown": {},
                "cross_company_capable": False,
                "error": str(e),
            }
