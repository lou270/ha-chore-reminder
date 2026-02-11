"""Binary sensor platform for Chore Reminder."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up the binary sensor platform."""
    chore_entity: ChoreEntity = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChoreDueSensor(chore_entity)])


class ChoreDueSensor(BinarySensorEntity):
    """Representation of a binary sensor that reports if chore is due."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, chore_entity: ChoreEntity) -> None:
        """Initialize the binary sensor."""
        self._chore = chore_entity
        self._attr_name = f"{chore_entity.name} À faire"
        self._attr_unique_id = f"{chore_entity.entry.entry_id}_due"
        self._attr_device_info = chore_entity.device_info

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._chore.add_listener(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (Problem/Due)."""
        return self._chore.is_due

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        # Use the configured icon if due, or a checkmark if done? 
        # Or just use the configured icon always?
        # Let's use specific icons for states.
        return "mdi:alert-circle" if self.is_on else "mdi:check-circle"
