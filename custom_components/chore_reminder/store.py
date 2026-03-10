"""Persistent storage for Chore Reminder."""
from __future__ import annotations

import uuid
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    STORAGE_KEY,
    STORAGE_VERSION,
    CONF_CHORE_ID,
    CONF_NAME,
    CONF_FREQUENCY,
    CONF_ICON,
    CONF_NOTES,
    CONF_LAST_COMPLETED,
    DEFAULT_ICON,
    DEFAULT_FREQUENCY,
)

_LOGGER = logging.getLogger(__name__)


class ChoreStore:
    """Manages loading and saving chores to persistent storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._chores: list[dict[str, Any]] = []
        self._listeners: list = []

    async def async_load(self) -> None:
        """Load chores from storage."""
        data = await self._store.async_load()
        if data and "chores" in data:
            self._chores = data["chores"]
        else:
            self._chores = []
        _LOGGER.debug("Loaded %d chores", len(self._chores))

    async def async_save(self) -> None:
        """Save chores to storage."""
        await self._store.async_save({"chores": self._chores})
        self._notify_listeners()

    def get_all_chores(self) -> list[dict[str, Any]]:
        """Return all chores sorted by urgency (days remaining ascending)."""
        now = dt_util.now()
        chores_with_remaining = []
        for chore in self._chores:
            days = self._days_remaining(chore, now)
            chores_with_remaining.append((days, chore))
        chores_with_remaining.sort(key=lambda x: x[0])
        return [c for _, c in chores_with_remaining]

    def get_chore(self, chore_id: str) -> dict[str, Any] | None:
        """Return a specific chore by ID."""
        for chore in self._chores:
            if chore[CONF_CHORE_ID] == chore_id:
                return chore
        return None

    def _days_remaining(self, chore: dict[str, Any], now: datetime | None = None) -> int:
        """Compute days remaining for a chore."""
        if now is None:
            now = dt_util.now()
        last_completed = dt_util.parse_datetime(chore.get(CONF_LAST_COMPLETED, ""))
        if last_completed is None:
            return 0
        frequency = chore.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)
        next_due = last_completed.date() + __import__("datetime").timedelta(days=frequency)
        return (next_due - now.date()).days

    def days_remaining(self, chore_id: str) -> int:
        """Return days remaining for a specific chore."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return 0
        return self._days_remaining(chore)

    def next_due_date(self, chore_id: str) -> datetime | None:
        """Return the next due date for a chore as a datetime."""
        from datetime import timedelta
        chore = self.get_chore(chore_id)
        if chore is None:
            return None
        last_completed = dt_util.parse_datetime(chore.get(CONF_LAST_COMPLETED, ""))
        if last_completed is None:
            return None
        frequency = chore.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)
        return last_completed + timedelta(days=frequency)

    async def async_add_chore(
        self,
        name: str,
        frequency: int = DEFAULT_FREQUENCY,
        icon: str = DEFAULT_ICON,
        notes: str = "",
    ) -> dict[str, Any]:
        """Add a new chore and persist."""
        chore: dict[str, Any] = {
            CONF_CHORE_ID: str(uuid.uuid4()),
            CONF_NAME: name,
            CONF_FREQUENCY: frequency,
            CONF_ICON: icon,
            CONF_NOTES: notes,
            CONF_LAST_COMPLETED: dt_util.now().isoformat(),
        }
        self._chores.append(chore)
        await self.async_save()
        return chore

    async def async_update_chore(
        self,
        chore_id: str,
        **kwargs: Any,
    ) -> bool:
        """Update a chore's fields and persist."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return False
        for key, value in kwargs.items():
            chore[key] = value
        await self.async_save()
        return True

    async def async_complete_chore(self, chore_id: str) -> bool:
        """Mark a chore as completed now and persist."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return False
        chore[CONF_LAST_COMPLETED] = dt_util.now().isoformat()
        await self.async_save()
        _LOGGER.info("Chore '%s' completed", chore.get(CONF_NAME))
        return True

    async def async_remove_chore(self, chore_id: str) -> bool:
        """Remove a chore and persist."""
        original_len = len(self._chores)
        self._chores = [c for c in self._chores if c[CONF_CHORE_ID] != chore_id]
        if len(self._chores) == original_len:
            return False
        await self.async_save()
        return True

    def add_listener(self, listener) -> None:
        """Register a listener called on chore data changes."""
        self._listeners.append(listener)

    def remove_listener(self, listener) -> None:
        """Unregister a listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Notify all registered listeners of a data change."""
        for listener in self._listeners:
            try:
                listener()
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Error in chore store listener: %s", err)
