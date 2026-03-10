"""Sensor platform for Chore Reminder - shows the most urgent upcoming chore."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_NAME, CONF_ICON, CONF_CHORE_ID, DEFAULT_ICON
from .store import ChoreStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    store: ChoreStore = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChoreNextSensor(store, entry)])


class ChoreNextSensor(SensorEntity):
    """Sensor representing the most urgent upcoming chore."""

    _attr_has_entity_name = True
    _attr_translation_key = "next_chore"
    _attr_icon = "mdi:clock-alert-outline"
    _attr_native_unit_of_measurement = "jours"

    def __init__(self, store: ChoreStore, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_next_chore"

    async def async_added_to_hass(self) -> None:
        """Register listener."""
        self._store.add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Deregister listener."""
        self._store.remove_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> int | None:
        """Return days remaining for the most urgent chore."""
        chores = self._store.get_all_chores()
        if not chores:
            return None
        most_urgent = chores[0]
        return self._store.days_remaining(most_urgent[CONF_CHORE_ID])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes with details of the most urgent chore."""
        chores = self._store.get_all_chores()
        if not chores:
            return {}
        most_urgent = chores[0]
        chore_id = most_urgent[CONF_CHORE_ID]
        next_due = self._store.next_due_date(chore_id)
        return {
            "chore_name": most_urgent.get(CONF_NAME, ""),
            "chore_icon": most_urgent.get(CONF_ICON, DEFAULT_ICON),
            "next_due": next_due.isoformat() if next_due else None,
            "days_remaining": self._store.days_remaining(chore_id),
            "total_chores": len(chores),
            "overdue_count": sum(
                1 for c in chores if self._store.days_remaining(c[CONF_CHORE_ID]) < 0
            ),
        }
