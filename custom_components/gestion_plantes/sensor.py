from __future__ import annotations

from typing import Any
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .__init__ import PlantDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    plant_device: PlantDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlantDaysRemainingSensor(plant_device)])


class PlantDaysRemainingSensor(SensorEntity):
    """Representation of a sensor that reports days remaining."""

    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "jours"

    def __init__(self, plant_device: PlantDevice) -> None:
        """Initialize the sensor."""
        self._plant = plant_device
        self._attr_name = f"{plant_device.name} Jours Restants"
        self._attr_unique_id = f"{plant_device.entry.entry_id}_days_remaining"
        self._attr_device_info = plant_device.device_info

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._plant.add_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self._plant.days_remaining

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "last_watered": self._plant.last_watered.isoformat(),
            "next_watering": (self._plant.last_watered + timedelta(days=self._plant.interval)).isoformat(),
        }
