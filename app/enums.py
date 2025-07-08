from enum import Enum

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

class ConversationStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"

class MarketplaceListingStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
    AVAILABLE = "available"  # Only if you really need it
