# app/db/repositories/driver_repository.py
import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, Driver, TelegramChat

logger = logging.getLogger(__name__)


class DriverRepository:
    """
    Repository for Driver entity.
    Handles database operations for drivers.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_driver(self, name: str, company_id: int, chat_id: int | None = None) -> Driver:
        """
        Create a new driver.

        Args:
            name (str): Driver name
            company_id (int): ID of the company the driver belongs to
            chat_id (int, optional): ID of the driver's Telegram chat

        Returns:
            Driver: Created driver instance
        """
        try:
            # Ensure company exists
            result = await self.db.execute(select(Company).where(Company.id == company_id))
            company = result.scalar_one_or_none()
            if not company:
                raise ValueError(f"Company with ID {company_id} does not exist")

            # Ensure chat exists if provided
            if chat_id:
                result = await self.db.execute(
                    select(TelegramChat).where(TelegramChat.id == chat_id)
                )
                chat = result.scalar_one_or_none()
                if not chat:
                    raise ValueError(f"Telegram chat with ID {chat_id} does not exist")

            # Generate a new driver ID (in a real system, this might follow a specific pattern)
            # For this example, we'll use a simple incremental ID
            result = await self.db.execute(select(Driver).order_by(Driver.id.desc()).limit(1))
            last_driver = result.scalar_one_or_none()
            new_id = (last_driver.id + 1) if last_driver else 1

            driver = Driver(id=new_id, name=name, company_id=company_id, chat_id=chat_id)

            self.db.add(driver)
            await self.db.commit()
            await self.db.refresh(driver)

            return driver

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating driver: {e!s}")
            raise

    async def get_driver_by_id(self, driver_id: int) -> Driver | None:
        """
        Get a driver by ID.

        Args:
            driver_id (int): ID of the driver to find

        Returns:
            Optional[Driver]: Driver if found, None otherwise
        """
        result = await self.db.execute(select(Driver).where(Driver.id == driver_id))
        return result.scalar_one_or_none()

    async def get_driver_by_name(self, name: str) -> Driver | None:
        """
        Get a driver by name.

        Args:
            name (str): Name of the driver to find

        Returns:
            Optional[Driver]: Driver if found, None otherwise
        """
        result = await self.db.execute(select(Driver).where(Driver.name == name))
        return result.scalar_one_or_none()

    async def get_drivers_by_company(self, company_id: int) -> list[Driver]:
        """
        Get all drivers for a company.

        Args:
            company_id (int): ID of the company to get drivers for

        Returns:
            List[Driver]: List of drivers for the company
        """
        result = await self.db.execute(select(Driver).where(Driver.company_id == company_id))
        return list(result.scalars().all())

    async def get_drivers(self, skip: int = 0, limit: int = 100) -> list[Driver]:
        """
        Get a list of drivers with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Driver]: List of drivers
        """
        result = await self.db.execute(select(Driver).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update_driver(
        self,
        driver_id: int,
        name: str | None = None,
        company_id: int | None = None,
        chat_id: int | None = None,
    ) -> Driver | None:
        """
        Update a driver's information.

        Args:
            driver_id (int): ID of the driver to update
            name (str, optional): New name for the driver
            company_id (int, optional): New company ID for the driver
            chat_id (int, optional): New chat ID for the driver

        Returns:
            Optional[Driver]: Updated driver if found, None otherwise
        """
        try:
            result = await self.db.execute(select(Driver).where(Driver.id == driver_id))
            driver = result.scalar_one_or_none()
            if not driver:
                return None

            if name is not None:
                driver.name = name

            if company_id is not None:
                # Ensure company exists
                result = await self.db.execute(select(Company).where(Company.id == company_id))
                company = result.scalar_one_or_none()
                if not company:
                    raise ValueError(f"Company with ID {company_id} does not exist")
                driver.company_id = company_id

            if chat_id is not None:
                # Ensure chat exists if provided
                if chat_id > 0:
                    result = await self.db.execute(
                        select(TelegramChat).where(TelegramChat.id == chat_id)
                    )
                    chat = result.scalar_one_or_none()
                    if not chat:
                        raise ValueError(f"Telegram chat with ID {chat_id} does not exist")
                driver.chat_id = chat_id

            await self.db.commit()
            await self.db.refresh(driver)

            return driver

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating driver: {e!s}")
            raise

    async def delete_driver(self, driver_id: int) -> bool:
        """
        Delete a driver.

        Args:
            driver_id (int): ID of the driver to delete

        Returns:
            bool: True if the driver was deleted, False otherwise
        """
        try:
            result = await self.db.execute(select(Driver).where(Driver.id == driver_id))
            driver = result.scalar_one_or_none()
            if not driver:
                return False

            await self.db.delete(driver)
            await self.db.commit()

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting driver: {e!s}")
            raise
