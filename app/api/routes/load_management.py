# app/api/routes/load_management.py
# app/api/routes/load_management.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.services.load_service import LoadService
from app.services.notification_service import NotificationService
from app.db.repositories.driver_repository import DriverRepository
from app.schemas.load import LoadResponse
from app.schemas.driver import DriverResponse
import asyncio

router = APIRouter(
    prefix="/load-management",
    tags=["load-management"],
    responses={404: {"description": "Not found"}},
)


@router.put("/{load_id}/assign-driver/{driver_id}", response_model=LoadResponse)
async def assign_driver_to_load(
    load_id: int,
    driver_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Assign a driver to a load.

    Args:
        load_id (int): ID of the load
        driver_id (int): ID of the driver to assign
        background_tasks (BackgroundTasks): FastAPI background tasks
        db (Session): Database session

    Returns:
        LoadResponse: Updated load data
    """
    # Get the load
    load_service = LoadService(db)
    load_data = load_service.get_load_by_id(load_id)

    if not load_data:
        raise HTTPException(status_code=404, detail=f"Load with ID {load_id} not found")

    # Get the driver
    driver_repo = DriverRepository(db)
    driver = driver_repo.get_driver_by_id(driver_id)

    if not driver:
        raise HTTPException(
            status_code=404, detail=f"Driver with ID {driver_id} not found"
        )

    # Update the load with the driver
    load = load_data["load"]
    load.driver_id = driver_id
    load.assigned_driver = driver.name
    db.commit()
    db.refresh(load)

    # Send notification to the driver in the background
    async def send_notification():
        notification_service = NotificationService(db)
        await notification_service.notify_driver_about_load(load_id, driver_id)

    background_tasks.add_task(asyncio.run, send_notification())

    # Format response
    response = {
        "id": load.id,
        "trip_id": load.trip_id,
        "pickup_facility": load.pickup_facility.name
        if hasattr(load, "pickup_facility") and load.pickup_facility
        else load.pickup_facility_id,
        "dropoff_facility": load.dropoff_facility.name
        if hasattr(load, "dropoff_facility") and load.dropoff_facility
        else load.dropoff_facility_id,
        "pickup_address": load.pickup_address,
        "dropoff_address": load.dropoff_address,
        "start_time": load.start_time,
        "end_time": load.end_time,
        "rate": float(load.rate),
        "rate_per_mile": float(load.rate_per_mile),
        "distance": float(load.distance) if load.distance else None,
        "assigned_driver": load.assigned_driver,
        "legs": [],
    }

    # Add legs to the response
    for leg in load_data["legs"]:
        response["legs"].append(
            {
                "id": leg.id,
                "leg_id": leg.leg_id,
                "pickup_facility_id": leg.pickup_facility_id,
                "dropoff_facility_id": leg.dropoff_facility_id,
                "pickup_address": leg.pickup_address,
                "dropoff_address": leg.dropoff_address,
                "pickup_time": leg.pickup_time,
                "dropoff_time": leg.dropoff_time,
                "fuel_sur_charge": float(leg.fuel_sur_charge),
                "distance": float(leg.distance) if leg.distance else None,
                "assigned_driver": leg.assigned_driver,
            }
        )

    return response


@router.get("/assigned-drivers", response_model=List[DriverResponse])
async def get_assigned_drivers(db: Session = Depends(get_db)):
    """
    Get all drivers that have been assigned to loads.

    Args:
        db (Session): Database session

    Returns:
        List[DriverResponse]: List of drivers with load assignments
    """
    # Query for drivers with assignments
    query = (
        db.query(DriverRepository(db).db.query(DriverRepository(db).db.models.Driver))
        .join(
            DriverRepository(db).db.models.Load,
            DriverRepository(db).db.models.Load.driver_id
            == DriverRepository(db).db.models.Driver.id,
        )
        .distinct()
    )

    drivers = query.all()

    response = []
    for driver in drivers:
        response.append(
            {
                "id": driver.id,
                "name": driver.name,
                "company_id": driver.company_id,
                "chat_id": driver.chat_id,
            }
        )

    return response


@router.get("/available-drivers", response_model=List[DriverResponse])
async def get_available_drivers(db: Session = Depends(get_db)):
    """
    Get all drivers that are not currently assigned to loads.

    Args:
        db (Session): Database session

    Returns:
        List[DriverResponse]: List of available drivers
    """
    # Query for drivers without assignments
    driver_repo = DriverRepository(db)

    # This would be more efficient with a proper subquery
    all_drivers = driver_repo.get_drivers()
    assigned_drivers = (
        db.query(driver_repo.db.models.Driver)
        .join(
            driver_repo.db.models.Load,
            driver_repo.db.models.Load.driver_id == driver_repo.db.models.Driver.id,
        )
        .distinct()
        .all()
    )

    assigned_ids = [d.id for d in assigned_drivers]
    available_drivers = [d for d in all_drivers if d.id not in assigned_ids]

    response = []
    for driver in available_drivers:
        response.append(
            {
                "id": driver.id,
                "name": driver.name,
                "company_id": driver.company_id,
                "chat_id": driver.chat_id,
            }
        )

    return response


@router.post("/{load_id}/notify-driver", response_model=dict)
async def notify_driver(
    load_id: int, driver_id: Optional[int] = None, db: Session = Depends(get_db)
):
    """
    Send a notification to a driver about a load.

    Args:
        load_id (int): ID of the load
        driver_id (int, optional): ID of the driver to notify. If None, uses the driver assigned to the load.
        db (Session): Database session

    Returns:
        dict: Result of the notification
    """
    notification_service = NotificationService(db)
    result = await notification_service.notify_driver_about_load(load_id, driver_id)

    return {"success": result}
