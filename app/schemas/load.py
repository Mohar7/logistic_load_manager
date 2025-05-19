# app/schemas/load.py
from pydantic import BaseModel, condecimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import Body


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
    assigned_driver: Optional[str] = None
    dispatcher_id: Optional[int] = None


class LegCreate(LegBase):
    pass


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
    assigned_driver: Optional[str] = None
    is_team_load: bool = False
    dispatcher_id: Optional[int] = None


class TripCreate(TripBase):
    pass


class TripInDB(TripBase):
    id: int

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes


class Trip(TripInDB):
    legs: List[LegInDB] = []


class Leg(LegInDB):
    pass


class LoadRequest(BaseModel):
    """
    Request model for parsing a load text.
    """

    text: str = Body(..., description="Load text to parse", media_type="text/plain")


class ParsedLoadResponse(BaseModel):
    """
    Response model for a parsed load.
    """

    tripInfo: Dict[str, Any]
    legs: List[Dict[str, Any]]


class LoadResponse(BaseModel):
    """
    Response model for a load from the database.
    """

    id: int
    trip_id: str
    pickup_facility: Optional[str] = None
    dropoff_facility: Optional[str] = None
    pickup_address: Optional[str] = None
    dropoff_address: Optional[str] = None
    start_time: datetime
    end_time: datetime
    rate: float
    rate_per_mile: float
    distance: Optional[float] = None
    assigned_driver: Optional[str] = None
    legs: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes
