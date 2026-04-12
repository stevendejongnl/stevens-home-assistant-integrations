"""Constants for the DWMP integration."""

DOMAIN = "dwmp"

CONF_URL = "url"
CONF_TOKEN = "token"
CONF_PASSWORD = "password"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

TRACKING_STATUSES = [
    "unknown",
    "pre_transit",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "failed_attempt",
    "returned",
    "exception",
]

ACTIVE_STATUSES = {"unknown", "pre_transit", "in_transit", "out_for_delivery", "failed_attempt", "exception"}
DELIVERED_STATUSES = {"delivered", "returned"}
