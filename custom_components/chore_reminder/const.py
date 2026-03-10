"""Constants for the Chore Reminder integration."""

DOMAIN = "chore_reminder"

# Storage
STORAGE_KEY = f"{DOMAIN}.chores"
STORAGE_VERSION = 1

# Chore fields
CONF_CHORE_ID = "id"
CONF_NAME = "name"
CONF_FREQUENCY = "frequency"
CONF_ICON = "icon"
CONF_NOTES = "notes"
CONF_LAST_COMPLETED = "last_completed"

# Defaults
DEFAULT_FREQUENCY = 7
DEFAULT_ICON = "mdi:broom"
