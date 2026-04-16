from enum import Enum


class ImageStatus(str, Enum):
    INGESTED = "INGESTED"
    OCR_DONE = "OCR_DONE"
    OCR_FAILED = "OCR_FAILED"
    FINAL_UPDATED = "FINAL_UPDATED"
    FINAL_UPDATED_CHILD = "FINAL_UPDATED_CHILD"
    DROPPED = "DROPPED"


class QualityLevel(str, Enum):
    UNKNOWN = "UNKNOWN"
    NO_PROBLEM = "NO_PROBLEM"
    OCR_LOW = "OCR_LOW"
    LOW = "LOW"


class IntegrityStatus(str, Enum):
    OK = "OK"
    NO_APPROACH = "NO_APPROACH"
    IGNORED = "IGNORED"
    SUSPECTED_MISSING = "SUSPECTED_MISSING"
    MISSING = "MISSING"
    PURGED = "PURGED"
