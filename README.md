# 🧹 Chore Reminder — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/lou270/ha-chore-reminder/releases)
[![HA](https://img.shields.io/badge/Home%20Assistant-2026.2%2B-brightgreen.svg)](https://www.home-assistant.io/)

Manage all your recurring chores directly from Home Assistant, inspired by [Donetick](https://donetick.com/) — no external app required.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📋 **Native todo list** | Based on the `todo` entity, compatible with HA's built-in `todo-list` card |
| 🔄 **Flexible scheduling** | By interval (every N days), weekly (fixed weekdays) or monthly (day of month) |
| 🧠 **Adaptive frequency** | Learns from your actual completion rhythm using history |
| 📊 **History** | Last 20 completions recorded automatically |
| 🏷️ **Categories** | Organize chores by category (kitchen, garden, pets…) |
| 🔔 **Notifications** | Daily reminders at 8 AM — persistent notification + optional mobile push |
| 📅 **Calendar** | Calendar view of all upcoming due dates |
| 📡 **Sensors** | Next chore + overdue chore counter |
| 💾 **Persistent storage** | All data saved as JSON via the HA store |

---

## 📦 Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. **Integrations** → ⋮ menu → **Custom repositories**
3. Add `https://github.com/lou270/ha-chore-reminder` (category: **Integration**)
4. Install **Chore Reminder**
5. Restart Home Assistant

### Manual installation

1. Copy the `custom_components/chore_reminder/` folder into your `config/custom_components/` directory
2. Restart Home Assistant

---

## ⚙️ Configuration

### First installation

1. **Settings** → **Devices & services** → **Add integration**
2. Search for **Chore Reminder** and click **Configure**
3. Click **Submit** — the integration is installed only once

### Add / Edit / Delete chores

1. **Settings** → **Devices & services** → **Chore Reminder** → **Configure**
2. Choose an action:
   - ➕ **Add a chore**
   - ✏️ **Edit a chore**
   - 🗑️ **Delete a chore**
   - 🔔 **Configure notifications**

### Chore parameters

| Parameter | Description |
|---|---|
| **Name** | Chore name |
| **Category** | Free text (e.g. `kitchen`, `garden`) |
| **Schedule type** | `interval` / `weekly` / `monthly` |
| **Frequency** | Number of days (for `interval` type) |
| **Days** | Weekdays (0=Mon…6=Sun) or day of month (for `weekly`/`monthly`), comma-separated |
| **Adaptive frequency** | Automatically computes the ideal frequency from completion history |
| **Icon** | MDI icon (e.g. `mdi:broom`) |
| **Notes** | Additional information |
| **Enable notifications** | Enables daily reminders at 8 AM |
| **Days in advance** | How many days before the due date to send the notification |

### Scheduling examples

```
Type: interval, Frequency: 7       → Every week
Type: weekly,   Days: 0, 3         → Every Monday and Thursday
Type: monthly,  Days: 1            → On the 1st of each month
Type: interval + adaptive enabled  → Frequency computed from history
```

### Mobile notifications

Go to **Configure → 🔔 Configure notifications** and enter your notify service name (found under **Settings → Devices & services → Companion App**):

```
notify.mobile_app_my_phone
```

Leave the field empty to disable mobile push. Persistent notifications are always sent regardless of this setting.

---

## 🃏 Lovelace cards

### Todo list (native, recommended)

```yaml
type: todo-list
entity: todo.taches_menageres
```

The native card automatically displays:
- The chore name
- The category with 🏷️
- Urgency: `⚠️ X days late` / `📅 Today` / `📅 In X days`
- The due date
- ✅ Checking = mark as done (resets the counter)

### Completing a chore from the list

Click the **circle** to the left of the name → the chore is marked as done, `last_completed` is updated, and the next due date is recalculated.

### Changing the due date

Click the chore → calendar icon → pick a new date. The schedule shifts accordingly (`last_completed = new_date - frequency`).

### Adding a chore from the list

Use the input field at the bottom of the card. The frequency defaults to 7 days; adjust it afterwards via Options.

### Calendar

```yaml
type: calendar
entities:
  - calendar.calendrier
```

### Next chore sensor

```yaml
type: entity
entity: sensor.prochaine_tache
```

Available attributes: `chore_name`, `chore_icon`, `chore_category`, `next_due`, `days_remaining`, `total_chores`, `overdue_count`, `categories`

### Overdue chores sensor

```yaml
type: entity
entity: sensor.taches_en_retard
```

Useful for automations and dashboard badges.

---

## 🤖 Automations

### Custom alert badge

```yaml
type: mushroom-chips-card
chips:
  - type: entity
    entity: sensor.taches_en_retard
    icon: mdi:alert-circle
    icon_color: red
    tap_action:
      action: navigate
      navigation_path: /lovelace/corvees
```

### Mobile notification on overdue chores

```yaml
automation:
  - alias: "Critical chore alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.taches_en_retard
        above: 0
    action:
      - service: notify.mobile_app_my_phone
        data:
          title: "🧹 Overdue chores"
          message: "{{ states('sensor.taches_en_retard') }} chore(s) overdue!"
```

---

## 📡 Created entities

| Entity | Type | Description |
|---|---|---|
| `todo.taches_menageres` | Todo | Full list of all chores |
| `sensor.prochaine_tache` | Sensor | Days remaining for the most urgent chore |
| `sensor.taches_en_retard` | Sensor | Number of overdue chores |
| `calendar.calendrier` | Calendar | Calendar of all upcoming due dates |

---

## 🔄 Migration from v1.x

> ⚠️ v2.0+ uses a different architecture (single instance instead of one per chore).

1. **Delete** the old Chore Reminder integration
2. Remove the `__pycache__` folder if present
3. Update the files
4. Restart Home Assistant
5. Reinstall the integration (once)
6. Recreate your chores via the **Options** menu

---

## 🛠️ Development

```
custom_components/chore_reminder/
├── __init__.py          # Integration setup
├── const.py             # Constants
├── store.py             # Persistent storage + business logic
├── config_flow.py       # Configuration and options flow
├── todo.py              # Todo list entity
├── sensor.py            # Sensors (next chore, overdue)
├── calendar.py          # Calendar entity
├── notify.py            # Daily check and notifications
└── translations/        # FR / EN translations
```

### Stored data

Data is saved in `.storage/chore_reminder.chores` (JSON):

```json
{
  "id": "uuid",
  "name": "Cat litter",
  "category": "pets",
  "icon": "mdi:cat",
  "schedule_type": "interval",
  "frequency": 3,
  "adaptive": true,
  "last_completed": "2026-03-10T18:00:00+01:00",
  "completion_history": ["2026-03-07T...", "2026-03-04T..."],
  "notify_when_due": true,
  "notify_advance_days": 1
}
```

The global notify service is stored in the config entry options:

```json
{
  "notify_service": "notify.mobile_app_my_phone"
}
```

---

## 📝 Changelog

### v2.2.0
- ✨ Native mobile push notifications — configure a `notify.*` service directly in the integration options
- ✨ New **🔔 Configure notifications** menu in Options

### v2.1.0
- ✨ Adaptive frequency (median of completion history)
- ✨ Completion history (last 20)
- ✨ Flexible scheduling: weekly and monthly
- ✨ Categories / Tags
- ✨ Daily notifications at 8 AM
- ✨ `sensor.taches_en_retard` overdue sensor

### v2.0.0
- ✨ Centralised architecture (single instance)
- ✨ Native `todo` integration (HA todo list)
- ✨ Persistent JSON storage
- ✨ Global calendar
- 🗑️ Removed `binary_sensor` and `button`

### v1.x
- Per-chore architecture (one config entry per chore)
- Custom Lovelace card

---

## 📄 License

MIT — © [lou270](https://github.com/lou270)
