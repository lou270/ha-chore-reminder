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

## Exemples de Cartes
Voir `lovelace_examples.yaml`.
