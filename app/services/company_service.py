# app/services/company_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.repositories.company_repository import CompanyRepository
from app.db.repositories.driver_repository import DriverRepository
from app.db.models import Company
import logging

logger = logging.getLogger(__name__)


class CompanyService:
    """
    Service for managing companies.
    """

    def __init__(self, db: Session):
        self.db = db
        self.company_repository = CompanyRepository(db)
        self.driver_repository = DriverRepository(db)

    def create_company(
        self, name: str, usdot: int, carrier_identifier: str, mc: int
    ) -> Dict[str, Any]:
        """
        Create a new company.

        Args:
            name (str): Company name
            usdot (int): USDOT number
            carrier_identifier (str): Carrier identifier
            mc (int): MC number

        Returns:
            Dict[str, Any]: Dictionary with created company information
        """
        try:
            # Check if company with USDOT already exists
            existing_company = self.company_repository.get_company_by_usdot(usdot)
            if existing_company:
                raise ValueError(f"Company with USDOT {usdot} already exists")

            # Create the company
            company = self.company_repository.create_company(
                name, usdot, carrier_identifier, mc
            )

            return {"company": company, "drivers_count": 0}

        except Exception as e:
            logger.error(f"Error in create_company: {str(e)}")
            raise

    def get_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a company by ID with driver count.

        Args:
            company_id (int): ID of the company to retrieve

        Returns:
            Optional[Dict[str, Any]]: Dictionary with company information and driver count, or None if not found
        """
        company = self.company_repository.get_company_by_id(company_id)
        if not company:
            return None

        drivers = self.driver_repository.get_drivers_by_company(company_id)

        return {"company": company, "drivers_count": len(drivers)}

    def get_companies(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all companies with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Dict[str, Any]]: List of companies with their driver counts
        """
        companies = self.company_repository.get_companies(skip, limit)
        result = []

        for company in companies:
            drivers = self.driver_repository.get_drivers_by_company(company.id)
            result.append({"company": company, "drivers_count": len(drivers)})

        return result

    def update_company(
        self,
        company_id: int,
        name: Optional[str] = None,
        usdot: Optional[int] = None,
        carrier_identifier: Optional[str] = None,
        mc: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update a company's information.

        Args:
            company_id (int): ID of the company to update
            name (str, optional): New name for the company
            usdot (int, optional): New USDOT number
            carrier_identifier (str, optional): New carrier identifier
            mc (int, optional): New MC number

        Returns:
            Optional[Dict[str, Any]]: Updated company information if found, None otherwise
        """
        try:
            # Check if USDOT is already used by another company
            if usdot is not None:
                existing_company = self.company_repository.get_company_by_usdot(usdot)
                if existing_company and existing_company.id != company_id:
                    raise ValueError(f"Company with USDOT {usdot} already exists")

            company = self.company_repository.update_company(
                company_id, name, usdot, carrier_identifier, mc
            )
            if not company:
                return None

            drivers = self.driver_repository.get_drivers_by_company(company_id)

            return {"company": company, "drivers_count": len(drivers)}

        except Exception as e:
            logger.error(f"Error in update_company: {str(e)}")
            raise

    def delete_company(self, company_id: int) -> bool:
        """
        Delete a company.

        Args:
            company_id (int): ID of the company to delete

        Returns:
            bool: True if the company was deleted, False otherwise
        """
        # Check if company has drivers
        drivers = self.driver_repository.get_drivers_by_company(company_id)
        if drivers:
            raise ValueError(
                f"Cannot delete company with ID {company_id} because it has {len(drivers)} drivers associated with it"
            )

        return self.company_repository.delete_company(company_id)
