"""Config flow for Chore Reminder integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_NAME

from .const import DOMAIN, DEFAULT_FREQUENCY, CONF_FREQUENCY, CONF_ICON

_LOGGER = logging.getLogger(__name__)

CHORE_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Required(CONF_FREQUENCY, default=DEFAULT_FREQUENCY): int,
    vol.Optional(CONF_ICON): str,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Chore Reminder."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=CHORE_SCHEMA
            )

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
