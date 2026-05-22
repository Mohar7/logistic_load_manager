# app/bot/services/load_service.py - Updated for full cross-company access
import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Company, Driver, Leg, Load

logger = logging.getLogger(__name__)


class LoadBotService:
    """Service for managing loads in the bot - Full cross-company access for dispatchers"""

    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    async def get_loads_by_dispatcher(self, dispatcher_id: int) -> list[Load]:
        """Get ALL loads in the system - dispatchers can now see everything"""
        try:
            # Dispatchers can now see ALL loads, not just their assigned ones
            result = await self.db.execute(
                select(Load)
                .options(selectinload(Load.company), selectinload(Load.driver))
                .order_by(Load.id.desc())
                .limit(100)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting loads for dispatcher: {e}")
            return []

    async def get_all_loads(self, limit: int = 100) -> list[Load]:
        """Get all loads in the system"""
        try:
            result = await self.db.execute(
                select(Load)
                .options(selectinload(Load.company), selectinload(Load.driver))
                .order_by(Load.id.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting all loads: {e}")
            return []

    async def get_unassigned_loads(self, limit: int = 50) -> list[Load]:
        """Get all unassigned loads across all companies"""
        try:
            result = await self.db.execute(
                select(Load)
                .options(selectinload(Load.company))
                .where(Load.driver_id.is_(None))
                .order_by(Load.id.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting unassigned loads: {e}")
            return []

    async def get_loads_by_company(self, company_id: int) -> list[Load]:
        """Get loads by specific company"""
        try:
            result = await self.db.execute(
                select(Load)
                .options(selectinload(Load.company), selectinload(Load.driver))
                .where(Load.company_id == company_id)
                .order_by(Load.id.desc())
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting loads for company: {e}")
            return []

    async def get_load_details(self, load_id: int) -> dict | None:
        """Get detailed load information"""
        try:
            load = (
                await self.db.execute(
                    select(Load)
                    .options(
                        selectinload(Load.company),
                        selectinload(Load.driver).selectinload(Driver.company),
                    )
                    .where(Load.id == load_id)
                )
            ).scalar_one_or_none()
            if not load:
                return None

            legs_result = await self.db.execute(
                select(Leg)
                .options(
                    selectinload(Leg.pickup_facility),
                    selectinload(Leg.dropoff_facility),
                )
                .where(Leg.load_id == load_id)
            )
            legs = list(legs_result.scalars().all())

            return {"load": load, "legs": legs}
        except SQLAlchemyError as e:
            logger.error(f"Error getting load details: {e}")
            return None

    async def get_available_drivers(self) -> list[Driver]:
        """Get ALL drivers across all companies - UPDATED for cross-company access"""
        try:
            # Return ALL drivers from ALL companies
            result = await self.db.execute(
                select(Driver)
                .options(selectinload(Driver.company))
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .order_by(Company.name.nullsfirst(), Driver.name)
            )
            drivers = list(result.scalars().all())

            logger.info(
                f"Retrieved {len(drivers)} drivers from all companies for cross-company access"
            )
            return drivers
        except SQLAlchemyError as e:
            logger.error(f"Error getting available drivers: {e}")
            return []

    async def get_drivers_by_company(self, company_id: int) -> list[Driver]:
        """Get drivers from specific company"""
        try:
            result = await self.db.execute(
                select(Driver)
                .options(selectinload(Driver.company))
                .where(Driver.company_id == company_id)
                .order_by(Driver.name)
            )
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error getting drivers for company: {e}")
            return []

    async def get_all_companies(self) -> list[Company]:
        """Get all companies - accessible to all dispatchers"""
        try:
            result = await self.db.execute(select(Company).order_by(Company.name))
            companies = list(result.scalars().all())
            logger.info(f"Retrieved {len(companies)} companies for cross-company access")
            return companies
        except SQLAlchemyError as e:
            logger.error(f"Error getting companies: {e}")
            return []

    async def get_drivers_with_company_info(self) -> list[dict[str, Any]]:
        """Get all drivers with their company information for cross-company display"""
        try:
            result = await self.db.execute(
                select(Driver)
                .options(selectinload(Driver.company))
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .order_by(Company.name.nullsfirst(), Driver.name)
            )
            drivers = list(result.scalars().all())

            result_list = []
            for driver in drivers:
                result_list.append(
                    {
                        "driver": driver,
                        "company_name": driver.company.name if driver.company else "No Company",
                        "company_id": driver.company_id,
                        "has_telegram": driver.chat_id is not None,
                    }
                )

            logger.info(
                f"Retrieved {len(result_list)} drivers with company info for cross-company access"
            )
            return result_list
        except SQLAlchemyError as e:
            logger.error(f"Error getting drivers with company info: {e}")
            return []

    async def get_drivers_by_telegram_availability(self) -> dict[str, list[Driver]]:
        """Get drivers grouped by Telegram availability"""
        try:
            all_drivers = await self.get_available_drivers()

            result = {"with_telegram": [], "without_telegram": []}

            for driver in all_drivers:
                if driver.chat_id:
                    result["with_telegram"].append(driver)
                else:
                    result["without_telegram"].append(driver)

            logger.info(
                f"Grouped drivers: {len(result['with_telegram'])} with Telegram, {len(result['without_telegram'])} without"
            )
            return result
        except Exception as e:
            logger.error(f"Error grouping drivers by Telegram availability: {e}")
            return {"with_telegram": [], "without_telegram": []}

    async def get_company_statistics(self) -> list[dict[str, Any]]:
        """Get statistics for each company"""
        try:
            companies = await self.get_all_companies()
            stats = []

            for company in companies:
                company_drivers = await self.get_drivers_by_company(company.id)
                company_loads = await self.get_loads_by_company(company.id)

                drivers_with_telegram = sum(1 for d in company_drivers if d.chat_id)
                unassigned_loads = sum(1 for l in company_loads if not l.driver_id)

                stats.append(
                    {
                        "company": company,
                        "total_drivers": len(company_drivers),
                        "drivers_with_telegram": drivers_with_telegram,
                        "total_loads": len(company_loads),
                        "unassigned_loads": unassigned_loads,
                    }
                )

            return stats
        except Exception as e:
            logger.error(f"Error getting company statistics: {e}")
            return []

    async def assign_driver_to_load(self, load_id: int, driver_id: int) -> bool:
        """Assign any driver to any load - cross-company assignment"""
        try:
            load = (
                await self.db.execute(select(Load).where(Load.id == load_id))
            ).scalar_one_or_none()
            driver = (
                await self.db.execute(
                    select(Driver)
                    .options(selectinload(Driver.company))
                    .where(Driver.id == driver_id)
                )
            ).scalar_one_or_none()

            if not load or not driver:
                return False

            load.driver_id = driver_id
            load.assigned_driver = driver.name
            await self.db.commit()

            logger.info(
                f"Cross-company assignment: Driver {driver.name} from {driver.company.name if driver.company else 'No Company'} assigned to load {load.trip_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error assigning driver to load: {e}")
            await self.db.rollback()
            return False

    async def get_load_assignment_suggestions(self, load_id: int) -> list[dict[str, Any]]:
        """Get driver suggestions for a load, including cross-company options"""
        try:
            load = (
                await self.db.execute(select(Load).where(Load.id == load_id))
            ).scalar_one_or_none()
            if not load:
                return []

            # Get all available drivers (not currently assigned to active loads)
            busy_drivers_subq = (
                select(Load.driver_id)
                .where(Load.driver_id.isnot(None))
                .where(Load.end_time > load.start_time)  # Overlapping loads
            )
            result = await self.db.execute(
                select(Driver)
                .options(selectinload(Driver.company))
                .where(Driver.id.notin_(busy_drivers_subq))
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .order_by(Company.name.nullsfirst(), Driver.name)
            )
            available_drivers = list(result.scalars().all())

            suggestions = []
            for driver in available_drivers:
                suggestions.append(
                    {
                        "driver": driver,
                        "company_name": driver.company.name if driver.company else "No Company",
                        "has_telegram": driver.chat_id is not None,
                        "cross_company": driver.company_id != load.company_id
                        if load.company_id
                        else False,
                    }
                )

            return suggestions
        except Exception as e:
            logger.error(f"Error getting load assignment suggestions: {e}")
            return []

    async def get_system_wide_statistics(self) -> dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            total_loads = (
                await self.db.execute(select(func.count()).select_from(Load))
            ).scalar_one()
            assigned_loads = (
                await self.db.execute(
                    select(func.count()).select_from(Load).where(Load.driver_id.isnot(None))
                )
            ).scalar_one()
            unassigned_loads = (
                await self.db.execute(
                    select(func.count()).select_from(Load).where(Load.driver_id.is_(None))
                )
            ).scalar_one()
            total_drivers = (
                await self.db.execute(select(func.count()).select_from(Driver))
            ).scalar_one()
            telegram_drivers = (
                await self.db.execute(
                    select(func.count()).select_from(Driver).where(Driver.chat_id.isnot(None))
                )
            ).scalar_one()
            total_companies = (
                await self.db.execute(select(func.count()).select_from(Company))
            ).scalar_one()
            active_companies = (
                await self.db.execute(
                    select(func.count(func.distinct(Company.id)))
                    .select_from(Company)
                    .join(Driver, Driver.company_id == Company.id)
                )
            ).scalar_one()

            stats = {
                "loads": {
                    "total": total_loads,
                    "assigned": assigned_loads,
                    "unassigned": unassigned_loads,
                },
                "drivers": {
                    "total": total_drivers,
                    "telegram": telegram_drivers,
                },
                "companies": {
                    "total": total_companies,
                    "active": active_companies,
                },
                "cross_company": {
                    "enabled": True,
                    "assignments": 0,  # Could be calculated if tracking cross-company assignments
                },
            }

            logger.info("Generated system-wide statistics")
            return stats
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}
