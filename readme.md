# Gestionnaire de Clés 🔑

## Description
Application web de gestion des clés et des salles développée avec Streamlit et SQLAlchemy. Cette application permet de gérer efficacement les emprunts de clés, les salles et les emprunteurs dans un établissement.

## Fonctionnalités principales

### 📊 Tableau de bord
- Vue d'ensemble des statistiques (nombre de salles, emprunteurs, emprunts)
- Visualisation de la disponibilité des salles
- Graphiques et tableaux interactifs

### 🏢 Gestion des Salles
- Liste complète des salles avec leurs caractéristiques
- Ajout de nouvelles salles
- Import en masse via fichier CSV
- Suivi de la disponibilité

### 🔑 Gestion des Clés
- Attribution automatique des clés aux salles
- Suivi de l'état des clés (disponible/empruntée)
- Historique des emprunts

### 👥 Gestion des Emprunteurs
- Enregistrement des emprunteurs
- Suivi des emprunts par utilisateur
- Historique des emprunts

## Structure de la base de données

### Tables principales
- `emprunteurs` : Informations sur les personnes autorisées à emprunter
- `salles` : Détails des salles (capacité, équipements, etc.)
- `cles` : Gestion des clés physiques
- `emprunts` : Suivi des emprunts et retours

## Technologies utilisées
- **Frontend** : Streamlit
- **Base de données** : SQLite avec SQLAlchemy
- **Visualisation** : Pandas, Streamlit components
- **UI Components** : streamlit-shadcn-ui, AgGrid

## Installation et démarrage

1. Cloner le repository
"""bash
git clone https://github.com/Mr-KAM/gestionnaire-de-cl-.git
cd gestionnaire-de-cl-
"""

2. Installer les dépendances
"""bash
pew new gestionnaire_de_cle
pew workon gestionnaire_de_cle
pip install -r requirements.txt
"""
3. Lancer l'application
"""bash
streamlit run app.py
"""


## Remarques importantes
⚠️ L'application nécessite Python 3.9+
📊 Les données sont persistées localement dans une base SQLite
🔄 Redémarrage nécessaire après modification du schéma de base de données
🚧 Version de développement - ne pas utiliser en production

## Contribuer
Les contributions sont les bienvenues via :
- Signalement de bugs sur l'issue tracker
- Suggestions d'améliorations
- Pull requests pour les corrections
