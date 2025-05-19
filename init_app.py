# init_app.py
import asyncio
import os
import subprocess
import logging
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import engine, SessionLocal
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_database_exists():
    """Check if database tables exist."""
    try:
        inspector = inspect(engine)
        has_tables = len(inspector.get_table_names()) > 0
        if has_tables:
            # Check specifically for our main tables
            required_tables = ["loads", "facilities", "companies", "drivers", "legs"]
            existing_tables = inspector.get_table_names()
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
        logger.error(f"Error checking database: {str(e)}")
        return False


def run_migrations():
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
        logger.error(f"Migration failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {str(e)}")
        return False


def initialize_data():
    """Initialize database with default data."""
    try:
        logger.info("Initializing database data...")
        db = SessionLocal()
        try:
            init_db(db)
            logger.info("Database initialization completed successfully")
        finally:
            db.close()
        return True
    except Exception as e:
        logger.error(f"Data initialization failed: {str(e)}")
        return False


async def setup_database():
    """Set up the database if not already done."""
    if not check_database_exists():
        if run_migrations():
            initialize_data()
    else:
        logger.info("Database is already set up")


if __name__ == "__main__":
    # Run this script directly to set up the database
    asyncio.run(setup_database())
