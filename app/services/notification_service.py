# app/services/notification_service.py
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.repositories.load_repository import LoadRepository
from app.db.models import Driver, TelegramChat
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    """
    Service for sending notifications to drivers via Telegram.
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

            # Create message
            message = self._create_load_notification_message(load, legs, driver.name)

            # Send notification
            return await self._send_telegram_message(chat.chat_token, message)

        except Exception as e:
            logger.error(f"Error in notify_driver_about_load: {str(e)}")
            return False

    def _create_load_notification_message(self, load, legs, driver_name: str) -> str:
        """
        Create a formatted notification message for a load assignment.

        Args:
            load: Load object
            legs: List of Leg objects
            driver_name (str): Name of the driver

        Returns:
            str: Formatted message
        """
        message = f"🚚 NEW LOAD ASSIGNMENT 🚚\n\n"
        message += f"Hello {driver_name},\n\n"
        message += f"You have been assigned to load {load.trip_id}:\n\n"
        message += f"📍 Pickup: {load.pickup_address} ({load.start_time_str})\n"
        message += f"🏁 Dropoff: {load.dropoff_address} ({load.end_time_str})\n"
        message += f"💰 Rate: ${float(load.rate):.2f}\n"
        message += f"📏 Distance: {float(load.distance):.1f} mi\n\n"

        if legs:
            message += f"This load has {len(legs)} legs:\n\n"
            for i, leg in enumerate(legs, 1):
                message += (
                    f"Leg {i}: {leg.pickup_facility_id} to {leg.dropoff_facility_id}\n"
                )
                message += f"📏 Distance: {float(leg.distance):.1f} mi\n"
                if i < len(legs):
                    message += "\n"

        message += "\nPlease confirm receipt of this assignment."

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
        # In a real application, you would get the bot token from settings
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
        Notify multiple drivers about a load.

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
