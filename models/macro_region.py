from enum import Enum


class MacroRegion(str, Enum):
    US = "US"
    EU = "EU"
    UK = "UK"
    JP = "JP"
    CN = "CN"
    OTHER = "OTHER"
