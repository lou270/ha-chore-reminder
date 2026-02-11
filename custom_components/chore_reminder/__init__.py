"""The Chore Reminder integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_FREQUENCY, DEFAULT_FREQUENCY, CONF_ICON

_LOGGER = logging.getLogger(__name__)

from datetime import datetime, timedelta
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Chore Reminder from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create the ChoreEntity instance
    chore_entity = ChoreEntity(hass, entry)
    
    # Store it
    hass.data[DOMAIN][entry.entry_id] = chore_entity

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        pass
        # Pop data if needed
        # hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class ChoreEntity:
    """Class to manage chore state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.listeners = []
        
        # Load state from config entry data, default to now if missing
        last_completed_iso = self.entry.data.get("last_completed")
        if last_completed_iso:
            self._last_completed = dt_util.parse_datetime(last_completed_iso)
        else:
            self._last_completed = dt_util.now()

    @property
    def name(self):
        return self.entry.title

    @property
    def frequency(self):
        return self.entry.data.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)
    
    @property
    def icon(self):
        # Default icon if none provided
        return self.entry.data.get(CONF_ICON) or "mdi:checkbox-marked-circle-outline"

    @property
    def last_completed(self):
        return self._last_completed

    @property
    def days_remaining(self):
        next_due = self._last_completed + timedelta(days=self.frequency)
        diff = next_due - dt_util.now()
        return diff.days

    @property
    def is_due(self):
        return self.days_remaining <= 0

    def complete(self):
        """Mark the chore as completed."""
        self._last_completed = dt_util.now()
        
        # Persist the new date to config entry
        new_data = self.entry.data.copy()
        new_data["last_completed"] = self._last_completed.isoformat()
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
            model="Chore Reminder v1",
        )
