# Gestion des Plantes (Home Assistant Integration)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Intégration personnalisée pour gérer l'arrosage de vos plantes dans Home Assistant.

## Fonctionnalités
-   **Ajout facile** : Configuration via l'interface utilisateur (UI).
-   **Suivi** : Calcul automatique des jours restants avant le prochain arrosage.
-   **Alertes** : Capteur binaire "Problème" quand la plante a besoin d'eau.
-   **Action** : Bouton pour valider l'arrosage et réinitialiser le chronomètre.
-   **Persistance** : La date du dernier arrosage est conservée même après redémarrage.

## Installation

### Via HACS (Recommandé)
1.  Assurez-vous d'avoir [HACS](https://hacs.xyz/) installé.
2.  Ajoutez ce dépôt en tant que **Dépôt personnalisé** :
    -   Allez dans HACS > Intégrations.
    -   Cliquez sur les 3 points en haut à droite > Dépôts personnalisés.
    -   Collez l'URL de ce dépôt et choisissez la catégorie **"Integration"**.
3.  Cliquez sur **Télécharger**.
4.  Redémarrez Home Assistant.

### Manuelle
1.  Téléchargez le dossier `custom_components/gestion_plantes`.
2.  Copiez-le dans votre dossier `config/custom_components/`.
3.  Redémarrez Home Assistant.

## Configuration
1.  Allez dans **Paramètres** > **Appareils et services**.
2.  Cliquez sur **Ajouter une intégration**.
3.  Cherchez **"Gestion des Plantes"**.
4.  Suivez les instructions pour ajouter vos plantes (Nom, Intervalle, Image).

## Cartes Lovelace (Exemples)
Voir le fichier `lovelace_examples.yaml` ou le Wiki pour des exemples de cartes (Tuile, Mushroom, etc.).
