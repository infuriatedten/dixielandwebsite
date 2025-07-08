from enum import Enum

class ConversationStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"

class MarketplaceListingStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
