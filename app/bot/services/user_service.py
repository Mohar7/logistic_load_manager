# app/bot/services/user_service.py - Updated for cross-company access
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from app.db.models import Dispatchers, Company, TelegramChat
import logging

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing bot users and registration - Updated"""

    def __init__(self, db: Session):
        self.db = db

    async def create_user_registration(
        self, telegram_id: int, username: str, name: str, role: str
    ) -> bool:
        """Create a user registration request"""
        try:
            # Check if user already exists
            existing_user = (
                self.db.query(Dispatchers)
                .filter(Dispatchers.telegram_id == telegram_id)
                .first()
            )

            if existing_user:
                return False

            # Create user with role - dispatchers no longer need company assignment
            user = Dispatchers(name=name, telegram_id=telegram_id, role=role)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            logger.info(
                f"Created user registration: {name} ({role}) - Telegram ID: {telegram_id}"
            )
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error creating user registration: {e}")
            self.db.rollback()
            return False

    async def complete_dispatcher_registration(
        self, telegram_id: int, company_id: int, name: str
    ) -> bool:
        """Complete dispatcher registration - company is now optional/informational"""
        try:
            # Check if dispatcher exists
            dispatcher = (
                self.db.query(Dispatchers)
                .filter(Dispatchers.telegram_id == telegram_id)
                .first()
            )

            if not dispatcher:
                # Create new dispatcher - they can manage all companies
                dispatcher = Dispatchers(
                    name=name, telegram_id=telegram_id, role="dispatcher"
                )
                self.db.add(dispatcher)
                self.db.commit()
                self.db.refresh(dispatcher)

            logger.info(
                f"Completed dispatcher registration: {name} - Can manage all companies"
            )
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error completing dispatcher registration: {e}")
            self.db.rollback()
            return False

    async def approve_manager(self, telegram_id: int) -> bool:
        """Approve a manager registration"""
        try:
            user = (
                self.db.query(Dispatchers)
                .filter(
                    Dispatchers.telegram_id == telegram_id,
                    Dispatchers.role == "manager",
                )
                .first()
            )

            if not user:
                return False

            # You could add a status column to track approval
            # For now, we'll just log the approval
            logger.info(f"Manager approved: {user.name} - Telegram ID: {telegram_id}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error approving manager: {e}")
            self.db.rollback()
            return False

    async def get_companies(self) -> List[Company]:
        """Get all available companies"""
        try:
            return self.db.query(Company).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting companies: {e}")
            return []

    async def get_user_by_telegram_id(
        self, telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get user information by Telegram ID"""
        try:
            # Check for user in Dispatchers table (now handles both dispatchers and managers)
            user = (
                self.db.query(Dispatchers)
                .filter(Dispatchers.telegram_id == telegram_id)
                .first()
            )

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

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all registered users"""
        try:
            users = self.db.query(Dispatchers).all()

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

    async def get_pending_managers(self) -> List[Dict[str, Any]]:
        """Get managers pending approval"""
        try:
            # You could add a status column and filter by status='pending'
            # For now, we'll just return all managers
            managers = (
                self.db.query(Dispatchers).filter(Dispatchers.role == "manager").all()
            )

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
            user = self.db.query(Dispatchers).filter(Dispatchers.id == user_id).first()
            if not user:
                return False

            self.db.delete(user)
            self.db.commit()

            logger.info(f"Deleted user: {user.name} ({user.role})")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error deleting user: {e}")
            self.db.rollback()
            return False

    async def update_user_role(self, telegram_id: int, new_role: str) -> bool:
        """Update a user's role"""
        try:
            user = (
                self.db.query(Dispatchers)
                .filter(Dispatchers.telegram_id == telegram_id)
                .first()
            )

            if not user:
                return False

            old_role = user.role
            user.role = new_role
            self.db.commit()

            logger.info(f"Updated user role: {user.name} from {old_role} to {new_role}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error updating user role: {e}")
            self.db.rollback()
            return False

    async def notify_admins_new_registration(
        self, telegram_id: int, name: str, role: str = "manager"
    ):
        """Notify administrators about new registration"""
        try:
            # Get all existing managers to notify them
            managers = (
                self.db.query(Dispatchers).filter(Dispatchers.role == "manager").all()
            )

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
async def migrate_existing_users(db: Session):
    """Migrate existing users to have proper roles"""
    try:
        # Update users without roles to be dispatchers
        users_without_roles = (
            db.query(Dispatchers).filter(Dispatchers.role.is_(None)).all()
        )

        for user in users_without_roles:
            user.role = "dispatcher"  # Default to dispatcher
            logger.info(f"Updated {user.name} to dispatcher role")

        db.commit()
        logger.info(
            f"Migrated {len(users_without_roles)} users to have dispatcher role"
        )

    except Exception as e:
        logger.error(f"Error migrating users: {e}")
        db.rollback()
