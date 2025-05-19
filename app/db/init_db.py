# app/db/init_db.py
from sqlalchemy.orm import Session
from app.db.models import Company
import logging

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Initialize the database with default data.

    Args:
        db (Session): Database session
    """
    # Create a default company if none exists
    company = db.query(Company).first()
    if not company:
        logger.info("Creating default company")
        company = Company(
            name="Default Logistics Company",
            usdot=12345,
            carrier_identifier="DEFAULT",
            mc=67890,
        )
        db.add(company)
        db.commit()
        logger.info(f"Created default company with ID {company.id}")
    else:
        logger.info(f"Default company already exists with ID {company.id}")
