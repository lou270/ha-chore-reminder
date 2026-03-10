"""Todo platform for Chore Reminder."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_CHORE_ID,
    CONF_CATEGORY,
    CONF_LAST_COMPLETED,
    CONF_NAME,
    CONF_ICON,
    CONF_NOTES,
    CONF_FREQUENCY,
    DEFAULT_ICON,
    DEFAULT_FREQUENCY,
)
from .store import ChoreStore

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the todo platform."""
    store: ChoreStore = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChoreTodoListEntity(store, entry)])


class ChoreTodoListEntity(TodoListEntity):
    """A todo list entity representing all chores."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "chore_list"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, store: ChoreStore, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self._store = store
        self._attr_unique_id = f"{entry.entry_id}_todo"
        self._attr_icon = "mdi:checkbox-marked-circle-outline"
        self._entry = entry

    async def async_added_to_hass(self) -> None:
        """Register listener for store changes."""
        self._store.add_listener(self._on_store_update)

    async def async_will_remove_from_hass(self) -> None:
        """Deregister listener."""
        self._store.remove_listener(self._on_store_update)

    def _on_store_update(self) -> None:
        """Called when the chore store changes."""
        self.async_write_ha_state()

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return the list of todo items sorted by urgency."""
        items = []
        now = dt_util.now()
        for chore in self._store.get_all_chores():
            chore_id = chore[CONF_CHORE_ID]
            next_due_dt = self._store.next_due_date(chore_id)
            due_date = next_due_dt.date() if next_due_dt else now.date()
            days = self._store.days_remaining(chore_id)

            status = TodoItemStatus.NEEDS_ACTION

            notes = chore.get(CONF_NOTES, "") or ""
            category = chore.get(CONF_CATEGORY, "") or ""

            if days < 0:
                suffix = f"⚠️ En retard de {abs(days)}j"
            elif days == 0:
                suffix = "📅 Aujourd'hui"
            elif days == 1:
                suffix = "📅 Demain"
            else:
                suffix = f"📅 Dans {days}j"

            parts = [suffix]
            if category:
                parts.append(f"🏷️ {category}")
            if notes:
                parts.append(notes)

            description = " · ".join(parts)

            items.append(
                TodoItem(
                    uid=chore_id,
                    summary=chore.get(CONF_NAME, ""),
                    status=status,
                    description=description,
                    due=due_date,
                )
            )
        return items


    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new chore from the todo UI."""

        # If user provided a due date, back-calculate last_completed
        last_completed_iso: str | None = None
        if item.due:
            due_as_date = item.due if isinstance(item.due, date) else item.due.date()
            last_completed_dt = due_as_date - timedelta(days=DEFAULT_FREQUENCY)
            last_completed_iso = dt_util.start_of_local_day(
                datetime(last_completed_dt.year, last_completed_dt.month, last_completed_dt.day)
            ).isoformat()

        chore = await self._store.async_add_chore(
            name=item.summary or "",
            notes=item.description or "",
        )
        if last_completed_iso:
            await self._store.async_update_chore(
                chore[CONF_CHORE_ID],
                **{CONF_LAST_COMPLETED: last_completed_iso}
            )

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Handle completing, editing name, description or due date from the todo UI."""

        chore_id = item.uid

        if item.status == TodoItemStatus.COMPLETED:
            # Mark as completed → reset last_completed to now
            await self._store.async_complete_chore(chore_id)
            return

        update: dict[str, Any] = {}

        # Handle name change
        if item.summary is not None:
            update[CONF_NAME] = item.summary

        # Handle description change (strip injected status prefix)
        if item.description is not None:
            desc = item.description
            for prefix in ("⚠️", "📅"):
                if desc.startswith(prefix):
                    desc = desc.split(" · ", 1)[1] if " · " in desc else ""
                    break
            update[CONF_NOTES] = desc

        # Handle due date change → recalculate last_completed
        if item.due is not None:
            chore = self._store.get_chore(chore_id)
            if chore:
                frequency = chore.get(CONF_FREQUENCY, DEFAULT_FREQUENCY)
                due_as_date = item.due if isinstance(item.due, date) else item.due.date()
                new_last_completed = due_as_date - timedelta(days=frequency)
                new_lc_dt = dt_util.start_of_local_day(
                    datetime(new_last_completed.year, new_last_completed.month, new_last_completed.day)
                )
                update[CONF_LAST_COMPLETED] = new_lc_dt.isoformat()

        if update:
            await self._store.async_update_chore(chore_id, **update)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete chores from the todo UI."""
        for uid in uids:
            await self._store.async_remove_chore(uid)
