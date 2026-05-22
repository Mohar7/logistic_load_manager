# app/schemas/company.py

from pydantic import BaseModel


class CompanyBase(BaseModel):
    name: str
    usdot: int
    carrier_identifier: str
    mc: int


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    id: int

    class Config:
        from_attributes = True


class CompanyResponse(BaseModel):
    """
    Response model for companies.
    """

    id: int
    name: str
    usdot: int
    carrier_identifier: str
    mc: int
    drivers_count: int

    class Config:
        from_attributes = True
