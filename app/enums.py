from enum import Enum

class UserRole(Enum):
    USER = "user"
    OFFICER = "officer"
    ADMIN = "admin"



class MarketplaceListingStatus(Enum):
    AVAILABLE = "AVAILABLE"
    SOLD_PENDING = "SOLD_PENDING"
    SOLD_OUT = "SOLD_OUT"
    CANCELLED = "CANCELLED"

class NotificationType(Enum):
    GENERAL_INFO = "GENERAL_INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"

class PermitApplicationStatus(Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
