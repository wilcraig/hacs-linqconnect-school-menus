"""Constants for the LinQ Connect School Menus integration."""
DOMAIN = "linqconnect_school_menus"

# Configuration keys
CONF_MENU_URL = "menu_url"
CONF_BUILDING_ID = "building_id"
CONF_DISTRICT_ID = "district_id"
CONF_DAYS_TO_SHOW = "days_to_show"

# Default values
DEFAULT_DAYS_TO_SHOW = 1
MIN_DAYS_TO_SHOW = 1
MAX_DAYS_TO_SHOW = 7

# Update interval (in minutes)
UPDATE_INTERVAL = 60

# API endpoints
LINQCONNECT_API_BASE_URL = "https://api.linqconnect.com/api/FamilyMenu"
LINQCONNECT_PUBLIC_BASE_URL = "https://linqconnect.com/public/menu"
