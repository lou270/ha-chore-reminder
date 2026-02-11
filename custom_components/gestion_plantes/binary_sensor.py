"""Binary sensor platform for Gestion des Plantes."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up the binary sensor platform."""
    plant_device: PlantDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlantNeedsWaterSensor(plant_device)])


class PlantNeedsWaterSensor(BinarySensorEntity):
    """Representation of a binary sensor that reports if plant needs water."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, plant_device: PlantDevice) -> None:
        """Initialize the binary sensor."""
        self._plant = plant_device
        self._attr_name = f"{plant_device.name} Besoin d'eau"
        self._attr_unique_id = f"{plant_device.entry.entry_id}_needs_water"
        self._attr_device_info = plant_device.device_info

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._plant.add_listener(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        # Device Class Moisture: ON means wet, OFF means dry? 
        # Actually usually: Moisture: Off = dry, On = wet. 
        # Wait, usually moisture sensors are: Wet (On) / Dry (Off).
        # But here we want an alert. 
        # Let's check Device Class Problem: On = problem.
        # Let's use PROBLEM for "Needs Water" = On. 
        # Or Moisture: 
        #   Moisture (default): On means moisture detected (wet), Off means no moisture (dry).
        #   So if we want "Needs Water", it means it is Dry (Off).
        #   But the user wants to see "Needs Water" -> On.
        # Let's stick to PROBLEM or just no device class with custom icon.
        # However, plan said "Moisture".
        # If I use moisture: On = Wet. We want to alert when Dry.
        # So is_on should be True when Wet.
        # So "Needs Water" is actually the opposite of Moisture.
        # Let's use DeviceClass.PROBLEM which is On when problem (Need water).
        return self._plant.needs_water

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return "mdi:water-alert" if self.is_on else "mdi:water-check"
