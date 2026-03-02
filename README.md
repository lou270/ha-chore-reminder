# Chore Reminder (Home Assistant Integration)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Intégration personnalisée pour gérer vos tâches ménagères récurrentes dans Home Assistant.

## Fonctionnalités
-   **Tâches Récurrentes** : Configurez des tâches avec une fréquence en jours.
-   **Suivi** : Calcul automatique des jours restants avant la prochaine échéance.
-   **Alertes** : Capteur "Problème" quand la tâche est à faire.
-   **Action** : Bouton pour marquer comme fait.
-   **Icônes/Images** : Personnalisables pour chaque tâche (Icône MDI ou URL d'image).

## Installation

### Via HACS
1.  Ajoutez ce dépôt en tant que **Dépôt personnalisé** dans HACS.
2.  Installez l'intégration **Chore Reminder**.
3.  Redémarrez Home Assistant.

### Manuelle
1.  Copiez `custom_components/chore_reminder` dans votre dossier `config/custom_components/`.
2.  Redémarrez Home Assistant.

## Configuration
1.  Allez dans **Paramètres** > **Appareils et services**.
2.  Cliquez sur **Ajouter une intégration**.
3.  Cherchez **"Chore Reminder"**.
4.  Ajoutez vos tâches (Nom, Fréquence, Icône).

## Exemples de Cartes (Lovelace UI)

### 1. Affichage détaillé d'une ou plusieurs tâches
Voici un exemple de carte utilisant la disposition `custom:mushroom-entity-card` (si vous utilisez Mushroom) ou une simple carte `Entities` pour afficher le nom, les jours restants, l'état d'alerte et le bouton d'action au même endroit.

*Assurez-vous de remplacer `nom_de_la_corvee` par l'ID réel généré par Home Assistant.*

```yaml
type: entities
title: 🧹 Mes Corvées
entities:
  # --- Corvée 1 ---
  - type: custom:multiple-entity-row # Nécessite la carte HACS 'multiple-entity-row'
    entity: sensor.nom_de_la_corvee_jours_restants
    name: Nettoyer la cuisine
    icon: mdi:broom
    state_color: true
    entities:
      - entity: binary_sensor.nom_de_la_corvee_a_faire
        name: false
        icon: mdi:alert-circle
      - entity: button.nom_de_la_corvee_terminer
        name: Fait !
        icon: mdi:check
  # --- Corvée 2 ---
  - type: custom:multiple-entity-row
    entity: sensor.une_autre_corvee_jours_restants
    name: Arroser les plantes
    icon: mdi:watering-can
    state_color: true
    entities:
      - entity: binary_sensor.une_autre_corvee_a_faire
        name: false
      - entity: button.une_autre_corvee_terminer
        name: Fait !
        icon: mdi:check
```

*Astuce : Si vous ne voulez pas installer de cartes personnalisées, voici la version native simple :*
```yaml
type: entities
title: 🧹 Mes Corvées
entities:
  - entity: sensor.nom_de_la_corvee_jours_restants
  - entity: button.nom_de_la_corvee_terminer
```

### 2. Le Calendrier des tâches
Puisque l'intégration génère un calendrier complet prédisant les échéances à venir de toutes vos corvées, vous pouvez l'afficher avec la carte native `calendar` :

```yaml
type: calendar
title: 📅 Planning des Corvées
entities:
  - calendar.nom_de_la_corvee_calendrier
  - calendar.une_autre_corvee_calendrier
initial_view: dayGridMonth
```

### 3. Prochaines tâches (Dynamique)
Utilisez la carte personnalisée `auto-entities` (disponible sur HACS) pour afficher **automatiquement** toutes vos corvées triées par urgence. Les nouvelles tâches ajoutées apparaîtront sans modification de la carte.

```yaml
type: custom:auto-entities
card:
  type: entities
  title: 📋 Prochaines Tâches
  show_header_toggle: false
filter:
  include:
    - integration: chore_reminder
      domain: sensor
sort:
  method: state
  numeric: true
```
