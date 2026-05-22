# app/services/driver_service.py
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Driver
from app.db.repositories.company_repository import CompanyRepository
from app.db.repositories.driver_repository import DriverRepository

logger = logging.getLogger(__name__)


class DriverService:
    """
    Service for managing drivers.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.driver_repository = DriverRepository(db)
        self.company_repository = CompanyRepository(db)

    async def create_driver(
        self, name: str, company_id: int, chat_id: int | None = None
    ) -> dict[str, Any]:
        """
        Create a new driver.

        Args:
            name (str): Driver name
            company_id (int): ID of the company the driver belongs to
            chat_id (int, optional): ID of the driver's Telegram chat

        Returns:
            Dict[str, Any]: Dictionary with created driver information
        """
        try:
            # Check if company exists
            company = await self.company_repository.get_company_by_id(company_id)
            if not company:
                raise ValueError(f"Company with ID {company_id} does not exist")

            # Create the driver
            driver = await self.driver_repository.create_driver(name, company_id, chat_id)

            return {"driver": driver, "company": company}

        except Exception as e:
            logger.error(f"Error in create_driver: {e!s}")
            raise

    async def get_driver_by_id(self, driver_id: int) -> dict[str, Any] | None:
        """
        Get a driver by ID with company information.

        Args:
            driver_id (int): ID of the driver to retrieve

        Returns:
            Optional[Dict[str, Any]]: Dictionary with driver and company information, or None if not found
        """
        driver = await self.driver_repository.get_driver_by_id(driver_id)
        if not driver:
            return None

        company = await self.company_repository.get_company_by_id(driver.company_id)

        return {"driver": driver, "company": company}

    async def get_driver_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get a driver by name with company information.

        Args:
            name (str): Name of the driver to retrieve

        Returns:
            Optional[Dict[str, Any]]: Dictionary with driver and company information, or None if not found
        """
        driver = await self.driver_repository.get_driver_by_name(name)
        if not driver:
            return None

        company = await self.company_repository.get_company_by_id(driver.company_id)

        return {"driver": driver, "company": company}

    async def get_drivers(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get all drivers with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Dict[str, Any]]: List of drivers with their company information
        """
        drivers = await self.driver_repository.get_drivers(skip, limit)
        result = []

        for driver in drivers:
            company = await self.company_repository.get_company_by_id(driver.company_id)
            result.append({"driver": driver, "company": company})

        return result

    async def get_drivers_by_company(self, company_id: int) -> list[Driver]:
        """
        Get all drivers for a specific company.

        Args:
            company_id (int): ID of the company to get drivers for

        Returns:
            List[Driver]: List of drivers for the company
        """
        return await self.driver_repository.get_drivers_by_company(company_id)

    async def update_driver(
        self,
        driver_id: int,
        name: str | None = None,
        company_id: int | None = None,
        chat_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Update a driver's information.

        Args:
            driver_id (int): ID of the driver to update
            name (str, optional): New name for the driver
            company_id (int, optional): New company ID for the driver
            chat_id (int, optional): New chat ID for the driver

        Returns:
            Optional[Dict[str, Any]]: Updated driver information if found, None otherwise
        """
        try:
            # Check if company exists if provided
            if company_id is not None:
                company = await self.company_repository.get_company_by_id(company_id)
                if not company:
                    raise ValueError(f"Company with ID {company_id} does not exist")

            driver = await self.driver_repository.update_driver(
                driver_id, name, company_id, chat_id
            )
            if not driver:
                return None

            company = await self.company_repository.get_company_by_id(driver.company_id)

            return {"driver": driver, "company": company}

        except Exception as e:
            logger.error(f"Error in update_driver: {e!s}")
            raise

    async def delete_driver(self, driver_id: int) -> bool:
        """
        Delete a driver.

        Args:
            driver_id (int): ID of the driver to delete

        Returns:
            bool: True if the driver was deleted, False otherwise
        """
        return await self.driver_repository.delete_driver(driver_id)
