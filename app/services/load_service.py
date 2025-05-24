# app/services/load_service.py
from typing import Dict, Any, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.parser.parsing_service import ParsingService
from app.db.repositories.load_repository import LoadRepository
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

    def parse_and_save_load(
        self, load_text: str, dispatcher_id: int = None
    ) -> Dict[str, Any]:
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

    def update_load(
        self, load_id: int, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing load with provided data.

        Args:
            load_id (int): ID of the load to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Dict[str, Any]]: Updated load with legs or None if not found
        """
        try:
            # Check if load exists
            existing_load = self.load_repository.get_load_by_id(load_id)
            if not existing_load:
                logger.warning(f"Load with ID {load_id} not found")
                return None

            # Update the load
            updated_load = self.load_repository.update_load(load_id, update_data)

            # Get updated legs
            legs = self.load_repository.get_legs_for_load(load_id)

            logger.info(f"Load {load_id} updated successfully")
            return {"load": updated_load, "legs": legs}

        except Exception as e:
            logger.error(f"Error updating load {load_id}: {str(e)}")
            raise

    def update_load_with_parsed_data(
        self, load_id: int, load_text: str, dispatcher_id: int = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing load by parsing new text data.

        Args:
            load_id (int): ID of the load to update
            load_text (str): New load text to parse
            dispatcher_id (int, optional): Dispatcher ID

        Returns:
            Optional[Dict[str, Any]]: Updated load with legs or None if not found
        """
        try:
            # Check if load exists
            existing_load = self.load_repository.get_load_by_id(load_id)
            if not existing_load:
                logger.warning(f"Load with ID {load_id} not found")
                return None

            # Parse the new load text
            parsing_service = ParsingService(
                text=load_text, dispatcher_id=dispatcher_id
            )
            parsed_data = parsing_service.parse()

            if not parsed_data or "tripInfo" not in parsed_data:
                raise ValueError(
                    "Failed to parse load text or no trip information found"
                )

            # Delete existing legs
            self.load_repository.delete_legs_for_load(load_id)

            # Update the load with parsed trip info
            updated_load = self.load_repository.update_load(
                load_id, parsed_data["tripInfo"]
            )

            # Create new legs
            legs = []
            for leg_data in parsed_data.get("legs", []):
                leg = self.load_repository.create_leg(load_id, leg_data)
                legs.append(leg)

            logger.info(f"Load {load_id} updated with parsed data successfully")
            return {"load": updated_load, "legs": legs}

        except Exception as e:
            logger.error(f"Error updating load {load_id} with parsed data: {str(e)}")
            raise

    def delete_load(self, load_id: int) -> bool:
        """
        Delete a load and all its associated legs.

        Args:
            load_id (int): ID of the load to delete

        Returns:
            bool: True if deleted successfully, False if not found
        """
        try:
            # Check if load exists
            existing_load = self.load_repository.get_load_by_id(load_id)
            if not existing_load:
                logger.warning(f"Load with ID {load_id} not found")
                return False

            # Delete legs first (foreign key constraint)
            self.load_repository.delete_legs_for_load(load_id)

            # Delete the load
            success = self.load_repository.delete_load(load_id)

            if success:
                logger.info(f"Load {load_id} and its legs deleted successfully")
            else:
                logger.warning(f"Failed to delete load {load_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting load {load_id}: {str(e)}")
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
