"""The Chore Reminder integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_FREQUENCY, DEFAULT_FREQUENCY, CONF_ICON, CONF_IMAGE

_LOGGER = logging.getLogger(__name__)

from datetime import datetime, timedelta
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON, Platform.CALENDAR]

CARD_JS = "chore-reminder-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_JS}"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Chore Reminder component."""
    card_path = Path(__file__).parent / CARD_JS
    from homeassistant.components.http import StaticPathConfig
    from homeassistant.components.frontend import add_extra_js_url
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(card_path), cache_headers=False)]
        )
    except RuntimeError:
        pass  # Route already registered
    add_extra_js_url(hass, CARD_URL)
    _LOGGER.info("Chore Reminder card registered at %s", CARD_URL)
    return True

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
    def image(self):
        return self.entry.data.get(CONF_IMAGE)

    @property
    def last_completed(self):
        return self._last_completed

    @property
    def days_remaining(self):
        next_due = self._last_completed + timedelta(days=self.frequency)
        # Comparer les dates (sans heure) pour un nombre de jours précis
        diff = next_due.date() - dt_util.now().date()
        return diff.days

    @property
    def is_due(self):
        return self.days_remaining <= 0

    def set_last_completed(self, iso_string: str):
        """Restore the chore state."""
        self._last_completed = dt_util.parse_datetime(iso_string)
        self.notify_listeners()

    def complete(self):
        """Mark the chore as completed."""
        self._last_completed = dt_util.now()
        
        # We rely on RestoreSensor to save/restore this state safely
        # Modifying config entry data here caused unexpected reloads.
        
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
