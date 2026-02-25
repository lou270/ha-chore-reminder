from __future__ import annotations

from datetime import datetime, timedelta, date

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from . import ChoreEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    chore: ChoreEntity = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChoreCalendar(chore)])


class ChoreCalendar(CalendarEntity):
    """Calendar entity for a chore."""

    _attr_has_entity_name = True
    _attr_translation_key = "calendar"

    def __init__(self, chore: ChoreEntity) -> None:
        """Initialize the calendar entity."""
        self.chore = chore
        self._attr_unique_id = f"{self.chore.entry.entry_id}_calendar"
        self._attr_device_info = self.chore.device_info

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        next_due = self.chore.last_completed + timedelta(days=self.chore.frequency)
        # We need the local date 
        start = dt_util.as_local(next_due).date()
        end = start + timedelta(days=1)
        
        return CalendarEvent(
            start=start,
            end=end,
            summary=self.chore.name,
        )

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return calendar events occurring within a specified time window."""
        events = []
        
        start_date_local = dt_util.as_local(start_date).date()
        end_date_local = dt_util.as_local(end_date).date()

        next_due = self.chore.last_completed + timedelta(days=self.chore.frequency)
        current_date = dt_util.as_local(next_due).date()

        # Fast forward if current_date is far in the past compared to start_date_local
        if current_date < start_date_local:
            days_diff = (start_date_local - current_date).days
            periods = days_diff // self.chore.frequency
            if periods > 0:
                current_date += timedelta(days=self.chore.frequency * periods)
        
        # Protect against infinite loop
        max_events = 365 # 1 year max theoretically
        generated = 0
        
        while current_date <= end_date_local and generated < max_events:
            event_end = current_date + timedelta(days=1)
            
            # Check if this occurrence falls within the requested range
            if (current_date >= start_date_local and current_date < end_date_local) or \
               (event_end > start_date_local and current_date <= end_date_local):
                events.append(
                    CalendarEvent(
                        start=current_date,
                        end=event_end,
                        summary=self.chore.name,
                    )
                )
                
            # Move to the next frequency period assuming it's completed exactly on the due date
            current_date += timedelta(days=self.chore.frequency)
            generated += 1

        return events

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.chore.add_listener(self.async_write_ha_state)

