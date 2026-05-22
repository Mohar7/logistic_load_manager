# init_app.py
import logging
import os
import subprocess

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.db.database import SYNC_DATABASE_URL
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bootstrap is a one-shot synchronous task; we don't need the async engine here.
# Using psycopg2 keeps Alembic and inspection straightforward.
bootstrap_engine = create_engine(SYNC_DATABASE_URL)
BootstrapSession = sessionmaker(bootstrap_engine)


def check_database_exists() -> bool:
    """Check if database tables exist."""
    try:
        inspector = inspect(bootstrap_engine)
        existing_tables = inspector.get_table_names()
        if existing_tables:
            # Check specifically for our main tables
            required_tables = ["loads", "facilities", "companies", "drivers", "legs"]
            missing_tables = [
                table for table in required_tables if table not in existing_tables
            ]

            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                return False
            return True
        else:
            logger.warning("No tables found in the database")
            return False
    except SQLAlchemyError as e:
        logger.error(f"Error checking database: {e!s}")
        return False


def run_migrations() -> bool:
    """Run database migrations."""
    try:
        logger.info("Running database migrations...")
        # Check if we're running in Docker or locally
        if os.path.exists("/.dockerenv"):
            # In Docker, use alembic directly
            subprocess.run(["alembic", "upgrade", "head"], check=True)
        else:
            # Local environment
            subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Database migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e!s}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e!s}")
        return False


def initialize_data() -> bool:
    """Initialize database with default data."""
    try:
        logger.info("Initializing database data...")
        with BootstrapSession() as db:
            init_db(db)
            logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Data initialization failed: {e!s}")
        return False


async def setup_database() -> None:
    """Set up the database if not already done.

    Stays async because it's called from the FastAPI lifespan context, but
    the underlying work is synchronous (alembic + table inspection). One-shot
    blocking I/O at startup is acceptable.
    """
    if not check_database_exists():
        if run_migrations():
            initialize_data()
    else:
        logger.info("Database is already set up")


if __name__ == "__main__":
    import asyncio

    asyncio.run(setup_database())
