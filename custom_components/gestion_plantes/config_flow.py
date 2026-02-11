"""Config flow for Gestion des Plantes integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_NAME

from .const import DOMAIN, DEFAULT_INTERVAL, CONF_WATERING_INTERVAL, CONF_IMAGE_URL

_LOGGER = logging.getLogger(__name__)

PLANT_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Required(CONF_WATERING_INTERVAL, default=DEFAULT_INTERVAL): int,
    vol.Optional(CONF_IMAGE_URL): str,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gestion des Plantes."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=PLANT_SCHEMA
            )

        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
