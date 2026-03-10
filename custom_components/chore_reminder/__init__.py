"""The Chore Reminder integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .store import ChoreStore
from .notify import setup_notifications

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TODO, Platform.SENSOR, Platform.CALENDAR]

CARD_JS = "chore-reminder-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_JS}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Chore Reminder component (register Lovelace card)."""
    card_path = Path(__file__).parent / CARD_JS
    if card_path.exists():
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

    # Initialize the store
    store = ChoreStore(hass)
    await store.async_load()
    hass.data[DOMAIN][entry.entry_id] = store

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register daily notifications
    setup_notifications(hass, entry)

    # Reload on options change
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update - reload the entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
