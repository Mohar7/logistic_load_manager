# app/schemas/driver.py
from pydantic import BaseModel
from typing import Optional, List


class DriverBase(BaseModel):
    name: str
    company_id: int
    chat_id: Optional[int] = None


class DriverCreate(DriverBase):
    pass


class Driver(DriverBase):
    id: int

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes


class DriverResponse(BaseModel):
    """
    Response model for drivers.
    """

    id: int
    name: str
    company_id: int
    chat_id: Optional[int] = None

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes
