from enum import Enum

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

class ConversationStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"

class MarketplaceListingStatus(Enum):
    AVAILABLE = "AVAILABLE"
    SOLD_PENDIN = "SOLD_PENDING"  # fix spelling exactly as in DB
    SOLD_OUT = "SOLD_OUT"
    CANCELLED = "CANCELLED"




class PermitApplicationStatus(Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
