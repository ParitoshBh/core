"""Constants for the Canada Post integration."""

DOMAIN = "canada_post"
API_URL = (
    "https://www.canadapost.ca/trackweb/rs/track/json/package/{tracking_number}/detail"
)

ATTRIBUTION = "Information provided by Canada Post"
ATTR_ATTRIBUTION = "attribution"
ATTR_LOCATION_ADDR = "location"
ATTR_DATE = "date"
ATTR_TIME = "time"
ATTR_TIMEZONE = "timezone"

CONF_NAME = "Canada Post"
CONF_TRACKING_NUMBERS = "tracking_numbers"
DEFAULT_TRACKING_NUMBERS = "Tracking Numbers (comma separated)"