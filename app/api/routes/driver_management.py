# app/api/routes/driver_management.py
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.driver import DriverCreate, DriverResponse
from app.services.driver_service import DriverService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/drivers",
    tags=["drivers"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=DriverResponse)
async def create_driver(driver: DriverCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new driver.

    Args:
        driver (DriverCreate): Driver data
        db (AsyncSession): Database session

    Returns:
        DriverResponse: Created driver data
    """
    try:
        driver_service = DriverService(db)
        result = await driver_service.create_driver(
            name=driver.name, company_id=driver.company_id, chat_id=driver.chat_id
        )

        driver_data = result["driver"]
        return {
            "id": driver_data.id,
            "name": driver_data.name,
            "company_id": driver_data.company_id,
            "chat_id": driver_data.chat_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating driver: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a driver by ID.

    Args:
        driver_id (int): ID of the driver to retrieve
        db (AsyncSession): Database session

    Returns:
        DriverResponse: Driver data
    """
    driver_service = DriverService(db)
    result = await driver_service.get_driver_by_id(driver_id)

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Driver with ID {driver_id} not found"
        )

    driver_data = result["driver"]
    return {
        "id": driver_data.id,
        "name": driver_data.name,
        "company_id": driver_data.company_id,
        "chat_id": driver_data.chat_id,
    }


@router.get("/", response_model=list[DriverResponse])
async def get_drivers(
    skip: int = 0,
    limit: int = 100,
    company_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all drivers with pagination.

    Args:
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        company_id (int, optional): Filter drivers by company ID
        db (AsyncSession): Database session

    Returns:
        List[DriverResponse]: List of drivers
    """
    driver_service = DriverService(db)

    if company_id:
        # Get drivers for a specific company
        drivers = await driver_service.get_drivers_by_company(company_id)
        return [
            {
                "id": driver.id,
                "name": driver.name,
                "company_id": driver.company_id,
                "chat_id": driver.chat_id,
            }
            for driver in drivers
        ]
    else:
        # Get all drivers
        results = await driver_service.get_drivers(skip, limit)
        return [
            {
                "id": result["driver"].id,
                "name": result["driver"].name,
                "company_id": result["driver"].company_id,
                "chat_id": result["driver"].chat_id,
            }
            for result in results
        ]


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: int,
    driver_update: DriverCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a driver.

    Args:
        driver_id (int): ID of the driver to update
        driver_update (DriverCreate): Updated driver data
        db (AsyncSession): Database session

    Returns:
        DriverResponse: Updated driver data
    """
    try:
        driver_service = DriverService(db)
        result = await driver_service.update_driver(
            driver_id=driver_id,
            name=driver_update.name,
            company_id=driver_update.company_id,
            chat_id=driver_update.chat_id,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail=f"Driver with ID {driver_id} not found"
            )

        driver_data = result["driver"]
        return {
            "id": driver_data.id,
            "name": driver_data.name,
            "company_id": driver_data.company_id,
            "chat_id": driver_data.chat_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating driver: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{driver_id}")
async def delete_driver(driver_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a driver.

    Args:
        driver_id (int): ID of the driver to delete
        db (AsyncSession): Database session

    Returns:
        dict: Success message
    """
    driver_service = DriverService(db)
    result = await driver_service.delete_driver(driver_id)

    if not result:
        raise HTTPException(
            status_code=404, detail=f"Driver with ID {driver_id} not found"
        )

    return {"message": f"Driver with ID {driver_id} successfully deleted"}
