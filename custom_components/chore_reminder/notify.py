"""Daily notification checker for Chore Reminder."""
from __future__ import annotations

import logging
from datetime import datetime, time

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_CHORE_ID,
    CONF_NOTIFY_WHEN_DUE,
    CONF_NOTIFY_ADVANCE_DAYS,
    CONF_NOTIFY_SERVICE,
)
from .store import ChoreStore

_LOGGER = logging.getLogger(__name__)

NOTIFY_HOUR = 8  # Check at 8:00 AM every day


def setup_notifications(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register the daily notification check."""

    @callback
    def _check_notifications_callback(now: datetime) -> None:
        """Callback called at 8:00 AM — schedule the async check."""
        hass.async_create_task(_async_check_and_notify(hass, entry))

    # Track every day at 8:00:00
    unsub = async_track_time_change(
        hass,
        _check_notifications_callback,
        hour=NOTIFY_HOUR,
        minute=0,
        second=0,
    )
    # Store the unsub so we can cancel it when the entry is unloaded
    entry.async_on_unload(unsub)


async def _async_check_and_notify(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Check all chores and send notifications for due ones."""
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        return

    store: ChoreStore = hass.data[DOMAIN][entry.entry_id]
    chores = store.get_all_chores()

    for chore in chores:
        if not chore.get(CONF_NOTIFY_WHEN_DUE):
            continue

        chore_id = chore[CONF_CHORE_ID]
        name = chore.get(CONF_NAME, "Corvée")
        advance_days = chore.get(CONF_NOTIFY_ADVANCE_DAYS, 1)
        days = store.days_remaining(chore_id)

        if days <= advance_days:
            notify_service = entry.options.get(CONF_NOTIFY_SERVICE, "")
            _send_notification(hass, name, days, notify_service)


def _send_notification(hass: HomeAssistant, name: str, days: int, notify_service: str = "") -> None:
    """Send a persistent notification and optionally a mobile push for a due chore."""
    if days < 0:
        message = f"⚠️ **{name}** est en retard de {abs(days)} jour(s) !"
        title = f"Corvée en retard : {name}"
    elif days == 0:
        message = f"📋 **{name}** doit être fait **aujourd'hui** !"
        title = f"Corvée à faire aujourd'hui : {name}"
    elif days == 1:
        message = f"📋 **{name}** doit être fait **demain**."
        title = f"Rappel corvée : {name}"
    else:
        message = f"📋 **{name}** doit être fait dans **{days} jours**."
        title = f"Rappel corvée : {name}"

    notification_id = f"{DOMAIN}_{name.lower().replace(' ', '_')}"

    hass.async_create_task(
        hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": title,
                "message": message,
                "notification_id": notification_id,
            },
        )
    )

    if notify_service:
        domain, _, service = notify_service.partition(".")
        if domain and service:
            hass.async_create_task(
                hass.services.async_call(
                    domain,
                    service,
                    {"title": title, "message": message},
                )
            )

    _LOGGER.info("Notification sent for chore '%s' (days_remaining=%d)", name, days)
