# This file makes the services directory a Python package.
# It can also be used to selectively expose functions if desired,
# though direct imports from the service modules are also common.

# Example of selective exposure (optional):
# from .messaging_service import get_user_conversations, send_reply, start_conversation
# from .notification_service import create_notification, get_notifications_for_user, get_unread_notification_count
# from .vehicle_service import register_vehicle_for_user, get_user_vehicles, generate_license_plate

# If not doing selective exposure, this file can remain empty.
# Routes will typically do: from app.services.messaging_service import ...
# Or if a service is very commonly used, it could be imported into the main app package's __init__.
```
