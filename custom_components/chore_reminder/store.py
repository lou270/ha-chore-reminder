"""Persistent storage for Chore Reminder."""
from __future__ import annotations

import uuid
import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    STORAGE_KEY,
    STORAGE_VERSION,
    CONF_CHORE_ID,
    CONF_NAME,
    CONF_CATEGORY,
    CONF_FREQUENCY,
    CONF_ICON,
    CONF_NOTES,
    CONF_LAST_COMPLETED,
    CONF_COMPLETION_HISTORY,
    CONF_SCHEDULE_TYPE,
    CONF_SCHEDULE_DAYS,
    CONF_ADAPTIVE,
    CONF_NOTIFY_WHEN_DUE,
    CONF_NOTIFY_ADVANCE_DAYS,
    SCHEDULE_TYPE_INTERVAL,
    SCHEDULE_TYPE_WEEKLY,
    SCHEDULE_TYPE_MONTHLY,
    DEFAULT_ICON,
    DEFAULT_FREQUENCY,
    DEFAULT_SCHEDULE_TYPE,
    DEFAULT_NOTIFY_ADVANCE_DAYS,
    COMPLETION_HISTORY_MAX,
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
            self._chores = [self._migrate_chore(c) for c in data["chores"]]
        else:
            self._chores = []
        _LOGGER.debug("Loaded %d chores", len(self._chores))

    def _migrate_chore(self, chore: dict[str, Any]) -> dict[str, Any]:
        """Ensure old chore entries have all new fields."""
        chore.setdefault(CONF_CATEGORY, "")
        chore.setdefault(CONF_SCHEDULE_TYPE, SCHEDULE_TYPE_INTERVAL)
        chore.setdefault(CONF_SCHEDULE_DAYS, [])
        chore.setdefault(CONF_ADAPTIVE, False)
        chore.setdefault(CONF_COMPLETION_HISTORY, [])
        chore.setdefault(CONF_NOTIFY_WHEN_DUE, False)
        chore.setdefault(CONF_NOTIFY_ADVANCE_DAYS, DEFAULT_NOTIFY_ADVANCE_DAYS)
        return chore

    async def async_save(self) -> None:
        """Save chores to storage."""
        await self._store.async_save({"chores": self._chores})
        self._notify_listeners()

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_all_chores(self) -> list[dict[str, Any]]:
        """Return all chores sorted by urgency (days remaining ascending)."""
        now = dt_util.now()
        return sorted(
            self._chores,
            key=lambda c: self._days_remaining(c, now)
        )

    def get_all_categories(self) -> list[str]:
        """Return sorted list of unique non-empty categories."""
        return sorted({c.get(CONF_CATEGORY, "") for c in self._chores if c.get(CONF_CATEGORY)})

    def get_chore(self, chore_id: str) -> dict[str, Any] | None:
        """Return a specific chore by ID."""
        for chore in self._chores:
            if chore[CONF_CHORE_ID] == chore_id:
                return chore
        return None

    def get_chores_by_category(self, category: str) -> list[dict[str, Any]]:
        """Return all chores in a given category."""
        return [c for c in self.get_all_chores() if c.get(CONF_CATEGORY, "") == category]

    # ── Scheduling ────────────────────────────────────────────────────────────

    def _effective_frequency(self, chore: dict[str, Any]) -> int:
        """Return the effective frequency (adaptive or configured)."""
        if chore.get(CONF_ADAPTIVE):
            adaptive = self.adaptive_frequency(chore)
            if adaptive is not None:
                return adaptive
        return chore.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)

    def adaptive_frequency(self, chore: dict[str, Any]) -> int | None:
        """Compute median interval from completion history. Returns None if insufficient data."""
        history = chore.get(CONF_COMPLETION_HISTORY, [])
        if len(history) < 2:
            return None
        dates = sorted([dt_util.parse_datetime(d).date() for d in history if dt_util.parse_datetime(d)])
        if len(dates) < 2:
            return None
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        intervals.sort()
        median = intervals[len(intervals) // 2]
        return max(1, median)

    def _next_due_from(self, chore: dict[str, Any], from_date: date) -> date:
        """Compute the next due date from a given date based on schedule_type."""
        schedule_type = chore.get(CONF_SCHEDULE_TYPE, SCHEDULE_TYPE_INTERVAL)
        schedule_days = chore.get(CONF_SCHEDULE_DAYS, [])
        frequency = self._effective_frequency(chore)

        if schedule_type == SCHEDULE_TYPE_WEEKLY and schedule_days:
            # Find the next occurrence of any listed weekday (0=Mon, 6=Sun)
            for offset in range(1, 15):
                candidate = from_date + timedelta(days=offset)
                if candidate.weekday() in schedule_days:
                    return candidate
            return from_date + timedelta(days=7)

        elif schedule_type == SCHEDULE_TYPE_MONTHLY and schedule_days:
            # Next occurrence of the listed day-of-month
            target_day = schedule_days[0]
            # Try this month first, then next month
            for months_ahead in range(0, 3):
                year = from_date.year + (from_date.month + months_ahead - 1) // 12
                month = (from_date.month + months_ahead - 1) % 12 + 1
                try:
                    candidate = date(year, month, target_day)
                    if candidate > from_date:
                        return candidate
                except ValueError:
                    continue
            return from_date + timedelta(days=30)

        else:
            # Default: interval
            return from_date + timedelta(days=frequency)

    def _days_remaining(self, chore: dict[str, Any], now: datetime | None = None) -> int:
        """Compute days remaining for a chore."""
        if now is None:
            now = dt_util.now()
        last_completed = dt_util.parse_datetime(chore.get(CONF_LAST_COMPLETED, ""))
        if last_completed is None:
            return 0
        next_due = self._next_due_from(chore, last_completed.date())
        return (next_due - now.date()).days

    def days_remaining(self, chore_id: str) -> int:
        """Return days remaining for a specific chore."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return 0
        return self._days_remaining(chore)

    def next_due_date(self, chore_id: str) -> datetime | None:
        """Return the next due date for a chore as a datetime."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return None
        last_completed = dt_util.parse_datetime(chore.get(CONF_LAST_COMPLETED, ""))
        if last_completed is None:
            return None
        due_date = self._next_due_from(chore, last_completed.date())
        return dt_util.start_of_local_day(
            datetime(due_date.year, due_date.month, due_date.day)
        )

    def get_overdue_chores(self) -> list[dict[str, Any]]:
        """Return chores that are overdue (days_remaining < 0)."""
        return [c for c in self._chores if self._days_remaining(c) < 0]

    def get_due_soon_chores(self, advance_days: int) -> list[dict[str, Any]]:
        """Return chores due within advance_days."""
        return [c for c in self._chores if self._days_remaining(c) <= advance_days]

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self, chore_id: str) -> dict[str, Any]:
        """Compute statistics for a chore."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return {}
        history = chore.get(CONF_COMPLETION_HISTORY, [])
        frequency = chore.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)

        avg_interval: float | None = None
        on_time_rate: float | None = None
        intervals: list[int] = []

        if len(history) >= 2:
            dates = sorted([dt_util.parse_datetime(d).date() for d in history if dt_util.parse_datetime(d)])
            intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
            avg_interval = sum(intervals) / len(intervals)
            on_time = sum(1 for iv in intervals if iv <= frequency * 1.1)
            on_time_rate = round(on_time / len(intervals) * 100, 1)

        return {
            "completion_count": len(history),
            "average_interval": round(avg_interval, 1) if avg_interval else None,
            "adaptive_frequency": self.adaptive_frequency(chore),
            "on_time_rate": on_time_rate,
            "history": history[-10:],  # last 10
        }

    # ── Write ─────────────────────────────────────────────────────────────────

    async def async_add_chore(
        self,
        name: str,
        frequency: int = DEFAULT_FREQUENCY,
        icon: str = DEFAULT_ICON,
        notes: str = "",
        category: str = "",
        schedule_type: str = DEFAULT_SCHEDULE_TYPE,
        schedule_days: list[int] | None = None,
        adaptive: bool = False,
        notify_when_due: bool = False,
        notify_advance_days: int = DEFAULT_NOTIFY_ADVANCE_DAYS,
    ) -> dict[str, Any]:
        """Add a new chore and persist."""
        chore: dict[str, Any] = {
            CONF_CHORE_ID: str(uuid.uuid4()),
            CONF_NAME: name,
            CONF_CATEGORY: category,
            CONF_FREQUENCY: frequency,
            CONF_ICON: icon,
            CONF_NOTES: notes,
            CONF_SCHEDULE_TYPE: schedule_type,
            CONF_SCHEDULE_DAYS: schedule_days or [],
            CONF_ADAPTIVE: adaptive,
            CONF_NOTIFY_WHEN_DUE: notify_when_due,
            CONF_NOTIFY_ADVANCE_DAYS: notify_advance_days,
            CONF_LAST_COMPLETED: dt_util.now().isoformat(),
            CONF_COMPLETION_HISTORY: [],
        }
        self._chores.append(chore)
        await self.async_save()
        return chore

    async def async_update_chore(self, chore_id: str, **kwargs: Any) -> bool:
        """Update a chore's fields and persist."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return False
        for key, value in kwargs.items():
            chore[key] = value
        await self.async_save()
        return True

    async def async_complete_chore(self, chore_id: str) -> bool:
        """Mark a chore as completed now, recording to history."""
        chore = self.get_chore(chore_id)
        if chore is None:
            return False
        now_iso = dt_util.now().isoformat()
        chore[CONF_LAST_COMPLETED] = now_iso

        # Append to history, trimming to max size
        history: list[str] = chore.setdefault(CONF_COMPLETION_HISTORY, [])
        history.append(now_iso)
        if len(history) > COMPLETION_HISTORY_MAX:
            history[:] = history[-COMPLETION_HISTORY_MAX:]

        await self.async_save()
        _LOGGER.info("Chore '%s' completed (history: %d entries)", chore.get(CONF_NAME), len(history))
        return True

    async def async_remove_chore(self, chore_id: str) -> bool:
        """Remove a chore and persist."""
        original_len = len(self._chores)
        self._chores = [c for c in self._chores if c[CONF_CHORE_ID] != chore_id]
        if len(self._chores) == original_len:
            return False
        await self.async_save()
        return True

    # ── Listeners ─────────────────────────────────────────────────────────────

    def add_listener(self, listener) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            try:
                listener()
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Error in chore store listener: %s", err)
