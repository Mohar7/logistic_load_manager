# app/services/load_service.py
from typing import Dict, Any, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.parser.parsing_service import ParsingService
from app.db.repositories.load_repository import LoadRepository
from app.db.models import Load, Leg
import logging

logger = logging.getLogger(__name__)


class LoadService:
    """
    Service for managing loads.
    Connects the parsing service with the database.
    """

    def __init__(self, db: Session):
        self.db = db
        self.load_repository = LoadRepository(db)

    def parse_and_save_load(self, load_text: str, dispatcher_id: int) -> Dict[str, Any]:
        try:
            # Parse the load text
            parsing_service = ParsingService(
                text=load_text, dispatcher_id=dispatcher_id
            )
            logger.info(
                f"Parsing load text for dispatcher {dispatcher_id} with length {len(load_text)}"
            )
            parsed_data = parsing_service.parse()

            # Check if parsing was successful
            if not parsed_data or "tripInfo" not in parsed_data:
                raise ValueError(
                    "Failed to parse load text or no trip information found"
                )

            # Check if load with this trip_id already exists
            existing_load = self.load_repository.get_load_by_trip_id(
                parsed_data["tripInfo"]["trip_id"]
            )
            if existing_load:
                logger.info(
                    f"Load with trip_id {parsed_data['tripInfo']['trip_id']} already exists"
                )
                # Return existing load with its legs
                legs = self.load_repository.get_legs_for_load(existing_load.id)
                return {"load": existing_load, "legs": legs, "is_new": False}

            # Create new load
            load = self.load_repository.create_load(parsed_data["tripInfo"])

            # Create legs for the load
            legs = []
            for leg_data in parsed_data.get("legs", []):
                leg = self.load_repository.create_leg(load.id, leg_data)
                legs.append(leg)

            return {"load": load, "legs": legs, "is_new": True}

        except Exception as e:
            logger.error(f"Error in parse_and_save_load: {str(e)}")
            raise

    def get_load_by_id(self, load_id: int) -> Optional[Dict[str, Any]]:
        load = self.load_repository.get_load_by_id(load_id)
        if not load:
            return None

        legs = self.load_repository.get_legs_for_load(load_id)

        return {"load": load, "legs": legs}

    def get_load_by_trip_id(self, trip_id: str) -> Optional[Dict[str, Any]]:
        load = self.load_repository.get_load_by_trip_id(trip_id)
        if not load:
            return None

        legs = self.load_repository.get_legs_for_load(load.id)

        return {"load": load, "legs": legs}

    def get_all_loads(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        loads = self.load_repository.get_loads(skip, limit)
        result = []

        for load in loads:
            legs = self.load_repository.get_legs_for_load(load.id)
            result.append({"load": load, "legs": legs})

        return result

    def update_dispatcher_for_load(self, load_id: int, dispatcher_id: int):
        try:
            self.load_repository.update_dispatcher_for_the_load(
                load_id=load_id, dispatcher_id=dispatcher_id
            )
        except SQLAlchemyError as e:
            logger.error(f"Error updating dispatcher for load: {str(e)}")
            raise
