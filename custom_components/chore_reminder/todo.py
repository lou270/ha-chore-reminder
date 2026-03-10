"""Todo platform for Chore Reminder."""
from __future__ import annotations

import logging
from datetime import datetime
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

            # Overdue or due today = NEEDS_ACTION but with urgency in description suffix
            status = TodoItemStatus.NEEDS_ACTION

            description = chore.get(CONF_NOTES, "") or ""
            if days <= 0:
                suffix = f"⚠️ En retard de {abs(days)}j" if days < 0 else "📅 Aujourd'hui"
            elif days == 1:
                suffix = "📅 Demain"
            else:
                suffix = f"📅 Dans {days}j"

            if description:
                description = f"{suffix} · {description}"
            else:
                description = suffix

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
        await self._store.async_add_chore(
            name=item.summary or "",
            notes=item.description or "",
        )

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Handle completing, editing name or description from the todo UI."""
        chore_id = item.uid

        if item.status == TodoItemStatus.COMPLETED:
            # Mark as completed → reset last_completed to now
            await self._store.async_complete_chore(chore_id)
        else:
            # Update name/description if changed
            update: dict[str, Any] = {}
            if item.summary is not None:
                update[CONF_NAME] = item.summary
            if item.description is not None:
                # Strip the status suffix we injected
                desc = item.description
                for prefix in ("⚠️", "📅"):
                    if desc.startswith(prefix):
                        # Remove the injected suffix
                        if " · " in desc:
                            desc = desc.split(" · ", 1)[1]
                        else:
                            desc = ""
                        break
                update[CONF_NOTES] = desc
            if update:
                await self._store.async_update_chore(chore_id, **update)

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete chores from the todo UI."""
        for uid in uids:
            await self._store.async_remove_chore(uid)
