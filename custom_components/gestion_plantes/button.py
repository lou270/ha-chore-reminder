"""Button platform for Gestion des Plantes."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up the button platform."""
    plant_device: PlantDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlantWaterButton(plant_device)])

class PlantWaterButton(ButtonEntity):
    """Representation of a button to water the plant."""

    _attr_icon = "mdi:watering-can"

    def __init__(self, plant_device: PlantDevice) -> None:
        """Initialize the button."""
        self._plant = plant_device
        self._attr_name = f"{plant_device.name} Arroser"
        self._attr_unique_id = f"{plant_device.entry.entry_id}_water_button"
        self._attr_device_info = plant_device.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        self._plant.water()
