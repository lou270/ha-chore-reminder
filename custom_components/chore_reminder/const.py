"""Constants for the Chore Reminder integration."""

DOMAIN = "chore_reminder"

# Storage
STORAGE_KEY = f"{DOMAIN}.chores"
STORAGE_VERSION = 1

# Chore fields
CONF_CHORE_ID = "id"
CONF_NAME = "name"
CONF_CATEGORY = "category"
CONF_FREQUENCY = "frequency"
CONF_ICON = "icon"
CONF_NOTES = "notes"
CONF_LAST_COMPLETED = "last_completed"
CONF_COMPLETION_HISTORY = "completion_history"

# Scheduling
CONF_SCHEDULE_TYPE = "schedule_type"
CONF_SCHEDULE_DAYS = "schedule_days"
CONF_ADAPTIVE = "adaptive"

SCHEDULE_TYPE_INTERVAL = "interval"
SCHEDULE_TYPE_WEEKLY = "weekly"
SCHEDULE_TYPE_MONTHLY = "monthly"

# Notifications
CONF_NOTIFY_WHEN_DUE = "notify_when_due"
CONF_NOTIFY_ADVANCE_DAYS = "notify_advance_days"

# Defaults
DEFAULT_FREQUENCY = 7
DEFAULT_ICON = "mdi:broom"
DEFAULT_SCHEDULE_TYPE = SCHEDULE_TYPE_INTERVAL
DEFAULT_NOTIFY_ADVANCE_DAYS = 1
COMPLETION_HISTORY_MAX = 20
