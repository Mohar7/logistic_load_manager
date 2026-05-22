# app/schemas/driver.py

from pydantic import BaseModel


class DriverBase(BaseModel):
    name: str
    company_id: int
    chat_id: int | None = None


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
    chat_id: int | None = None

    class Config:
        from_attributes = True  # Changed from orm_mode to from_attributes
