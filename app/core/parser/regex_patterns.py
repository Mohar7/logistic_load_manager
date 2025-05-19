# app/core/parser/regex_patterns.py

# Regular expression patterns for parsing load text
TRIP_ID_PATTERN = r"\bT-[A-Z0-9]{9}\b"
FACILITY_PATTERN = r"\b[A-Z]{3}[A-Z0-9]{1,2}\b"
TRIP_TIME_PATTERN = r"(?:\w{3}, )?\d{1,2} \w{3}, [\d:,]+ [A-Z]{3}"
PRICE_PATTERN = r"\$\d+(?:[ ,]\d+)*(?:[.,]\d+)?"
RPM_PATTERN = r"\$\d+\.\d+/mi"
DISTANCE_PATTERN = r"(\d+)\s*mi"
LEG_ID_PATTERN = r"\b[0-9][A-Z0-9]{8}\b"
LEG_FACILITY_PATTERN = r"\b[A-Z]{3}[A-Z0-9]{1,2}\b"
SIMPLE_PRICE_PATTERN = r"\$\d+[,\.]?\d*"
ADDRESS_LINE_PATTERN = r"^[A-Z0-9]{4}$"  # Not used in current logic?
ADDRESS_PATTERN = r"([A-Za-z\s]+,\s*[A-Z]{2})\s*\d{5}"
DRIVER_PATTERN = r"Assign driver\s*\n(.*)"
LEG_SPLIT_MARKER = "Drop-off instructions"

# Timezone mappings
TIMEZONE_MAP = {
    "EDT": "America/New_York",
    "CDT": "America/Chicago",
    "MDT": "America/Denver",
    "PDT": "America/Los_Angeles",
}
