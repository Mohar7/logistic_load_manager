# app/db/repositories/load_repository.py - updated
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from app.db.models import Load, Leg, Facility, Driver, Company
from app.schemas.load import TripCreate, LegCreate, Trip, Leg as LegSchema
import logging

logger = logging.getLogger(__name__)


class LoadRepository:
    """
    Repository for Load and Leg entities.
    Handles database operations for loads and legs.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_load(self, load_data: Dict[str, Any]) -> Load:
        """
        Create a new load record in the database.

        Args:
                load_data (Dict[str, Any]): Load data from parsed trip

        Returns:
                Load: Created load instance
        """
        try:
            # Check if facilities exist, create if not
            pickup_facility = self._get_or_create_facility(
                load_data["pick_up_facility_id"], load_data["pick_up_address"]
            )

            dropoff_facility = self._get_or_create_facility(
                load_data["drop_off_facility_id"], load_data["drop_off_address"]
            )

            # Check if driver exists
            driver_id = None
            if load_data.get("assigned_driver"):
                driver = (
                    self.db.query(Driver)
                    .filter(Driver.name == load_data["assigned_driver"])
                    .first()
                )
                if driver:
                    driver_id = driver.id

            # Get default company (for demo purposes)
            company = self._get_default_company()

            # Create the load
            db_load = Load(
                trip_id=load_data["trip_id"],
                pickup_facility_id=pickup_facility.id,
                dropoff_facility_id=dropoff_facility.id,
                pickup_address=load_data["pick_up_address"],
                dropoff_address=load_data["drop_off_address"],
                start_time=load_data["pick_up_time"],
                end_time=load_data["drop_off_time"],
                start_time_str=load_data["pick_up_time_str"],
                end_time_str=load_data["drop_off_time_str"],
                rate=load_data["rate"],
                rate_per_mile=load_data["rate_per_mile"],
                distance=load_data["distance"],
                driver_id=driver_id,
                assigned_driver=load_data.get("assigned_driver"),
                company_id=company.id,
                is_team_load=load_data.get("is_team_load", False),
            )

            self.db.add(db_load)
            self.db.commit()
            self.db.refresh(db_load)

            return db_load

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating load: {str(e)}")
            raise

    def create_leg(self, load_id: int, leg_data: Dict[str, Any]) -> Leg:
        """
        Create a leg for a load.

        Args:
                load_id (int): ID of the parent load
                leg_data (Dict[str, Any]): Leg data from parsing

        Returns:
                Leg: Created leg instance
        """
        try:
            db_leg = Leg(
                leg_id=leg_data["leg_id"],
                load_id=load_id,
                pickup_facility_id=leg_data["pick_up_facility_id"],
                dropoff_facility_id=leg_data["drop_off_facility_id"],
                pickup_address=leg_data["pick_up_address"],
                dropoff_address=leg_data["drop_off_address"],
                pickup_time=leg_data["pick_up_time"],
                dropoff_time=leg_data["drop_off_time"],
                pickup_time_str=leg_data["pick_up_time_str"],
                dropoff_time_str=leg_data["drop_off_time_str"],
                fuel_sur_charge=leg_data["fuel_sur_charge"],
                distance=leg_data["distance"],
                assigned_driver=leg_data.get("assigned_driver"),
            )

            self.db.add(db_leg)
            self.db.commit()
            self.db.refresh(db_leg)

            return db_leg

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating leg: {str(e)}")
            raise

    def get_load_by_id(self, load_id: int) -> Optional[Load]:
        """
        Get a load by its ID.

        Args:
                load_id (int): Load ID to find

        Returns:
                Optional[Load]: Load if found, None otherwise
        """
        return self.db.query(Load).filter(Load.id == load_id).first()

    def get_load_by_trip_id(self, trip_id: str) -> Optional[Load]:
        """
        Get a load by its trip ID.

        Args:
                trip_id (str): Trip ID to find

        Returns:
                Optional[Load]: Load if found, None otherwise
        """
        return self.db.query(Load).filter(Load.trip_id == trip_id).first()

    def get_loads(self, skip: int = 0, limit: int = 100) -> List[Load]:
        """
        Get a list of loads with pagination.

        Args:
                skip (int): Number of records to skip
                limit (int): Maximum number of records to return

        Returns:
                List[Load]: List of loads
        """
        return self.db.query(Load).offset(skip).limit(limit).all()

    def get_legs_for_load(self, load_id: int) -> List[Leg]:
        """
        Get all legs for a specific load.

        Args:
                load_id (int): Load ID to get legs for

        Returns:
                List[Leg]: List of legs
        """
        return self.db.query(Leg).filter(Leg.load_id == load_id).all()

    def _get_or_create_facility(self, facility_id: str, location: str) -> Facility:
        """
        Get a facility by ID or create it if it doesn't exist.

        Args:
                facility_id (str): Facility ID
                location (str): Facility location

        Returns:
                Facility: Found or created facility
        """
        # Try to find by name first
        facility = self.db.query(Facility).filter(Facility.name == facility_id).first()

        if not facility:
            logger.info(f"Creating new facility: {facility_id}")
            try:
                facility = Facility(name=facility_id, location=location)
                self.db.add(facility)
                self.db.commit()
                self.db.refresh(facility)
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"Error creating facility: {str(e)}")
                # Try again in case another process created it concurrently
                facility = (
                    self.db.query(Facility).filter(Facility.name == facility_id).first()
                )
                if not facility:
                    # If still not found, create a default facility
                    facility = Facility(name=facility_id, location=location)
                    self.db.add(facility)
                    self.db.commit()
                    self.db.refresh(facility)

        return facility

    def _get_default_company(self) -> Company:
        """
        Get or create a default company for testing purposes.

        Returns:
                Company: Default company instance
        """
        company = self.db.query(Company).first()
        if not company:
            company = Company(
                name="Default Logistics Company",
                usdot=12345,
                carrier_identifier="DEFAULT",
                mc=67890,
            )
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
        return company

    def update_dispatcher_for_the_load(self, load_id: int, dispatcher_id: int):
        try:
            self.db.query(Load).filter(Load.id == load_id).update(
                {Load.dispatcher_id: dispatcher_id}
            )
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error setting dispatcher for the load: {str(e)}")
            raise
