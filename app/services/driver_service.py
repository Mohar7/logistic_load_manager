# app/services/driver_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.repositories.driver_repository import DriverRepository
from app.db.repositories.company_repository import CompanyRepository
from app.db.models import Driver
import logging

logger = logging.getLogger(__name__)


class DriverService:
    """
    Service for managing drivers.
    """

    def __init__(self, db: Session):
        self.db = db
        self.driver_repository = DriverRepository(db)
        self.company_repository = CompanyRepository(db)

    def create_driver(
        self, name: str, company_id: int, chat_id: Optional[int] = None
    ) -> Dict[str, Any]:
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
            company = self.company_repository.get_company_by_id(company_id)
            if not company:
                raise ValueError(f"Company with ID {company_id} does not exist")

            # Create the driver
            driver = self.driver_repository.create_driver(name, company_id, chat_id)

            return {"driver": driver, "company": company}

        except Exception as e:
            logger.error(f"Error in create_driver: {str(e)}")
            raise

    def get_driver_by_id(self, driver_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a driver by ID with company information.

        Args:
            driver_id (int): ID of the driver to retrieve

        Returns:
            Optional[Dict[str, Any]]: Dictionary with driver and company information, or None if not found
        """
        driver = self.driver_repository.get_driver_by_id(driver_id)
        if not driver:
            return None

        company = self.company_repository.get_company_by_id(driver.company_id)

        return {"driver": driver, "company": company}

    def get_driver_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a driver by name with company information.

        Args:
            name (str): Name of the driver to retrieve

        Returns:
            Optional[Dict[str, Any]]: Dictionary with driver and company information, or None if not found
        """
        driver = self.driver_repository.get_driver_by_name(name)
        if not driver:
            return None

        company = self.company_repository.get_company_by_id(driver.company_id)

        return {"driver": driver, "company": company}

    def get_drivers(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all drivers with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Dict[str, Any]]: List of drivers with their company information
        """
        drivers = self.driver_repository.get_drivers(skip, limit)
        result = []

        for driver in drivers:
            company = self.company_repository.get_company_by_id(driver.company_id)
            result.append({"driver": driver, "company": company})

        return result

    def get_drivers_by_company(self, company_id: int) -> List[Driver]:
        """
        Get all drivers for a specific company.

        Args:
            company_id (int): ID of the company to get drivers for

        Returns:
            List[Driver]: List of drivers for the company
        """
        return self.driver_repository.get_drivers_by_company(company_id)

    def update_driver(
        self,
        driver_id: int,
        name: Optional[str] = None,
        company_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
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
                company = self.company_repository.get_company_by_id(company_id)
                if not company:
                    raise ValueError(f"Company with ID {company_id} does not exist")

            driver = self.driver_repository.update_driver(
                driver_id, name, company_id, chat_id
            )
            if not driver:
                return None

            company = self.company_repository.get_company_by_id(driver.company_id)

            return {"driver": driver, "company": company}

        except Exception as e:
            logger.error(f"Error in update_driver: {str(e)}")
            raise

    def delete_driver(self, driver_id: int) -> bool:
        """
        Delete a driver.

        Args:
            driver_id (int): ID of the driver to delete

        Returns:
            bool: True if the driver was deleted, False otherwise
        """
        return self.driver_repository.delete_driver(driver_id)
