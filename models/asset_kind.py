from enum import Enum


class AssetKind(str, Enum):
    """
    Broad categories for company assets used across industries.

    Detailed sector-specific classification belongs in Asset.subtype,
    not in this enum.
    """

    PRODUCT = "product"
    SERVICE = "service"
    PLATFORM = "platform"
    TECHNOLOGY = "technology"
    SOFTWARE = "software"
    DRUG = "drug"
    MEDICAL_DEVICE = "medical_device"
    PROGRAM = "program"
    PROJECT = "project"
    FACILITY = "facility"
    RESOURCE = "resource"
    MEDIA = "media"
    FINANCIAL_PRODUCT = "financial_product"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    OTHER = "other"