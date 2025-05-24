# app/db/models.py - Updated to handle facility names and IDs
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Numeric,
    Boolean,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    location = Column(String(255))
    full_address = Column(Text, nullable=True)

    pickup_loads = relationship(
        "Load", foreign_keys="Load.pickup_facility_id", back_populates="pickup_facility"
    )
    dropoff_loads = relationship(
        "Load",
        foreign_keys="Load.dropoff_facility_id",
        back_populates="dropoff_facility",
    )


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    usdot = Column(Integer)
    carrier_identifier = Column(String(255))
    mc = Column(Integer)

    telegram_chats = relationship("TelegramChat", back_populates="company")
    drivers = relationship("Driver", back_populates="company")
    loads = relationship("Load", back_populates="company")


class TelegramChat(Base):
    __tablename__ = "telegram_chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(255))
    chat_token = Column(Integer)
    company_id = Column(Integer, ForeignKey("companies.id"))

    company = relationship("Company", back_populates="telegram_chats")
    drivers = relationship("Driver", back_populates="chat")


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    company_id = Column(Integer, ForeignKey("companies.id"))
    chat_id = Column(Integer, ForeignKey("telegram_chats.id"))

    company = relationship("Company", back_populates="drivers")
    chat = relationship("TelegramChat", back_populates="drivers")
    loads = relationship("Load", back_populates="driver")


class Dispatchers(Base):
    __tablename__ = "dispatchers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    telegram_id = Column(Integer)

    loads = relationship("Load", back_populates="dispatcher")


class Load(Base):
    __tablename__ = "loads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String(255), unique=True)

    # Facility IDs (nullable for when facilities don't exist yet)
    pickup_facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    dropoff_facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)

    # Facility names/codes (for when we have codes like PSP1, TUS5)
    pickup_facility_name = Column(String(255), nullable=True)
    dropoff_facility_name = Column(String(255), nullable=True)

    # Address information
    pickup_address = Column(String(255))
    dropoff_address = Column(String(255))
    pickup_full_address = Column(Text, nullable=True)
    dropoff_full_address = Column(Text, nullable=True)

    # Time information
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    start_time_str = Column(String(50))
    end_time_str = Column(String(50))

    # Financial information
    rate = Column(Numeric(12, 2), nullable=False)
    rate_per_mile = Column(Numeric(12, 2), nullable=False)
    distance = Column(Numeric(10, 2))

    # Driver assignment
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    assigned_driver = Column(String(255), nullable=True)

    # Company and dispatcher
    company_id = Column(Integer, ForeignKey("companies.id"))
    dispatcher_id = Column(Integer, ForeignKey("dispatchers.id"), nullable=True)

    # Load properties
    is_team_load = Column(Boolean, default=False)

    # Relationships
    pickup_facility = relationship(
        "Facility", foreign_keys=[pickup_facility_id], back_populates="pickup_loads"
    )
    dropoff_facility = relationship(
        "Facility", foreign_keys=[dropoff_facility_id], back_populates="dropoff_loads"
    )
    driver = relationship("Driver", back_populates="loads")
    company = relationship("Company", back_populates="loads")
    legs = relationship("Leg", back_populates="load")
    dispatcher = relationship("Dispatchers", back_populates="loads")


class Leg(Base):
    __tablename__ = "legs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    leg_id = Column(String(255), unique=True)
    load_id = Column(Integer, ForeignKey("loads.id"))

    # Facility information (both IDs and names/codes)
    pickup_facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    dropoff_facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    pickup_facility_name = Column(String(255), nullable=True)
    dropoff_facility_name = Column(String(255), nullable=True)

    # Address information
    pickup_address = Column(String(255))
    dropoff_address = Column(String(255))
    pickup_full_address = Column(Text, nullable=True)
    dropoff_full_address = Column(Text, nullable=True)

    # Time information
    pickup_time = Column(DateTime, nullable=False)
    dropoff_time = Column(DateTime, nullable=False)
    pickup_time_str = Column(String(50))
    dropoff_time_str = Column(String(50))

    # Financial and distance information
    fuel_sur_charge = Column(Numeric(12, 2))
    distance = Column(Numeric(10, 2))
    assigned_driver = Column(String(255), nullable=True)

    # Relationships
    load = relationship("Load", back_populates="legs")
    pickup_facility = relationship("Facility", foreign_keys=[pickup_facility_id])
    dropoff_facility = relationship("Facility", foreign_keys=[dropoff_facility_id])
