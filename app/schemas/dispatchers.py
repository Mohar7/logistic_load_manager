# app/schemas/company.py

from pydantic import BaseModel


class DispatcherBase(BaseModel):
    name: str
    telegram_id: int


class AddDispatcher(DispatcherBase):
    pass


class Dispatcher(DispatcherBase):
    id: int

    class Config:
        from_attributes = True


class DispatcherResponse(BaseModel):
    id: int
    name: str
    telegram_id: int

    class Config:
        from_attributes = True
