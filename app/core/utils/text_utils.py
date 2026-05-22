# app/core/utils/text_utils.py
import re
from decimal import Decimal, InvalidOperation


def find_first(pattern: str, text: str, group: int = 0) -> str | None:
    """
    Helper method to find the first match of a regex pattern.

    Args:
        pattern (str): Regex pattern to search for
        text (str): Text to search in
        group (int): Group to return from match

    Returns:
        str or None: Matched string or None if no match
    """
    match = re.search(pattern, text)
    if match:
        try:
            return match.group(group)
        except IndexError:
            return None
    return None


def find_all(pattern: str, text: str, group: int = 0) -> list[str]:
    """
    Helper method to find all matches of a regex pattern.

    Args:
        pattern (str): Regex pattern to search for
        text (str): Text to search in
        group (int): Group to return from matches

    Returns:
        List[str]: List of matched strings
    """
    return re.findall(pattern, text)


def parse_decimal(value: str | None, replacements: dict | None = None) -> Decimal | None:
    """
    Helper method to parse Decimal values.

    Args:
        value (str): String representation of decimal value
        replacements (dict): Dictionary of replacements to clean the string

    Returns:
        Decimal or None: Parsed decimal value or None if parsing fails
    """
    if value is None:
        return None
    if replacements is None:
        replacements = {"$": "", " ": "", ",": ".", "/mi": ""}

    cleaned_value = value
    for old, new in replacements.items():
        cleaned_value = cleaned_value.replace(old, new)

    try:
        return Decimal(cleaned_value)
    except InvalidOperation:
        # Could add error logging or other handling
        return None
