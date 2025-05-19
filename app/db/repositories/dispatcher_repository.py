# app/db/repositories/company_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.db.models import Dispatchers
import logging

logger = logging.getLogger(__name__)


class DispatcherRepository:
    """
    Repository for Dispatcher entity.
    Handles database operations for dispatchers.
    """

    def __init__(self, db: Session):
        self.db = db

    def add_dispatcher_to_db(self, name: str, telegram_id: int) -> Dispatchers:
        try:
            dispatcher = Dispatchers(
                name=name,
                telegram_id=telegram_id,
            )

            self.db.add(dispatcher)
            self.db.commit()
            self.db.refresh(dispatcher)

            return dispatcher

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error adding dispatcher: {str(e)}")
            raise

    def get_dispatcher_by_id(self, dispatcher_id: int) -> Optional[Dispatchers]:
        return (
            self.db.query(Dispatchers).filter(Dispatchers.id == dispatcher_id).first()
        )

    def get_dispatchers(self, skip: int = 0, limit: int = 100) -> List[Dispatchers]:
        return self.db.query(Dispatchers).offset(skip).limit(limit).all()

    def update_dispatcher(
        self,
        dispatcher_id: int,
        name: Optional[str] = None,
        telegram_id: Optional[int] = None,
    ) -> Optional[Dispatchers]:
        try:
            self.db.query(Dispatchers).filter(Dispatchers.id == dispatcher_id).update(
                {Dispatchers.name: name, Dispatchers.telegram_id: telegram_id}
            )

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating dispatcher: {str(e)}")
            raise

    def delete_dispatcher(self, dispatcher_id: int) -> bool:
        try:
            company = (
                self.db.query(Dispatchers)
                .filter(Dispatchers.id == dispatcher_id)
                .first()
            )
            if not company:
                return False

            self.db.delete(company)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting dispatcher: {str(e)}")
            raise
