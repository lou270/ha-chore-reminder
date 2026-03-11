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
    CONF_CATEGORY,
    CONF_FREQUENCY,
    CONF_ICON,
    CONF_NOTES,
    CONF_CHORE_ID,
    CONF_SCHEDULE_TYPE,
    CONF_SCHEDULE_DAYS,
    CONF_ADAPTIVE,
    CONF_NOTIFY_WHEN_DUE,
    CONF_NOTIFY_ADVANCE_DAYS,
    DEFAULT_FREQUENCY,
    DEFAULT_ICON,
    DEFAULT_SCHEDULE_TYPE,
    DEFAULT_NOTIFY_ADVANCE_DAYS,
    SCHEDULE_TYPE_INTERVAL,
    SCHEDULE_TYPE_WEEKLY,
    SCHEDULE_TYPE_MONTHLY,
)
from .store import ChoreStore

_LOGGER = logging.getLogger(__name__)

WEEKDAYS = {
    "0": "Lundi",
    "1": "Mardi",
    "2": "Mercredi",
    "3": "Jeudi",
    "4": "Vendredi",
    "5": "Samedi",
    "6": "Dimanche",
}

def _days_to_str(days: list[int]) -> str:
    """Convert a list of day numbers to a comma-separated string."""
    return ", ".join(str(d) for d in days)


def _str_to_days(s: str) -> list[int]:
    """Parse a comma-separated string of numbers to a list of ints."""
    result = []
    for part in s.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


def _chore_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the chore add/edit schema with optional defaults."""
    d = defaults or {}
    schedule_type = d.get(CONF_SCHEDULE_TYPE, DEFAULT_SCHEDULE_TYPE)
    # schedule_days is stored as list[int] but shown as a comma-separated string
    raw_days = d.get(CONF_SCHEDULE_DAYS, [])
    days_default = _days_to_str(raw_days) if isinstance(raw_days, list) else str(raw_days)
    return vol.Schema({
        vol.Required(CONF_NAME, default=d.get(CONF_NAME, "")): str,
        vol.Optional(CONF_CATEGORY, default=d.get(CONF_CATEGORY, "")): str,
        vol.Required(CONF_SCHEDULE_TYPE, default=schedule_type): vol.In([
            SCHEDULE_TYPE_INTERVAL,
            SCHEDULE_TYPE_WEEKLY,
            SCHEDULE_TYPE_MONTHLY,
        ]),
        vol.Optional(CONF_FREQUENCY, default=d.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)): vol.All(int, vol.Range(min=1)),
        vol.Optional(CONF_SCHEDULE_DAYS, default=days_default): str,
        vol.Optional(CONF_ADAPTIVE, default=d.get(CONF_ADAPTIVE, False)): bool,
        vol.Optional(CONF_ICON, default=d.get(CONF_ICON, DEFAULT_ICON)): str,
        vol.Optional(CONF_NOTES, default=d.get(CONF_NOTES, "")): str,
        vol.Optional(CONF_NOTIFY_WHEN_DUE, default=d.get(CONF_NOTIFY_WHEN_DUE, False)): bool,
        vol.Optional(CONF_NOTIFY_ADVANCE_DAYS, default=d.get(CONF_NOTIFY_ADVANCE_DAYS, DEFAULT_NOTIFY_ADVANCE_DAYS)): vol.All(int, vol.Range(min=0, max=30)),
    }, extra=vol.REMOVE_EXTRA)


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
        return ChoreOptionsFlow()


class ChoreOptionsFlow(config_entries.OptionsFlow):
    """Handle options: add / edit / delete chores."""

    _selected_chore_id: str | None = None

    def _get_store(self) -> ChoreStore:
        return self.hass.data[DOMAIN][self.config_entry.entry_id]

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
            schedule_days = _str_to_days(user_input.get(CONF_SCHEDULE_DAYS, ""))

            await store.async_add_chore(
                name=user_input[CONF_NAME],
                category=user_input.get(CONF_CATEGORY, ""),
                frequency=user_input.get(CONF_FREQUENCY, DEFAULT_FREQUENCY),
                icon=user_input.get(CONF_ICON, DEFAULT_ICON) or DEFAULT_ICON,
                notes=user_input.get(CONF_NOTES, ""),
                schedule_type=user_input.get(CONF_SCHEDULE_TYPE, DEFAULT_SCHEDULE_TYPE),
                schedule_days=schedule_days,
                adaptive=user_input.get(CONF_ADAPTIVE, False),
                notify_when_due=user_input.get(CONF_NOTIFY_WHEN_DUE, False),
                notify_advance_days=user_input.get(CONF_NOTIFY_ADVANCE_DAYS, DEFAULT_NOTIFY_ADVANCE_DAYS),
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_chore",
            data_schema=_chore_schema(),
        )

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
            schedule_days = _str_to_days(user_input.get(CONF_SCHEDULE_DAYS, ""))

            await store.async_update_chore(
                self._selected_chore_id,
                **{
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_CATEGORY: user_input.get(CONF_CATEGORY, ""),
                    CONF_FREQUENCY: user_input.get(CONF_FREQUENCY, DEFAULT_FREQUENCY),
                    CONF_ICON: user_input.get(CONF_ICON, DEFAULT_ICON) or DEFAULT_ICON,
                    CONF_NOTES: user_input.get(CONF_NOTES, ""),
                    CONF_SCHEDULE_TYPE: user_input.get(CONF_SCHEDULE_TYPE, DEFAULT_SCHEDULE_TYPE),
                    CONF_SCHEDULE_DAYS: schedule_days,
                    CONF_ADAPTIVE: user_input.get(CONF_ADAPTIVE, False),
                    CONF_NOTIFY_WHEN_DUE: user_input.get(CONF_NOTIFY_WHEN_DUE, False),
                    CONF_NOTIFY_ADVANCE_DAYS: user_input.get(CONF_NOTIFY_ADVANCE_DAYS, DEFAULT_NOTIFY_ADVANCE_DAYS),
                }
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="edit_chore_details",
            data_schema=_chore_schema(chore),
        )

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
