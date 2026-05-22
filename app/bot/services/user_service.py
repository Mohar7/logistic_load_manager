# app/bot/services/user_service.py - Updated for cross-company access
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, Dispatchers

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing bot users and registration - Updated"""

    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def create_user_registration(
        self, telegram_id: int, username: str, name: str, role: str
    ) -> bool:
        """Create a user registration request"""
        try:
            # Check if user already exists
            existing_user = (
                await self.db.execute(
                    select(Dispatchers).where(Dispatchers.telegram_id == telegram_id)
                )
            ).scalar_one_or_none()

            if existing_user:
                return False

            # Create user with role - dispatchers no longer need company assignment
            user = Dispatchers(name=name, telegram_id=telegram_id, role=role)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(
                f"Created user registration: {name} ({role}) - Telegram ID: {telegram_id}"
            )
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error creating user registration: {e}")
            await self.db.rollback()
            return False

    async def complete_dispatcher_registration(
        self, telegram_id: int, company_id: int, name: str
    ) -> bool:
        """Complete dispatcher registration - company is now optional/informational"""
        try:
            # Check if dispatcher exists
            dispatcher = (
                await self.db.execute(
                    select(Dispatchers).where(Dispatchers.telegram_id == telegram_id)
                )
            ).scalar_one_or_none()

            if not dispatcher:
                # Create new dispatcher - they can manage all companies
                dispatcher = Dispatchers(
                    name=name, telegram_id=telegram_id, role="dispatcher"
                )
                self.db.add(dispatcher)
                await self.db.commit()
                await self.db.refresh(dispatcher)

            logger.info(
                f"Completed dispatcher registration: {name} - Can manage all companies"
            )
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error completing dispatcher registration: {e}")
            await self.db.rollback()
            return False

    async def approve_manager(self, telegram_id: int) -> bool:
        """Approve a manager registration"""
        try:
            user = (
                await self.db.execute(
                    select(Dispatchers).where(
                        Dispatchers.telegram_id == telegram_id,
                        Dispatchers.role == "manager",
                    )
                )
            ).scalar_one_or_none()

            if not user:
                return False

            # You could add a status column to track approval
            # For now, we'll just log the approval
            logger.info(f"Manager approved: {user.name} - Telegram ID: {telegram_id}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error approving manager: {e}")
            await self.db.rollback()
            return False

    async def get_companies(self) -> list[Company]:
        """Get all available companies"""
        try:
            result = await self.db.execute(select(Company))
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting companies: {e}")
            return []

    async def get_user_by_telegram_id(
        self, telegram_id: int
    ) -> dict[str, Any] | None:
        """Get user information by Telegram ID"""
        try:
            # Check for user in Dispatchers table (now handles both dispatchers and managers)
            user = (
                await self.db.execute(
                    select(Dispatchers).where(Dispatchers.telegram_id == telegram_id)
                )
            ).scalar_one_or_none()

            if user:
                return {
                    "id": user.id,
                    "name": user.name,
                    "telegram_id": user.telegram_id,
                    "role": user.role
                    or "dispatcher",  # Default to dispatcher if role is None
                }

            return None

        except SQLAlchemyError as e:
            logger.error(f"Error getting user: {e}")
            return None

    async def get_all_users(self) -> list[dict[str, Any]]:
        """Get all registered users"""
        try:
            result = await self.db.execute(select(Dispatchers))
            users = list(result.scalars().all())

            return [
                {
                    "id": user.id,
                    "name": user.name,
                    "telegram_id": user.telegram_id,
                    "role": user.role or "dispatcher",
                }
                for user in users
            ]

        except SQLAlchemyError as e:
            logger.error(f"Error getting all users: {e}")
            return []

    async def get_pending_managers(self) -> list[dict[str, Any]]:
        """Get managers pending approval"""
        try:
            # You could add a status column and filter by status='pending'
            # For now, we'll just return all managers
            result = await self.db.execute(
                select(Dispatchers).where(Dispatchers.role == "manager")
            )
            managers = list(result.scalars().all())

            return [
                {
                    "id": manager.id,
                    "name": manager.name,
                    "telegram_id": manager.telegram_id,
                    "role": manager.role,
                }
                for manager in managers
            ]

        except SQLAlchemyError as e:
            logger.error(f"Error getting pending managers: {e}")
            return []

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        try:
            user = (
                await self.db.execute(
                    select(Dispatchers).where(Dispatchers.id == user_id)
                )
            ).scalar_one_or_none()
            if not user:
                return False

            await self.db.delete(user)
            await self.db.commit()

            logger.info(f"Deleted user: {user.name} ({user.role})")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error deleting user: {e}")
            await self.db.rollback()
            return False

    async def update_user_role(self, telegram_id: int, new_role: str) -> bool:
        """Update a user's role"""
        try:
            user = (
                await self.db.execute(
                    select(Dispatchers).where(Dispatchers.telegram_id == telegram_id)
                )
            ).scalar_one_or_none()

            if not user:
                return False

            old_role = user.role
            user.role = new_role
            await self.db.commit()

            logger.info(f"Updated user role: {user.name} from {old_role} to {new_role}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error updating user role: {e}")
            await self.db.rollback()
            return False

    async def notify_admins_new_registration(
        self, telegram_id: int, name: str, role: str = "manager"
    ):
        """Notify administrators about new registration"""
        try:
            # Get all existing managers to notify them
            result = await self.db.execute(
                select(Dispatchers).where(Dispatchers.role == "manager")
            )
            managers = list(result.scalars().all())

            if managers:
                from aiogram import Bot

                from app.config import get_settings

                settings = get_settings()
                bot = Bot(token=settings.telegram_bot_token)

                notification_message = (
                    f"🔔 **New {role.title()} Registration**\n\n"
                    f"**Name:** {name}\n"
                    f"**Role:** {role.title()}\n"
                    f"**Telegram ID:** {telegram_id}\n\n"
                    f"Please review and approve this registration."
                )

                for manager in managers:
                    try:
                        await bot.send_message(
                            chat_id=manager.telegram_id,
                            text=notification_message,
                            parse_mode="Markdown",
                        )
                        logger.info(
                            f"Notified manager {manager.name} about new registration"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify manager {manager.name}: {e}")

                await bot.session.close()

        except Exception as e:
            logger.error(f"Error notifying admins: {e}")


# Migration script to update existing records (run this once)
async def migrate_existing_users(db: AsyncSession):
    """Migrate existing users to have proper roles"""
    try:
        # Update users without roles to be dispatchers
        result = await db.execute(
            select(Dispatchers).where(Dispatchers.role.is_(None))
        )
        users_without_roles = list(result.scalars().all())

        for user in users_without_roles:
            user.role = "dispatcher"  # Default to dispatcher
            logger.info(f"Updated {user.name} to dispatcher role")

        await db.commit()
        logger.info(
            f"Migrated {len(users_without_roles)} users to have dispatcher role"
        )

    except Exception as e:
        logger.error(f"Error migrating users: {e}")
        await db.rollback()
