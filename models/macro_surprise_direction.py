from enum import Enum


class MacroSurpriseDirection(str, Enum):
    ABOVE_FORECAST = "ABOVE_FORECAST"
    BELOW_FORECAST = "BELOW_FORECAST"
    IN_LINE = "IN_LINE"
    UNKNOWN = "UNKNOWN"
