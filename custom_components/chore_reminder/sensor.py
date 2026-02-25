"""Sensor platform for Chore Reminder."""
from __future__ import annotations

from typing import Any
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, RestoreSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .__init__ import ChoreEntity

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    chore_entity: ChoreEntity = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChoreDaysRemainingSensor(chore_entity)])


class ChoreDaysRemainingSensor(RestoreSensor):
    """Representation of a sensor that reports days remaining."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "jours"
    _attr_has_entity_name = True
    _attr_translation_key = "days_remaining"

    def __init__(self, chore_entity: ChoreEntity) -> None:
        """Initialize the sensor."""
        self._chore = chore_entity
        self._attr_unique_id = f"{chore_entity.entry.entry_id}_days_remaining"
        self._attr_device_info = chore_entity.device_info
        if chore_entity.image:
            self._attr_entity_picture = chore_entity.image

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        await super().async_added_to_hass()
        self._chore.add_listener(self.async_write_ha_state)

        # Restore previous state
        last_state = await self.async_get_last_state()
        if last_state and "last_completed" in last_state.attributes:
            try:
                self._chore.set_last_completed(last_state.attributes["last_completed"])
            except Exception:
                pass

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self._chore.days_remaining

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "last_completed": self._chore.last_completed.isoformat(),
            "next_due": (self._chore.last_completed + timedelta(days=self._chore.frequency)).isoformat(),
        }
