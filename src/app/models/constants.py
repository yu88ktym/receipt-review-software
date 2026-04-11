from enum import Enum


class ImageStatus(str, Enum):
    INGESTED = "INGESTED"
    OCR_DONE = "OCR_DONE"
    FINAL_UPDATED = "FINAL_UPDATED"
    DROPPED = "DROPPED"
    NOT_RECEIPT_SUSPECT = "NOT_RECEIPT_SUSPECT"


class QualityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNSET = "UNSET"


class IntegrityStatus(str, Enum):
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"
    UNSET = "UNSET"
