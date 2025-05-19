# app/db/repositories/company_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.db.models import Company
import logging

logger = logging.getLogger(__name__)


class CompanyRepository:
    """
    Repository for Company entity.
    Handles database operations for companies.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_company(
        self, name: str, usdot: int, carrier_identifier: str, mc: int
    ) -> Company:
        """
        Create a new company.

        Args:
            name (str): Company name
            usdot (int): USDOT number
            carrier_identifier (str): Carrier identifier
            mc (int): MC number

        Returns:
            Company: Created company instance
        """
        try:
            company = Company(
                name=name, usdot=usdot, carrier_identifier=carrier_identifier, mc=mc
            )

            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)

            return company

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating company: {str(e)}")
            raise

    def get_company_by_id(self, company_id: int) -> Optional[Company]:
        """
        Get a company by ID.

        Args:
            company_id (int): ID of the company to find

        Returns:
            Optional[Company]: Company if found, None otherwise
        """
        return self.db.query(Company).filter(Company.id == company_id).first()

    def get_company_by_name(self, name: str) -> Optional[Company]:
        """
        Get a company by name.

        Args:
            name (str): Name of the company to find

        Returns:
            Optional[Company]: Company if found, None otherwise
        """
        return self.db.query(Company).filter(Company.name == name).first()

    def get_company_by_usdot(self, usdot: int) -> Optional[Company]:
        """
        Get a company by USDOT number.

        Args:
            usdot (int): USDOT of the company to find

        Returns:
            Optional[Company]: Company if found, None otherwise
        """
        return self.db.query(Company).filter(Company.usdot == usdot).first()

    def get_companies(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """
        Get a list of companies with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Company]: List of companies
        """
        return self.db.query(Company).offset(skip).limit(limit).all()

    def update_company(
        self,
        company_id: int,
        name: Optional[str] = None,
        usdot: Optional[int] = None,
        carrier_identifier: Optional[str] = None,
        mc: Optional[int] = None,
    ) -> Optional[Company]:
        """
        Update a company's information.

        Args:
            company_id (int): ID of the company to update
            name (str, optional): New name for the company
            usdot (int, optional): New USDOT number
            carrier_identifier (str, optional): New carrier identifier
            mc (int, optional): New MC number

        Returns:
            Optional[Company]: Updated company if found, None otherwise
        """
        try:
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return None

            if name is not None:
                company.name = name

            if usdot is not None:
                company.usdot = usdot

            if carrier_identifier is not None:
                company.carrier_identifier = carrier_identifier

            if mc is not None:
                company.mc = mc

            self.db.commit()
            self.db.refresh(company)

            return company

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating company: {str(e)}")
            raise

    def delete_company(self, company_id: int) -> bool:
        """
        Delete a company.

        Args:
            company_id (int): ID of the company to delete

        Returns:
            bool: True if the company was deleted, False otherwise
        """
        try:
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return False

            self.db.delete(company)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting company: {str(e)}")
            raise
