# app/db/repositories/driver_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.db.models import Driver, Company, TelegramChat
import logging

logger = logging.getLogger(__name__)


class DriverRepository:
    """
    Repository for Driver entity.
    Handles database operations for drivers.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_driver(
        self, name: str, company_id: int, chat_id: Optional[int] = None
    ) -> Driver:
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
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError(f"Company with ID {company_id} does not exist")

            # Ensure chat exists if provided
            if chat_id:
                chat = (
                    self.db.query(TelegramChat)
                    .filter(TelegramChat.id == chat_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Telegram chat with ID {chat_id} does not exist")

            # Generate a new driver ID (in a real system, this might follow a specific pattern)
            # For this example, we'll use a simple incremental ID
            last_driver = self.db.query(Driver).order_by(Driver.id.desc()).first()
            new_id = (last_driver.id + 1) if last_driver else 1

            driver = Driver(
                id=new_id, name=name, company_id=company_id, chat_id=chat_id
            )

            self.db.add(driver)
            self.db.commit()
            self.db.refresh(driver)

            return driver

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating driver: {str(e)}")
            raise

    def get_driver_by_id(self, driver_id: int) -> Optional[Driver]:
        """
        Get a driver by ID.

        Args:
            driver_id (int): ID of the driver to find

        Returns:
            Optional[Driver]: Driver if found, None otherwise
        """
        return self.db.query(Driver).filter(Driver.id == driver_id).first()

    def get_driver_by_name(self, name: str) -> Optional[Driver]:
        """
        Get a driver by name.

        Args:
            name (str): Name of the driver to find

        Returns:
            Optional[Driver]: Driver if found, None otherwise
        """
        return self.db.query(Driver).filter(Driver.name == name).first()

    def get_drivers_by_company(self, company_id: int) -> List[Driver]:
        """
        Get all drivers for a company.

        Args:
            company_id (int): ID of the company to get drivers for

        Returns:
            List[Driver]: List of drivers for the company
        """
        return self.db.query(Driver).filter(Driver.company_id == company_id).all()

    def get_drivers(self, skip: int = 0, limit: int = 100) -> List[Driver]:
        """
        Get a list of drivers with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Driver]: List of drivers
        """
        return self.db.query(Driver).offset(skip).limit(limit).all()

    def update_driver(
        self,
        driver_id: int,
        name: Optional[str] = None,
        company_id: Optional[int] = None,
        chat_id: Optional[int] = None,
    ) -> Optional[Driver]:
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
            driver = self.db.query(Driver).filter(Driver.id == driver_id).first()
            if not driver:
                return None

            if name is not None:
                driver.name = name

            if company_id is not None:
                # Ensure company exists
                company = (
                    self.db.query(Company).filter(Company.id == company_id).first()
                )
                if not company:
                    raise ValueError(f"Company with ID {company_id} does not exist")
                driver.company_id = company_id

            if chat_id is not None:
                # Ensure chat exists if provided
                if chat_id > 0:
                    chat = (
                        self.db.query(TelegramChat)
                        .filter(TelegramChat.id == chat_id)
                        .first()
                    )
                    if not chat:
                        raise ValueError(
                            f"Telegram chat with ID {chat_id} does not exist"
                        )
                driver.chat_id = chat_id

            self.db.commit()
            self.db.refresh(driver)

            return driver

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating driver: {str(e)}")
            raise

    def delete_driver(self, driver_id: int) -> bool:
        """
        Delete a driver.

        Args:
            driver_id (int): ID of the driver to delete

        Returns:
            bool: True if the driver was deleted, False otherwise
        """
        try:
            driver = self.db.query(Driver).filter(Driver.id == driver_id).first()
            if not driver:
                return False

            self.db.delete(driver)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting driver: {str(e)}")
            raise
