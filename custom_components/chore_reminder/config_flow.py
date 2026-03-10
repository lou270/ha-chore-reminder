"""Config flow for Chore Reminder integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_FREQUENCY,
    CONF_ICON,
    CONF_NOTES,
    CONF_CHORE_ID,
    DEFAULT_FREQUENCY,
    DEFAULT_ICON,
)
from .store import ChoreStore

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Chore Reminder."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Initial installation - only one instance allowed."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Chore Reminder", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return ChoreOptionsFlow(config_entry)


class ChoreOptionsFlow(config_entries.OptionsFlow):
    """Handle options: add / edit / delete chores."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._selected_chore_id: str | None = None

    def _get_store(self) -> ChoreStore:
        return self.hass.data[DOMAIN][self._config_entry.entry_id]

    # ── Main menu ──────────────────────────────────────────────────────────────

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show main menu: add / edit / delete."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_chore", "edit_chore", "delete_chore"],
        )

    # ── Add ───────────────────────────────────────────────────────────────────

    async def async_step_add_chore(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new chore."""
        if user_input is not None:
            store = self._get_store()
            await store.async_add_chore(
                name=user_input[CONF_NAME],
                frequency=user_input.get(CONF_FREQUENCY, DEFAULT_FREQUENCY),
                icon=user_input.get(CONF_ICON, DEFAULT_ICON) or DEFAULT_ICON,
                notes=user_input.get(CONF_NOTES, ""),
            )
            return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_FREQUENCY, default=DEFAULT_FREQUENCY): vol.All(int, vol.Range(min=1)),
            vol.Optional(CONF_ICON, default=DEFAULT_ICON): str,
            vol.Optional(CONF_NOTES, default=""): str,
        })
        return self.async_show_form(step_id="add_chore", data_schema=schema)

    # ── Edit ──────────────────────────────────────────────────────────────────

    async def async_step_edit_chore(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select which chore to edit."""
        store = self._get_store()
        chores = store.get_all_chores()

        if not chores:
            return self.async_abort(reason="no_chores")

        if user_input is not None:
            self._selected_chore_id = user_input[CONF_CHORE_ID]
            return await self.async_step_edit_chore_details()

        options = {c[CONF_CHORE_ID]: c[CONF_NAME] for c in chores}
        schema = vol.Schema({vol.Required(CONF_CHORE_ID): vol.In(options)})
        return self.async_show_form(step_id="edit_chore", data_schema=schema)

    async def async_step_edit_chore_details(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit the selected chore's details."""
        store = self._get_store()
        chore = store.get_chore(self._selected_chore_id)
        if chore is None:
            return self.async_abort(reason="chore_not_found")

        if user_input is not None:
            await store.async_update_chore(
                self._selected_chore_id,
                **{
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_FREQUENCY: user_input[CONF_FREQUENCY],
                    CONF_ICON: user_input.get(CONF_ICON, DEFAULT_ICON) or DEFAULT_ICON,
                    CONF_NOTES: user_input.get(CONF_NOTES, ""),
                }
            )
            return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Required(CONF_NAME, default=chore.get(CONF_NAME, "")): str,
            vol.Required(CONF_FREQUENCY, default=chore.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)): vol.All(int, vol.Range(min=1)),
            vol.Optional(CONF_ICON, default=chore.get(CONF_ICON, DEFAULT_ICON)): str,
            vol.Optional(CONF_NOTES, default=chore.get(CONF_NOTES, "")): str,
        })
        return self.async_show_form(step_id="edit_chore_details", data_schema=schema)

    # ── Delete ────────────────────────────────────────────────────────────────

    async def async_step_delete_chore(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select which chore to delete."""
        store = self._get_store()
        chores = store.get_all_chores()

        if not chores:
            return self.async_abort(reason="no_chores")

        if user_input is not None:
            await store.async_remove_chore(user_input[CONF_CHORE_ID])
            return self.async_create_entry(title="", data={})

        options = {c[CONF_CHORE_ID]: c[CONF_NAME] for c in chores}
        schema = vol.Schema({vol.Required(CONF_CHORE_ID): vol.In(options)})
        return self.async_show_form(step_id="delete_chore", data_schema=schema)
