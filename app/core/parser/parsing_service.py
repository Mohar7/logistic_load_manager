# app/core/parser/parsing_service.py
import re
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import Body, Depends
from decimal import Decimal
from app.schemas.load import Trip, Leg
from app.core.utils.date_utils import parse_datetime_with_tz
from app.core.utils.text_utils import find_first, find_all, parse_decimal
from app.core.parser.regex_patterns import (
    TRIP_ID_PATTERN,
    FACILITY_PATTERN,
    TRIP_TIME_PATTERN,
    PRICE_PATTERN,
    RPM_PATTERN,
    DISTANCE_PATTERN,
    LEG_ID_PATTERN,
    LEG_FACILITY_PATTERN,
    SIMPLE_PRICE_PATTERN,
    ADDRESS_PATTERN,
    DRIVER_PATTERN,
    LEG_SPLIT_MARKER,
)


class ParsingService:
    """
    Service class for parsing text data to extract trip information and legs.
    This class provides functionality to process a structured string of text
    containing trip and stop details. It extracts relevant information,
    organizes it into a dictionary structure, and outputs it in JSON format.
    """

    def __init__(
        self,
        text: str = Body(description="load text", media_type="text/plain", default=""),
        dispatcher_id: Optional[int] = None,
    ):
        self.text = text
        self.data = None
        self.dispatcher_id = dispatcher_id

    def _extract_trip_info(
        self,
        text: str,
        full_text: Optional[str] = None,
        dispatcher_id: Optional[int] = None,
    ) -> Trip:
        """Extracts trip information from a text block."""
        if full_text is None:
            full_text = text  # Use main text if full_text is not provided

        dispatcher_id = dispatcher_id if dispatcher_id else self.dispatcher_id
        trip_id = find_first(TRIP_ID_PATTERN, text)
        trip_id = trip_id if trip_id else find_first(LEG_ID_PATTERN, full_text)

        facilities = find_all(FACILITY_PATTERN, text)
        pick_up_facility_id = facilities[0] if facilities else None
        drop_off_facility_id = facilities[1] if len(facilities) > 1 else None

        times = find_all(TRIP_TIME_PATTERN, full_text)
        pick_up_time = parse_datetime_with_tz(times[0]) if len(times) > 0 else None
        pick_up_time_str = times[0] if len(times) > 0 else None
        drop_off_time_str = times[-2] if len(times) > 1 else None
        drop_off_time = parse_datetime_with_tz(times[-2]) if len(times) >= 2 else None

        rate_str = find_first(PRICE_PATTERN, text)
        rate = parse_decimal(rate_str)

        rpm_str = find_first(RPM_PATTERN, text)
        rate_per_mile = parse_decimal(rpm_str)

        dist_str = find_first(DISTANCE_PATTERN, text, group=1)
        distance = int(dist_str) if dist_str else None

        addresses = find_all(ADDRESS_PATTERN, text)
        pick_up_address = addresses[0].strip() if addresses else None
        drop_off_address = addresses[-1].strip() if len(addresses) > 1 else None

        driver = find_first(DRIVER_PATTERN, text, group=1)
        assigned_driver = driver.strip() if driver else None

        return Trip(
            trip_id=trip_id or "UNKNOWN_TRIP_ID",
            pick_up_facility_id=pick_up_facility_id or "UNKNOWN_FACILITY",
            drop_off_facility_id=drop_off_facility_id or "UNKNOWN_FACILITY",
            pick_up_time=pick_up_time or datetime.min,
            drop_off_time=drop_off_time or datetime.min,
            rate=rate or Decimal(0.0),
            rate_per_mile=rate_per_mile or Decimal(0.0),
            distance=float(distance) if distance is not None else 0.0,
            pick_up_address=pick_up_address or "UNKNOWN_ADDRESS",
            drop_off_address=drop_off_address or "UNKNOWN_ADDRESS",
            assigned_driver=assigned_driver,
            is_team_load=False,
            pick_up_time_str=pick_up_time_str or "UNKNOWN_TIME",
            drop_off_time_str=drop_off_time_str or "UNKNOWN_TIME",
            id=0,  # Temporary ID, will be replaced when saved to database
            legs=[],
            dispatcher_id=dispatcher_id,
        )

    def _extract_leg_info(self, leg_text: str) -> Leg:
        """Extracts leg information from a text block."""
        leg_id = find_first(LEG_ID_PATTERN, leg_text)

        facilities = find_all(LEG_FACILITY_PATTERN, leg_text)
        pick_up_facility_id = facilities[0] if facilities else None
        drop_off_facility_id = facilities[1] if len(facilities) > 1 else None

        times = find_all(TRIP_TIME_PATTERN, leg_text)
        pick_up_time_str = times[0] if len(times) > 0 else None
        drop_off_time_str = times[-2] if len(times) > 1 else None
        pick_up_time = parse_datetime_with_tz(times[0]) if len(times) > 0 else None
        drop_off_time = parse_datetime_with_tz(times[-2]) if len(times) >= 2 else None

        price_str = find_first(SIMPLE_PRICE_PATTERN, leg_text)
        fuel_sur_charge = parse_decimal(price_str)

        dist_str = find_first(DISTANCE_PATTERN, leg_text, group=1)
        distance = int(dist_str) if dist_str else None

        addresses = find_all(ADDRESS_PATTERN, leg_text)
        pick_up_address = addresses[0].split("\n")[-1].strip() if addresses else None
        drop_off_address = (
            addresses[1].split("\n")[-1].strip() if len(addresses) > 1 else None
        )

        driver = find_first(DRIVER_PATTERN, leg_text, group=1)
        assigned_driver = driver.strip() if driver else None

        return Leg(
            leg_id=leg_id or "UNKNOWN_LEG_ID",
            pick_up_facility_id=pick_up_facility_id or "UNKNOWN_FACILITY",
            drop_off_facility_id=drop_off_facility_id or "UNKNOWN_FACILITY",
            pick_up_time=pick_up_time or datetime.min,
            drop_off_time=drop_off_time or datetime.min,
            fuel_sur_charge=fuel_sur_charge or Decimal(0.0),
            distance=float(distance) if distance is not None else 0.0,
            pick_up_address=pick_up_address or "UNKNOWN_ADDRESS",
            drop_off_address=drop_off_address or "UNKNOWN_ADDRESS",
            assigned_driver=assigned_driver,
            pick_up_time_str=pick_up_time_str or "UNKNOWN_TIME",
            drop_off_time_str=drop_off_time_str or "UNKNOWN_TIME",
            id=0,  # Temporary ID, will be replaced when saved to database
            load_id=0,  # Temporary load_id, will be replaced when saved to database
        )

    def parse(
        self, input_text: str = None, dispatcher_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main method for parsing text.

        Args:
                input_text (str, optional): Text to parse. If None, uses self.text.

        Returns:
                Dict[str, Any]: Dictionary with trip info and legs
        :param input_text:
                :param dispatcher_id:
        """
        if not self.text and not input_text:
            print("Error: No text provided for parsing.")
            return None

        load_text = self.text if not input_text else input_text
        leg_ids = find_all(LEG_ID_PATTERN, load_text)

        # Determine the split point between trip info and leg blocks
        split_point = -1
        if len(leg_ids) > 1:
            # Find the second occurrence of leg_id
            try:
                # Find the start index of the second leg_id
                split_point = load_text[5:].index(leg_ids[1]) + 5
            except ValueError:
                pass  # Second occurrence not found

        # If second leg_id occurrence not found, look for "Assign driver" as fallback
        if split_point == -1:
            assign_driver_marker = "Assign driver"
            try:
                split_point = load_text.index(assign_driver_marker)
            except ValueError:
                print(
                    "Warning: Could not find a reliable split point (second leg_id or 'Assign driver'). Parsing might be inaccurate."
                )
                # Default: consider all information as trip_info
                split_point = len(load_text)

        trip_info_text = load_text[:split_point]
        legs_text = load_text[split_point:]

        # Split remaining text into blocks by marker
        stops_blocks = legs_text.split(LEG_SPLIT_MARKER)

        trip_info = self._extract_trip_info(
            trip_info_text, full_text=load_text, dispatcher_id=dispatcher_id
        )

        loads = {
            "tripInfo": trip_info.model_dump(),
            "legs": [],
        }

        # First block after splitting may contain info related to the first leg
        first_leg_text = stops_blocks[0]
        # Subsequent blocks definitely start with leg info
        other_legs_text = stops_blocks[1:]

        # Process first leg (if exists)
        # Heuristic: if the first block contains a leg ID, consider it the first leg
        if find_first(LEG_ID_PATTERN, first_leg_text):
            leg = self._extract_leg_info(first_leg_text)
            loads["legs"].append(leg.model_dump())

        # Process remaining blocks
        for stop_block in other_legs_text:
            if stop_block.strip():  # Skip empty blocks
                leg = self._extract_leg_info(
                    f"{LEG_SPLIT_MARKER}\n{stop_block}"
                )  # Add marker back for context
                loads["legs"].append(leg.model_dump())

        self.data = loads  # Save result
        return loads


def get_parsing_service(
    text: str = Body("", description="load text", media_type="text/plain"),
) -> ParsingService:
    """
    Dependency for getting a parsing service instance.

    Args:
            text (str): Text to parse

    Returns:
            ParsingService: Configured parsing service instance
    """
    return ParsingService(text=text)
