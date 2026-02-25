"""Button platform for Chore Reminder."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up the button platform."""
    chore_entity: ChoreEntity = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChoreCompleteButton(chore_entity)])

class ChoreCompleteButton(ButtonEntity):
    """Representation of a button to complete the chore."""

    _attr_icon = "mdi:checkbox-marked-circle-outline"
    _attr_has_entity_name = True
    _attr_translation_key = "complete_button"

    def __init__(self, chore_entity: ChoreEntity) -> None:
        """Initialize the button."""
        self._chore = chore_entity
        self._attr_unique_id = f"{chore_entity.entry.entry_id}_complete_button"
        self._attr_device_info = chore_entity.device_info
        if chore_entity.image:
            self._attr_entity_picture = chore_entity.image

    async def async_press(self) -> None:
        """Handle the button press."""
        self._chore.complete()

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        return {
            "last_completed": self._chore.last_completed.isoformat()
        }
