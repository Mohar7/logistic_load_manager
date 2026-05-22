# app/schemas/load.py
from datetime import datetime
from typing import Any

from fastapi import Body
from pydantic import BaseModel, condecimal


class LegBase(BaseModel):
    leg_id: str
    pick_up_facility_id: str
    drop_off_facility_id: str
    pick_up_address: str
    drop_off_address: str
    pick_up_time: datetime
    drop_off_time: datetime
    pick_up_time_str: str
    drop_off_time_str: str
    fuel_sur_charge: condecimal(max_digits=12, decimal_places=2)
    distance: float
    assigned_driver: str | None = None
    dispatcher_id: int | None = None


class LegCreate(LegBase):
    pass


class LegUpdate(BaseModel):
    leg_id: str | None = None
    pick_up_facility_id: str | None = None
    drop_off_facility_id: str | None = None
    pick_up_address: str | None = None
    drop_off_address: str | None = None
    pick_up_time: datetime | None = None
    drop_off_time: datetime | None = None
    pick_up_time_str: str | None = None
    drop_off_time_str: str | None = None
    fuel_sur_charge: condecimal(max_digits=12, decimal_places=2) | None = None
    distance: float | None = None
    assigned_driver: str | None = None


class LegInDB(LegBase):
    id: int
    load_id: int

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes


class TripBase(BaseModel):
    trip_id: str
    pick_up_facility_id: str
    drop_off_facility_id: str
    pick_up_address: str
    drop_off_address: str
    pick_up_time: datetime
    drop_off_time: datetime
    pick_up_time_str: str
    drop_off_time_str: str
    rate: condecimal(max_digits=12, decimal_places=2)
    rate_per_mile: condecimal(max_digits=12, decimal_places=2)
    distance: float
    assigned_driver: str | None = None
    is_team_load: bool = False
    dispatcher_id: int | None = None


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    trip_id: str | None = None
    pick_up_facility_id: str | None = None
    drop_off_facility_id: str | None = None
    pick_up_address: str | None = None
    drop_off_address: str | None = None
    pick_up_time: datetime | None = None
    drop_off_time: datetime | None = None
    pick_up_time_str: str | None = None
    drop_off_time_str: str | None = None
    rate: condecimal(max_digits=12, decimal_places=2) | None = None
    rate_per_mile: condecimal(max_digits=12, decimal_places=2) | None = None
    distance: float | None = None
    assigned_driver: str | None = None
    is_team_load: bool | None = None
    dispatcher_id: int | None = None


class TripInDB(TripBase):
    id: int

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes


class Trip(TripInDB):
    legs: list[LegInDB] = []


class Leg(LegInDB):
    pass


class LoadRequest(BaseModel):
    """
    Request model for parsing a load text.
    """

    text: str = Body(..., description="Load text to parse", media_type="text/plain")


class LoadUpdateRequest(BaseModel):
    """
    Request model for updating a load.
    """

    trip_id: str | None = None
    pickup_facility_id: int | None = None
    dropoff_facility_id: int | None = None
    pickup_address: str | None = None
    dropoff_address: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    rate: condecimal(max_digits=12, decimal_places=2) | None = None
    rate_per_mile: condecimal(max_digits=12, decimal_places=2) | None = None
    distance: float | None = None
    assigned_driver: str | None = None
    is_team_load: bool | None = None
    dispatcher_id: int | None = None

    class Config:
        from_attributes = True


class ParsedLoadResponse(BaseModel):
    """
    Response model for a parsed load.
    """

    tripInfo: dict[str, Any]
    legs: list[dict[str, Any]]


class LoadResponse(BaseModel):
    """
    Response model for a load from the database.
    """

    id: int
    trip_id: str
    pickup_facility: str | None = None
    dropoff_facility: str | None = None
    pickup_address: str | None = None
    dropoff_address: str | None = None
    start_time: datetime
    end_time: datetime
    rate: float
    rate_per_mile: float
    distance: float | None = None
    assigned_driver: str | None = None
    legs: list[dict[str, Any]] = []

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes
