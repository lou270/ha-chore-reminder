"""The Gestion des Plantes integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_WATERING_INTERVAL, DEFAULT_INTERVAL, CONF_IMAGE_URL

_LOGGER = logging.getLogger(__name__)


from datetime import datetime, timedelta
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gestion des Plantes from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create the PlantDevice instance
    plant_device = PlantDevice(hass, entry)
    
    # Store it
    hass.data[DOMAIN][entry.entry_id] = plant_device

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

class PlantDevice:
    """Class to manage plant state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.listeners = []
        
        # Load state from config entry data, default to now if missing
        last_watered_iso = self.entry.data.get("last_watered")
        if last_watered_iso:
            self._last_watered = dt_util.parse_datetime(last_watered_iso)
        else:
            self._last_watered = dt_util.now()

    @property
    def name(self):
        return self.entry.title

    @property
    def interval(self):
        return self.entry.data.get(CONF_WATERING_INTERVAL, DEFAULT_INTERVAL)
    
    @property
    def image_url(self):
        return self.entry.data.get(CONF_IMAGE_URL)

    @property
    def last_watered(self):
        return self._last_watered

    @property
    def days_remaining(self):
        next_water = self._last_watered + timedelta(days=self.interval)
        diff = next_water - dt_util.now()
        return diff.days

    @property
    def needs_water(self):
        return self.days_remaining <= 0

    def water(self):
        """Water the plant."""
        self._last_watered = dt_util.now()
        
        # Persist the new date to config entry
        new_data = self.entry.data.copy()
        new_data["last_watered"] = self._last_watered.isoformat()
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        
        self.notify_listeners()

    def add_listener(self, method):
        self.listeners.append(method)

    def notify_listeners(self):
        for method in self.listeners:
            method()
            
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.name,
            manufacturer="Custom Integration",
            model="Plante v1",
        )
