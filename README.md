# 🧹 Chore Reminder — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/lou270/ha-chore-reminder/releases)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-brightgreen.svg)](https://www.home-assistant.io/)

Gérez toutes vos tâches ménagères récurrentes directement depuis Home Assistant, inspiré de [Donetick](https://donetick.com/) — sans application externe.

---

## ✨ Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| 📋 **Liste de tâches native** | Basée sur l'entité `todo`, compatible avec la carte `todo-list` de HA |
| 🔄 **Planification flexible** | Par intervalle (N jours), hebdomadaire (jours fixes) ou mensuelle (jour du mois) |
| 🧠 **Fréquence adaptive** | Apprend de votre rythme réel grâce à l'historique des completions |
| 📊 **Historique** | Dernières 20 completions enregistrées automatiquement |
| 🏷️ **Catégories** | Organisez vos tâches par catégorie (cuisine, jardin, animaux…) |
| 🔔 **Notifications** | Rappels automatiques à 8h chaque matin via `persistent_notification` |
| 📅 **Calendrier** | Vue calendrier de toutes les prochaines échéances |
| 📡 **Capteurs** | Prochaine tâche + compteur de tâches en retard |
| 💾 **Stockage persistant** | Toutes les données sauvegardées en JSON via le store HA |

---

## 📦 Installation

### Via HACS (recommandé)

1. Ouvrez HACS dans Home Assistant
2. **Intégrations** → menu ⋮ → **Dépôts personnalisés**
3. Ajoutez `https://github.com/lou270/ha-chore-reminder` (catégorie : **Intégration**)
4. Installez **Chore Reminder**
5. Redémarrez Home Assistant

### Installation manuelle

1. Copiez le dossier `custom_components/chore_reminder/` dans votre dossier `config/custom_components/`
2. Redémarrez Home Assistant

---

## ⚙️ Configuration

### Première installation

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration**
2. Cherchez **Chore Reminder** et cliquez sur **Configurer**
3. Cliquez sur **Soumettre** — l'intégration ne s'installe qu'une seule fois

### Ajouter / Modifier / Supprimer des tâches

1. **Paramètres** → **Appareils et services** → **Chore Reminder** → **Configurer**
2. Choisissez une action :
   - ➕ **Ajouter une tâche**
   - ✏️ **Modifier une tâche**
   - 🗑️ **Supprimer une tâche**

### Paramètres d'une tâche

| Paramètre | Description |
|---|---|
| **Nom** | Nom de la tâche |
| **Catégorie** | Texte libre (ex: `cuisine`, `jardin`) |
| **Type de planification** | `interval` / `weekly` / `monthly` |
| **Fréquence** | Nombre de jours (pour le type `interval`) |
| **Jours** | Jours de la semaine (0=Lun…6=Dim) ou jour du mois (pour `weekly`/`monthly`), séparés par des virgules |
| **Fréquence adaptive** | Calcule automatiquement la fréquence idéale depuis l'historique |
| **Icône** | Icône MDI (ex: `mdi:broom`) |
| **Notes** | Informations complémentaires |
| **Notifications** | Active les rappels à 8h |
| **Jours d'avance** | Nombre de jours avant l'échéance pour envoyer la notification |

### Exemples de planification

```
Type: interval, Fréquence: 7       → Toutes les semaines
Type: weekly, Jours: 0, 3          → Tous les lundis et jeudis
Type: monthly, Jours: 1            → Le 1er de chaque mois
Type: interval + adaptive activé   → Fréquence calculée sur l'historique
```

---

## 🃏 Cartes Lovelace

### Liste des tâches (native, recommandée)

```yaml
type: todo-list
entity: todo.taches_menageres
```

La carte native affiche automatiquement :
- Le nom de la tâche
- La catégorie avec 🏷️
- L'urgence : `⚠️ En retard de Xj` / `📅 Aujourd'hui` / `📅 Dans Xj`
- La date d'échéance
- ✅ Cocher = marquer comme fait (remet le compteur à zéro)

### Valider une tâche depuis la liste

Cliquez sur le **cercle** à gauche du nom → la tâche est marquée comme faite, `last_completed` est mis à jour, la prochaine échéance est recalculée.

### Changer la date d'échéance

Cliquez sur la tâche → icône calendrier → choisissez une nouvelle date. Le planning est décalé en conséquence (`last_completed = nouvelle_date - fréquence`).

### Ajouter une tâche depuis la liste

Utilisez le champ en bas de la carte. La fréquence sera par défaut de 7 jours ; modifiez-la ensuite via les Options.

### Calendrier

```yaml
type: calendar
entities:
  - calendar.calendrier
```

### Capteur prochaine tâche

```yaml
type: entity
entity: sensor.prochaine_tache
```

Attributs disponibles : `chore_name`, `chore_icon`, `chore_category`, `next_due`, `days_remaining`, `total_chores`, `overdue_count`, `categories`

### Capteur tâches en retard

```yaml
type: entity
entity: sensor.taches_en_retard
```

Utile pour les automations et les badges de tableau de bord.

---

## 🤖 Automations

### Badge d'alerte personnalisé

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

### Notification sur mobile

```yaml
automation:
  - alias: "Alerte corvée critique"
    trigger:
      - platform: numeric_state
        entity_id: sensor.taches_en_retard
        above: 0
    action:
      - service: notify.mobile_app_mon_telephone
        data:
          title: "🧹 Corvées en retard"
          message: "{{ states('sensor.taches_en_retard') }} tâche(s) en retard !"
```

---

## 📡 Entités créées

| Entité | Type | Description |
|---|---|---|
| `todo.taches_menageres` | Todo | Liste complète de toutes les tâches |
| `sensor.prochaine_tache` | Sensor | Jours restants pour la tâche la plus urgente |
| `sensor.taches_en_retard` | Sensor | Nombre de tâches en retard |
| `calendar.calendrier` | Calendar | Calendrier de toutes les prochaines échéances |

---

## 🔄 Migration depuis v1.x

> ⚠️ La v2.0+ utilise une architecture différente (une seule instance au lieu d'une par tâche).

1. **Supprimez** l'ancienne intégration Chore Reminder
2. Supprimez le dossier `__pycache__` si présent
3. Mettez à jour les fichiers
4. Redémarrez Home Assistant
5. Réinstallez l'intégration (une seule fois)
6. Recréez vos tâches via le menu **Options**

---

## 🛠️ Développement

```
custom_components/chore_reminder/
├── __init__.py          # Setup de l'intégration, notifications
├── const.py             # Constantes
├── store.py             # Stockage persistant + logique métier
├── config_flow.py       # Flux de configuration et d'options
├── todo.py              # Entité liste de tâches
├── sensor.py            # Capteurs (prochaine tâche, retard)
├── calendar.py          # Entité calendrier
├── notify.py            # Vérification quotidienne et notifications
└── translations/        # Traductions FR / EN
```

### Données stockées

Les données sont sauvegardées dans `.storage/chore_reminder.chores` (JSON) :

```json
{
  "id": "uuid",
  "name": "Litière",
  "category": "animaux",
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

---

## 📝 Changelog

### v2.1.0
- ✨ Fréquence adaptive (médiane de l'historique)
- ✨ Historique des completions (20 dernières)
- ✨ Planification flexible : hebdomadaire et mensuelle
- ✨ Catégories / Tags
- ✨ Notifications quotidiennes à 8h
- ✨ Capteur `sensor.taches_en_retard`

### v2.0.0
- ✨ Architecture centralisée (une seule instance)
- ✨ Intégration native `todo` (liste de tâches HA)
- ✨ Stockage JSON persistant
- ✨ Calendrier global
- 🗑️ Suppression de `binary_sensor` et `button`

### v1.x
- Architecture par corvée (une config entry par tâche)
- Carte Lovelace custom

---

## 📄 Licence

MIT — © [lou270](https://github.com/lou270)
