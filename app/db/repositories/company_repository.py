# app/db/repositories/company_repository.py
import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company

logger = logging.getLogger(__name__)


class CompanyRepository:
    """
    Repository for Company entity.
    Handles database operations for companies.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_company(
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
            await self.db.commit()
            await self.db.refresh(company)

            return company

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error creating company: {e!s}")
            raise

    async def get_company_by_id(self, company_id: int) -> Company | None:
        """
        Get a company by ID.

        Args:
            company_id (int): ID of the company to find

        Returns:
            Optional[Company]: Company if found, None otherwise
        """
        result = await self.db.execute(select(Company).where(Company.id == company_id))
        return result.scalar_one_or_none()

    async def get_company_by_name(self, name: str) -> Company | None:
        """
        Get a company by name.

        Args:
            name (str): Name of the company to find

        Returns:
            Optional[Company]: Company if found, None otherwise
        """
        result = await self.db.execute(select(Company).where(Company.name == name))
        return result.scalar_one_or_none()

    async def get_company_by_usdot(self, usdot: int) -> Company | None:
        """
        Get a company by USDOT number.

        Args:
            usdot (int): USDOT of the company to find

        Returns:
            Optional[Company]: Company if found, None otherwise
        """
        result = await self.db.execute(select(Company).where(Company.usdot == usdot))
        return result.scalar_one_or_none()

    async def get_companies(self, skip: int = 0, limit: int = 100) -> list[Company]:
        """
        Get a list of companies with pagination.

        Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[Company]: List of companies
        """
        result = await self.db.execute(select(Company).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update_company(
        self,
        company_id: int,
        name: str | None = None,
        usdot: int | None = None,
        carrier_identifier: str | None = None,
        mc: int | None = None,
    ) -> Company | None:
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
            result = await self.db.execute(
                select(Company).where(Company.id == company_id)
            )
            company = result.scalar_one_or_none()
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

            await self.db.commit()
            await self.db.refresh(company)

            return company

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating company: {e!s}")
            raise

    async def delete_company(self, company_id: int) -> bool:
        """
        Delete a company.

        Args:
            company_id (int): ID of the company to delete

        Returns:
            bool: True if the company was deleted, False otherwise
        """
        try:
            result = await self.db.execute(
                select(Company).where(Company.id == company_id)
            )
            company = result.scalar_one_or_none()
            if not company:
                return False

            await self.db.delete(company)
            await self.db.commit()

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting company: {e!s}")
            raise
