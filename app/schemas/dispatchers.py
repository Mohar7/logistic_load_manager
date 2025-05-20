# app/schemas/company.py
from pydantic import BaseModel
from typing import Optional, List


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
