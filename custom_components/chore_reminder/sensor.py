"""Sensor platform for Chore Reminder — global urgency + per-chore stats."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_ICON,
    CONF_CHORE_ID,
    CONF_CATEGORY,
    DEFAULT_ICON,
)
from .store import ChoreStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    store: ChoreStore = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ChoreNextSensor(store, entry),
        ChoreOverdueSensor(store, entry),
    ])


class ChoreNextSensor(SensorEntity):
    """Sensor for the most urgent upcoming chore."""

    _attr_has_entity_name = True
    _attr_translation_key = "next_chore"
    _attr_icon = "mdi:clock-alert-outline"
    _attr_native_unit_of_measurement = "jours"

    def __init__(self, store: ChoreStore, entry: ConfigEntry) -> None:
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_next_chore"

    async def async_added_to_hass(self) -> None:
        self._store.add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        self._store.remove_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> int | None:
        chores = self._store.get_all_chores()
        if not chores:
            return None
        return self._store.days_remaining(chores[0][CONF_CHORE_ID])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        chores = self._store.get_all_chores()
        if not chores:
            return {}
        most_urgent = chores[0]
        chore_id = most_urgent[CONF_CHORE_ID]
        next_due = self._store.next_due_date(chore_id)
        overdue = self._store.get_overdue_chores()
        return {
            "chore_name": most_urgent.get(CONF_NAME, ""),
            "chore_icon": most_urgent.get(CONF_ICON, DEFAULT_ICON),
            "chore_category": most_urgent.get(CONF_CATEGORY, ""),
            "next_due": next_due.isoformat() if next_due else None,
            "days_remaining": self._store.days_remaining(chore_id),
            "total_chores": len(chores),
            "overdue_count": len(overdue),
            "categories": self._store.get_all_categories(),
        }


class ChoreOverdueSensor(SensorEntity):
    """Sensor counting overdue chores."""

    _attr_has_entity_name = True
    _attr_translation_key = "overdue_count"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_native_unit_of_measurement = "tâches"

    def __init__(self, store: ChoreStore, entry: ConfigEntry) -> None:
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_overdue_count"

    async def async_added_to_hass(self) -> None:
        self._store.add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        self._store.remove_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> int:
        return len(self._store.get_overdue_chores())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        overdue = self._store.get_overdue_chores()
        return {
            "overdue_chores": [
                {
                    "name": c.get(CONF_NAME, ""),
                    "days_overdue": abs(self._store.days_remaining(c[CONF_CHORE_ID])),
                    "category": c.get(CONF_CATEGORY, ""),
                }
                for c in overdue
            ]
        }
