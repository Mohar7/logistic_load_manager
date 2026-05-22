# app/core/utils/date_utils.py
import logging
import re
from datetime import datetime

from dateutil import tz

from app.core.parser.regex_patterns import TIMEZONE_MAP

logger = logging.getLogger(__name__)


def parse_datetime_with_tz(date_str: str | None) -> datetime | None:
    """
    Parses a string with date and time, adding timezone information.

    Args:
        date_str: Date string to parse.

    Returns:
        Timezone-aware datetime object, or None if parsing fails.
    """
    if not date_str:
        return None

    match = re.search(r"\b(EDT|CDT|MDT|PDT)\b", date_str)
    if not match:
        logger.warning("Unknown or missing timezone in: %s", date_str)
        return None

    tz_abbr = match.group(1)
    tz_name = TIMEZONE_MAP.get(tz_abbr)
    if not tz_name:
        logger.warning("Timezone abbreviation '%s' not found in map.", tz_abbr)
        return None

    clean_date_str = date_str.replace(tz_abbr, "").strip()
    # Remove day of week if present
    clean_date_str = re.sub(r"^\w{3},\s*", "", clean_date_str)

    try:
        # Format: "19 Apr, 09:04"
        naive_dt = datetime.strptime(clean_date_str, "%d %b, %H:%M")
    except ValueError:
        logger.warning("Could not parse date string: %s", clean_date_str)
        return None

    current_year = datetime.now().year
    correct_dt = naive_dt.replace(year=current_year)

    local_tz = tz.gettz(tz_name)
    if not local_tz:
        logger.warning("Could not get timezone info for: %s", tz_name)
        return None

    return correct_dt.replace(tzinfo=local_tz)
