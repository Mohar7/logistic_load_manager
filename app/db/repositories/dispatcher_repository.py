# app/db/repositories/dispatcher_repository.py
import logging

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dispatchers

logger = logging.getLogger(__name__)


class DispatcherRepository:
    """
    Repository for Dispatcher entity.
    Handles database operations for dispatchers.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_dispatcher_to_db(self, name: str, telegram_id: int) -> Dispatchers:
        try:
            dispatcher = Dispatchers(
                name=name,
                telegram_id=telegram_id,
            )

            self.db.add(dispatcher)
            await self.db.commit()
            await self.db.refresh(dispatcher)

            return dispatcher

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error adding dispatcher: {e!s}")
            raise

    async def get_dispatcher_by_id(self, dispatcher_id: int) -> Dispatchers | None:
        result = await self.db.execute(select(Dispatchers).where(Dispatchers.id == dispatcher_id))
        return result.scalar_one_or_none()

    async def get_dispatcher_by_telegram_id(self, telegram_id: int) -> Dispatchers | None:
        result = await self.db.execute(
            select(Dispatchers).where(Dispatchers.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_dispatchers(self, skip: int = 0, limit: int = 100) -> list[Dispatchers]:
        result = await self.db.execute(select(Dispatchers).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update_dispatcher(
        self,
        dispatcher_id: int,
        name: str | None = None,
        telegram_id: int | None = None,
    ) -> Dispatchers | None:
        try:
            await self.db.execute(
                update(Dispatchers)
                .where(Dispatchers.id == dispatcher_id)
                .values(name=name, telegram_id=telegram_id)
            )
            await self.db.commit()
            return await self.get_dispatcher_by_id(dispatcher_id)

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating dispatcher: {e!s}")
            raise

    async def delete_dispatcher(self, dispatcher_id: int) -> bool:
        try:
            result = await self.db.execute(
                select(Dispatchers).where(Dispatchers.id == dispatcher_id)
            )
            company = result.scalar_one_or_none()
            if not company:
                return False

            await self.db.delete(company)
            await self.db.commit()

            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting dispatcher: {e!s}")
            raise
