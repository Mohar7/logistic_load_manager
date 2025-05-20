# app/services/dispatcher_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.db.repositories.dispatcher_repository import DispatcherRepository
from app.db.repositories.load_repository import LoadRepository
from app.schemas.dispatchers import DispatcherResponse, AddDispatcher
import logging

logger = logging.getLogger(__name__)


class DispatcherService:
    """
    Service class for managing dispatchers.
    """

    def __init__(self, db: Session):
        self.db = db
        self.dispatcher_repo = DispatcherRepository(db)
        self.load_repo = LoadRepository(db)

    def add_dispatcher(self, dispatcher_data: AddDispatcher) -> DispatcherResponse:
        """
        Adds a new dispatcher to the database.

        Args:
            dispatcher_data (AddDispatcher): Data for the new dispatcher.

        Returns:
            DispatcherResponse: Created dispatcher data.

        Raises:
            ValueError: If dispatcher with telegram_id already exists.
        """
        try:
            # Check for existing dispatcher
            existing = self.dispatcher_repo.get_dispatcher_by_telegram_id(dispatcher_data.telegram_id)
            if existing:
                raise ValueError(f"Dispatcher with telegram_id {dispatcher_data.telegram_id} already exists.")

            # Save to DB
            self.dispatcher_repo.add_dispatcher_to_db(
                name=dispatcher_data.name,
                telegram_id=dispatcher_data.telegram_id
            )

            # Fetch created dispatcher
            created_dispatcher = self.dispatcher_repo.get_dispatcher_by_telegram_id(dispatcher_data.telegram_id)
            logger.info(f"Dispatcher '{dispatcher_data.name}' added successfully.")
            return DispatcherResponse.model_validate(created_dispatcher)

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error in add_dispatcher: {str(e)}")
            raise ValueError(f"Dispatcher with telegram_id {dispatcher_data.telegram_id} already exists.") from e
        except Exception as e:
            logger.error(f"Unexpected error in add_dispatcher: {str(e)}")
            raise

    def get_dispatcher_by_id(self, dispatcher_id: int) -> Optional[DispatcherResponse]:
        """
        Retrieve a dispatcher by ID.

        Args:
            dispatcher_id (int): ID of the dispatcher.

        Returns:
            Optional[DispatcherResponse]: Dispatcher data or None if not found.
        """
        dispatcher = self.dispatcher_repo.get_dispatcher_by_id(dispatcher_id)
        return DispatcherResponse.model_validate(dispatcher) if dispatcher else None

    def get_dispatcher_by_telegram_id(self, telegram_id: int) -> Optional[DispatcherResponse]:
        """
        Retrieve a dispatcher by Telegram ID.

        Args:
            telegram_id (int): Telegram ID of the dispatcher.

        Returns:
            Optional[DispatcherResponse]: Dispatcher data or None if not found.
        """
        dispatcher = self.dispatcher_repo.get_dispatcher_by_telegram_id(telegram_id)
        return DispatcherResponse.model_validate(dispatcher) if dispatcher else None

    def get_dispatchers(self, skip: int = 0, limit: int = 100) -> List[DispatcherResponse]:
        """
        Get a list of dispatchers.

        Args:
            skip (int): Number of records to skip.
            limit (int): Max number of records to return.

        Returns:
            List[DispatcherResponse]: List of dispatchers.
        """
        dispatchers = self.dispatcher_repo.get_dispatchers(skip, limit)
        return [DispatcherResponse.model_validate(d) for d in dispatchers]

    def update_dispatcher(
        self,
        dispatcher_id: int,
        name: Optional[str] = None,
        telegram_id: Optional[int] = None,
    ) -> Optional[DispatcherResponse]:
        """
        Update an existing dispatcher.

        Args:
            dispatcher_id (int): ID of the dispatcher to update.
            name (Optional[str]): New name.
            telegram_id (Optional[int]): New Telegram ID.

        Returns:
            Optional[DispatcherResponse]: Updated dispatcher or None if not found.

        Raises:
            ValueError: If Telegram ID is already taken.
        """
        try:
            updated_dispatcher = self.dispatcher_repo.update_dispatcher(
                dispatcher_id=dispatcher_id,
                name=name,
                telegram_id=telegram_id
            )
            if not updated_dispatcher:
                logger.warning(f"Dispatcher with ID {dispatcher_id} not found.")
                return None

            logger.info(f"Dispatcher ID {dispatcher_id} updated successfully.")
            return DispatcherResponse.model_validate(updated_dispatcher)
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error in update_dispatcher: {str(e)}")
            raise ValueError(f"Telegram ID {telegram_id} is already taken.") from e
        except Exception as e:
            logger.error(f"Unexpected error in update_dispatcher: {str(e)}")
            raise

    def delete_dispatcher(self, dispatcher_id: int) -> bool:
        """
        Delete a dispatcher if no loads are associated.

        Args:
            dispatcher_id (int): ID of the dispatcher to delete.

        Returns:
            bool: True if deleted, False otherwise.

        Raises:
            ValueError: If the dispatcher has associated loads.
        """
        loads = self.load_repo.get_loads_by_dispatcher_id(dispatcher_id)
        if loads:
            msg = f"Cannot delete dispatcher {dispatcher_id}: {len(loads)} loads associated."
            logger.warning(msg)
            raise ValueError(msg)

        deleted = self.dispatcher_repo.delete_dispatcher(dispatcher_id=dispatcher_id)
        if deleted:
            logger.info(f"Dispatcher {dispatcher_id} was successfully deleted.")
        else:
            logger.error(f"Failed to delete dispatcher {dispatcher_id}.")
        return deleted