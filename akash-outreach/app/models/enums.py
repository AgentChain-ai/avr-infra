"""
Enums for the Akash Institute Outreach System
"""
from enum import Enum


class CallStatus(str, Enum):
    """Status of a phone call"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    FAILED = "failed"
    CALLBACK_REQUESTED = "callback_requested"
    CANCELLED = "cancelled"


class StudentStatus(str, Enum):
    """Status of a student in the system"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    DROPPED_OUT = "dropped_out"
    ON_HOLD = "on_hold"


class FieldType(str, Enum):
    """Types of configuration fields"""
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"
    TEXTAREA = "textarea"
