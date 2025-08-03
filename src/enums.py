from enum import Enum

class ParkingStatus(Enum):
    """Enum for parking space status"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    UNKNOWN = "unknown"

class CameraStatus(Enum):
    """Enum for camera operational status"""
    WORKING = "working"
    NOT_WORKING = "not_working"
    ERROR = "error"
