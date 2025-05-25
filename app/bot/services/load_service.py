# app/bot/services/load_service.py - Updated for full cross-company access
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from app.db.models import Load, Leg, Driver, Company, Dispatchers
import logging

logger = logging.getLogger(__name__)


class LoadBotService:
    """Service for managing loads in the bot - Full cross-company access for dispatchers"""

    def __init__(self, db: Session):
        self.db = db

    async def get_loads_by_dispatcher(self, dispatcher_id: int) -> List[Load]:
        """Get ALL loads in the system - dispatchers can now see everything"""
        try:
            # Dispatchers can now see ALL loads, not just their assigned ones
            return (
                self.db.query(Load)
                .order_by(Load.id.desc())
                .limit(100)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting loads for dispatcher: {e}")
            return []

    async def get_all_loads(self, limit: int = 100) -> List[Load]:
        """Get all loads in the system"""
        try:
            return self.db.query(Load).order_by(Load.id.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all loads: {e}")
            return []

    async def get_unassigned_loads(self, limit: int = 50) -> List[Load]:
        """Get all unassigned loads across all companies"""
        try:
            return (
                self.db.query(Load)
                .filter(Load.driver_id.is_(None))
                .order_by(Load.id.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting unassigned loads: {e}")
            return []

    async def get_loads_by_company(self, company_id: int) -> List[Load]:
        """Get loads by specific company"""
        try:
            return (
                self.db.query(Load)
                .filter(Load.company_id == company_id)
                .order_by(Load.id.desc())
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting loads for company: {e}")
            return []

    async def get_load_details(self, load_id: int) -> Optional[dict]:
        """Get detailed load information"""
        try:
            load = self.db.query(Load).filter(Load.id == load_id).first()
            if not load:
                return None

            legs = self.db.query(Leg).filter(Leg.load_id == load_id).all()

            return {"load": load, "legs": legs}
        except SQLAlchemyError as e:
            logger.error(f"Error getting load details: {e}")
            return None

    async def get_available_drivers(self) -> List[Driver]:
        """Get ALL drivers across all companies - UPDATED for cross-company access"""
        try:
            # Return ALL drivers from ALL companies
            drivers = (
                self.db.query(Driver)
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .order_by(Company.name.nullsfirst(), Driver.name)
                .all()
            )
            
            logger.info(f"Retrieved {len(drivers)} drivers from all companies for cross-company access")
            return drivers
        except SQLAlchemyError as e:
            logger.error(f"Error getting available drivers: {e}")
            return []

    async def get_drivers_by_company(self, company_id: int) -> List[Driver]:
        """Get drivers from specific company"""
        try:
            return (
                self.db.query(Driver)
                .filter(Driver.company_id == company_id)
                .order_by(Driver.name)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting drivers for company: {e}")
            return []

    async def get_all_companies(self) -> List[Company]:
        """Get all companies - accessible to all dispatchers"""
        try:
            companies = self.db.query(Company).order_by(Company.name).all()
            logger.info(f"Retrieved {len(companies)} companies for cross-company access")
            return companies
        except SQLAlchemyError as e:
            logger.error(f"Error getting companies: {e}")
            return []

    async def get_drivers_with_company_info(self) -> List[Dict[str, Any]]:
        """Get all drivers with their company information for cross-company display"""
        try:
            drivers = (
                self.db.query(Driver)
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .order_by(Company.name.nullsfirst(), Driver.name)
                .all()
            )
            
            result = []
            for driver in drivers:
                result.append({
                    "driver": driver,
                    "company_name": driver.company.name if driver.company else "No Company",
                    "company_id": driver.company_id,
                    "has_telegram": driver.chat_id is not None
                })
            
            logger.info(f"Retrieved {len(result)} drivers with company info for cross-company access")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting drivers with company info: {e}")
            return []

    async def get_drivers_by_telegram_availability(self) -> Dict[str, List[Driver]]:
        """Get drivers grouped by Telegram availability"""
        try:
            all_drivers = await self.get_available_drivers()
            
            result = {
                "with_telegram": [],
                "without_telegram": []
            }
            
            for driver in all_drivers:
                if driver.chat_id:
                    result["with_telegram"].append(driver)
                else:
                    result["without_telegram"].append(driver)
            
            logger.info(f"Grouped drivers: {len(result['with_telegram'])} with Telegram, {len(result['without_telegram'])} without")
            return result
        except Exception as e:
            logger.error(f"Error grouping drivers by Telegram availability: {e}")
            return {"with_telegram": [], "without_telegram": []}

    async def get_company_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for each company"""
        try:
            companies = await self.get_all_companies()
            stats = []
            
            for company in companies:
                company_drivers = await self.get_drivers_by_company(company.id)
                company_loads = await self.get_loads_by_company(company.id)
                
                drivers_with_telegram = sum(1 for d in company_drivers if d.chat_id)
                unassigned_loads = sum(1 for l in company_loads if not l.driver_id)
                
                stats.append({
                    "company": company,
                    "total_drivers": len(company_drivers),
                    "drivers_with_telegram": drivers_with_telegram,
                    "total_loads": len(company_loads),
                    "unassigned_loads": unassigned_loads
                })
            
            return stats
        except Exception as e:
            logger.error(f"Error getting company statistics: {e}")
            return []

    async def assign_driver_to_load(self, load_id: int, driver_id: int) -> bool:
        """Assign any driver to any load - cross-company assignment"""
        try:
            load = self.db.query(Load).filter(Load.id == load_id).first()
            driver = self.db.query(Driver).filter(Driver.id == driver_id).first()
            
            if not load or not driver:
                return False
            
            load.driver_id = driver_id
            load.assigned_driver = driver.name
            self.db.commit()
            
            logger.info(f"Cross-company assignment: Driver {driver.name} from {driver.company.name if driver.company else 'No Company'} assigned to load {load.trip_id}")
            return True
        except Exception as e:
            logger.error(f"Error assigning driver to load: {e}")
            self.db.rollback()
            return False

    async def get_drivers_with_company_info(self) -> List[Dict[str, Any]]:
        """Get all drivers with their company information for cross-company display"""
        try:
            drivers = (
                self.db.query(Driver)
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .order_by(Company.name.nullsfirst(), Driver.name)
                .all()
            )
            
            result = []
            for driver in drivers:
                result.append({
                    "driver": driver,
                    "company_name": driver.company.name if driver.company else "No Company",
                    "company_id": driver.company_id,
                    "has_telegram": driver.chat_id is not None
                })
            
            logger.info(f"Retrieved {len(result)} drivers with company info for cross-company access")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting drivers with company info: {e}")
            return []

    async def get_drivers_by_telegram_availability(self) -> Dict[str, List[Driver]]:
        """Get drivers grouped by Telegram availability"""
        try:
            all_drivers = await self.get_available_drivers()
            
            result = {
                "with_telegram": [],
                "without_telegram": []
            }
            
            for driver in all_drivers:
                if driver.chat_id:
                    result["with_telegram"].append(driver)
                else:
                    result["without_telegram"].append(driver)
            
            logger.info(f"Grouped drivers: {len(result['with_telegram'])} with Telegram, {len(result['without_telegram'])} without")
            return result
        except Exception as e:
            logger.error(f"Error grouping drivers by Telegram availability: {e}")
            return {"with_telegram": [], "without_telegram": []}

    async def get_company_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for each company"""
        try:
            companies = await self.get_all_companies()
            stats = []
            
            for company in companies:
                company_drivers = await self.get_drivers_by_company(company.id)
                company_loads = await self.get_loads_by_company(company.id)
                
                drivers_with_telegram = sum(1 for d in company_drivers if d.chat_id)
                unassigned_loads = sum(1 for l in company_loads if not l.driver_id)
                
                stats.append({
                    "company": company,
                    "total_drivers": len(company_drivers),
                    "drivers_with_telegram": drivers_with_telegram,
                    "total_loads": len(company_loads),
                    "unassigned_loads": unassigned_loads
                })
            
            logger.info(f"Generated statistics for {len(stats)} companies")
            return stats
        except Exception as e:
            logger.error(f"Error getting company statistics: {e}")
            return []

    async def assign_driver_to_load(self, load_id: int, driver_id: int) -> bool:
        """Assign any driver to any load - cross-company assignment"""
        try:
            load = self.db.query(Load).filter(Load.id == load_id).first()
            driver = self.db.query(Driver).filter(Driver.id == driver_id).first()
            
            if not load or not driver:
                logger.error(f"Load {load_id} or driver {driver_id} not found")
                return False
            
            load.driver_id = driver_id
            load.assigned_driver = driver.name
            self.db.commit()
            
            logger.info(f"Cross-company assignment: Driver {driver.name} from {driver.company.name if driver.company else 'No Company'} assigned to load {load.trip_id}")
            return True
        except Exception as e:
            logger.error(f"Error assigning driver to load: {e}")
            self.db.rollback()
            return False

    async def get_load_details(self, load_id: int) -> Optional[dict]:
        """Get detailed load information"""
        try:
            load = self.db.query(Load).filter(Load.id == load_id).first()
            if not load:
                return None

            legs = self.db.query(Leg).filter(Leg.load_id == load_id).all()

            return {"load": load, "legs": legs}
        except SQLAlchemyError as e:
            logger.error(f"Error getting load details: {e}")
            return None

    async def get_load_assignment_suggestions(self, load_id: int) -> List[Dict[str, Any]]:
        """Get driver suggestions for a load, including cross-company options"""
        try:
            load = self.db.query(Load).filter(Load.id == load_id).first()
            if not load:
                return []
            
            # Get all available drivers (not currently assigned to active loads)
            available_drivers = (
                self.db.query(Driver)
                .filter(Driver.id.notin_(
                    self.db.query(Load.driver_id)
                    .filter(Load.driver_id.isnot(None))
                    .filter(Load.end_time > load.start_time)  # Overlapping loads
                ))
                .join(Company, Driver.company_id == Company.id, isouter=True)
                .order_by(Company.name.nullsfirst(), Driver.name)
                .all()
            )
            
            suggestions = []
            for driver in available_drivers:
                suggestions.append({
                    "driver": driver,
                    "company_name": driver.company.name if driver.company else "No Company",
                    "has_telegram": driver.chat_id is not None,
                    "cross_company": driver.company_id != load.company_id if load.company_id else False
                })
            
            return suggestions
        except Exception as e:
            logger.error(f"Error getting load assignment suggestions: {e}")
            return []

    async def get_system_wide_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            stats = {
                "loads": {
                    "total": self.db.query(Load).count(),
                    "assigned": self.db.query(Load).filter(Load.driver_id.isnot(None)).count(),
                    "unassigned": self.db.query(Load).filter(Load.driver_id.is_(None)).count(),
                },
                "drivers": {
                    "total": self.db.query(Driver).count(),
                    "telegram": self.db.query(Driver).filter(Driver.chat_id.isnot(None)).count(),
                },
                "companies": {
                    "total": self.db.query(Company).count(),
                    "active": self.db.query(Company).join(Driver).distinct().count(),
                },
                "cross_company": {
                    "enabled": True,
                    "assignments": 0  # Could be calculated if tracking cross-company assignments
                }
            }
            
            logger.info("Generated system-wide statistics")
            return stats
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}