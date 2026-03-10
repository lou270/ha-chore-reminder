"""Calendar platform for Chore Reminder - shows all upcoming chore events."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_NAME, CONF_CHORE_ID, CONF_ICON, CONF_NOTES, CONF_FREQUENCY
from .store import ChoreStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the calendar platform."""
    store: ChoreStore = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChoreCalendarEntity(store, entry)])


class ChoreCalendarEntity(CalendarEntity):
    """Calendar entity showing all upcoming chore events."""

    _attr_has_entity_name = True
    _attr_translation_key = "chore_calendar"
    _attr_icon = "mdi:calendar-check"

    def __init__(self, store: ChoreStore, entry: ConfigEntry) -> None:
        """Initialize the calendar."""
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    async def async_added_to_hass(self) -> None:
        """Register listener."""
        self._store.add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Deregister listener."""
        self._store.remove_listener(self.async_write_ha_state)

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event (most urgent chore)."""
        chores = self._store.get_all_chores()
        if not chores:
            return None
        next_chore = chores[0]
        chore_id = next_chore[CONF_CHORE_ID]
        next_due = self._store.next_due_date(chore_id)
        if next_due is None:
            return None
        due_date = next_due.date()
        return CalendarEvent(
            start=due_date,
            end=due_date + timedelta(days=1),
            summary=next_chore.get(CONF_NAME, ""),
            description=next_chore.get(CONF_NOTES, ""),
        )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return all chore events in the requested range."""
        events: list[CalendarEvent] = []
        chores = self._store.get_all_chores()

        for chore in chores:
            chore_id = chore[CONF_CHORE_ID]
            frequency = chore.get(CONF_FREQUENCY, 7)
            name = chore.get(CONF_NAME, "")
            notes = chore.get(CONF_NOTES, "")

            # Generate recurring events up to 1 year from start_date
            next_due = self._store.next_due_date(chore_id)
            if next_due is None:
                continue

            event_date = next_due.date()
            limit = start_date.date() + timedelta(days=365)
            end_limit = min(end_date.date(), limit)

            # Advance to start_date window
            while event_date < start_date.date():
                event_date += timedelta(days=frequency)

            while event_date <= end_limit:
                events.append(
                    CalendarEvent(
                        start=event_date,
                        end=event_date + timedelta(days=1),
                        summary=name,
                        description=notes,
                    )
                )
                event_date += timedelta(days=frequency)

        return events
