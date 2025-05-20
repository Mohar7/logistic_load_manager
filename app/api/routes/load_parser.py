# app/api/routes/load_parser.py
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Annotated
from app.db.database import get_db
from app.core.parser.parsing_service import ParsingService, get_parsing_service
from app.services.load_service import LoadService
from app.schemas.load import ParsedLoadResponse, LoadResponse

router = APIRouter(
    prefix="/loads",
    tags=["loads"],
    responses={404: {"description": "Not found"}},
)


@router.post("/parse", response_model=ParsedLoadResponse)
async def parse_load(
    text: str = Body(..., media_type="text/plain"),
    parsing_service: ParsingService = Depends(get_parsing_service),
):
    """
    Parse load text and return structured data.

    Args:
            text (str): Load text to parse
            parsing_service (ParsingService): Parsing service dependency

    Returns:
            ParsedLoadResponse: Structured load data
    """
    parsed_data = parsing_service.parse(text)
    if not parsed_data:
        raise HTTPException(status_code=400, detail="Failed to parse load text")
    return parsed_data


@router.post("/create", response_model=LoadResponse)
async def create_load(
    dispatcher_id=Annotated[int, Query(default=None)],
    text: str = Annotated[str, Body(..., media_type="text/plain")],
    db: Session = Depends(get_db),
):
    load_service = LoadService(db)
    result = load_service.parse_and_save_load(text, dispatcher_id=dispatcher_id)

    # Transform the result to match the expected response model
    load = result["load"]
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
    for leg in result["legs"]:
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


@router.get("/{load_id}", response_model=LoadResponse)
async def get_load(load_id: int, db: Session = Depends(get_db)):
    """
    Get a load by its ID.

    Args:
            load_id (int): ID of the load to retrieve
            db (Session): Database session

    Returns:
            LoadResponse: Load data
    """
    load_service = LoadService(db)
    result = load_service.get_load_by_id(load_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"Load with ID {load_id} not found")

    # Transform the result to match the expected response model
    load = result["load"]
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
    for leg in result["legs"]:
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


@router.get("/", response_model=List[LoadResponse])
async def get_loads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all loads with pagination.

    Args:
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return
            db (Session): Database session

    Returns:
            List[LoadResponse]: List of loads
    """
    load_service = LoadService(db)
    results = load_service.get_all_loads(skip, limit)

    response = []
    for result in results:
        load = result["load"]
        load_response = {
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
        for leg in result["legs"]:
            load_response["legs"].append(
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

        response.append(load_response)

    return response


@router.get("/set_dispatcher/{load_id}/{dispatcher_id}")
async def update_dispatcher_for_load(
    load_id: int, dispatcher_id: int, db: Session = Depends(get_db)
):
    load_service = LoadService(db)
    try:
        load_service.update_dispatcher_for_load(
            load_id=load_id, dispatcher_id=dispatcher_id
        )
        return {"message": "success"}
    except Exception as e:
        return {"message": "error", "error": str(e)}
