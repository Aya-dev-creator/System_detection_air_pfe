# 🌍 AirPredict — Système de Surveillance et Prédiction de la Qualité de l'Air

AirPredict (AirWatch) est une application web moderne basée sur **Flask (Python)** et le **Server-Side Rendering (SSR)** permettant de surveiller la qualité de l'air, de prédire l'indice de pollution à l'aide de modèles de Machine Learning, et d'accompagner les entreprises dans leur transition écologique via des recommandations générées par l'intelligence artificielle (Mistral AI).

---

## 📖 Sommaire
1. [Architecture & Technologies](#-architecture--technologies)
2. [Structure du Projet](#-structure-du-projet)
3. [Configuration et Installation](#-configuration-et-installation)
4. [Démarrage Rapide](#-démarrage-rapide)
5. [Module Entreprises & Industries (B2B)](#-module-entreprises--industries-b2b)
6. [Routes de l'Application](#-routes-de-lapplication)
7. [Format des Fichiers CSV de Test](#-format-des-fichiers-csv-de-test)
8. [Sécurité et Robustesse](#-sécurité-et-robustesse)
9. [Dépannage (Troubleshooting)](#-dépannage-troubleshooting)

---

## 🏗️ Architecture & Technologies

L'application est entièrement construite sur une architecture **SSR (Server-Side Rendering)** et **sans aucun JavaScript côté client (No-JS)**, garantissant une rapidité optimale, une sécurité accrue et une compatibilité maximale.

*   **Backend** : Python 3.10+ & Flask 3.0.0 (Gestion des routes, de la session, du traitement des données).
*   **Base de Données** : SQLite 3 (Stockage des mesures historiques de la qualité de l'air).
*   **Machine Learning** : Modèles prédictifs entraînés (Scikit-Learn) sérialisés dans le dossier `models/` sous format `.pkl`.
*   **Intelligence Artificielle** : API Mistral AI pour générer des rapports écologiques sur-mesure pour les industries.
*   **Frontend** : HTML5 sémantique & Jinja2 (Moteur de templates) stylisés en CSS3 pur (animations, barres de progression dynamiques, media queries responsives).
*   **Cartographie** : Cartes géographiques générées avec Folium.

---

## 📁 Structure du Projet

```text
versel/
├── 🐍 Code Backend Principal
│   ├── web_server.py                  # Serveur Flask principal (routes, traitement)
│   ├── database.py                    # Module de gestion de la base de données SQLite
│   ├── config.py                      # Configurations globales de l'application
│   ├── ml_model.py                    # Logique du modèle de Machine Learning
│   ├── weather_chatbot.py             # Chatbot météo et intégration de l'API Mistral AI
│   └── openweather_data_provider.py   # Module d'intégration de l'API OpenWeather Map
│
├── 🎨 Interface Utilisateur (Templates HTML & CSS)
│   ├── static/
│   │   └── css/
│   │       ├── dashboard.css          # Design global moderne et premium
│   │       └── responsive.css         # Media queries pour appareils mobiles
│   └── templates/
│       ├── base.html                  # Squelette de base HTML5
│       ├── dashboard.html             # Dashboard public principal
│       ├── analytics.html             # Graphiques et analyses
│       ├── predictions.html           # Interface utilisateur des prédictions ML
│       ├── map.html                   # Vue cartographique
│       ├── chatbot.html               # Chatbot grand public
│       ├── news.html                  # Flux d'actualités sur l'air
│       ├── co2_wash.html              # Module CO2 Wash
│       ├── static_map_render.html     # Conteneur pour carte Folium
│       └── entreprise_...             # Templates dédiés à l'espace Entreprises
│
├── 📊 Données & Modèles
│   ├── data/
│   │   ├── air_quality.db             # Base de données SQLite locale
│   │   ├── test_capteurs_usine.csv    # Fichier de données d'importation de test
│   │   └── uploads/                   # Dossier de réception des imports CSV
│   └── models/
│       ├── air_quality_model.pkl      # Fichier pickle du modèle ML
│       └── air_quality_model_scaler.pkl # Scaler associé au modèle ML
│
└── ⚙️ Fichiers de Configuration
    ├── requirements.txt               # Dépendances Python nécessaires
    ├── pyproject.toml                 # Fichier de configuration du projet
    └── .env                           # Variables d'environnement privées (Clés API)
```

---

## ⚙️ Configuration et Installation

### Prerrequis
*   Python 3.10 ou version supérieure installée sur votre machine.

### Étape 1 : Cloner et préparer l'environnement virtuel
```bash
# Activer/créer un environnement virtuel Python
python -m venv .venv

# Activer l'environnement virtuel (sur Windows)
.venv\Scripts\activate
```

### Étape 2 : Installer les dépendances
```bash
pip install -r requirements.txt
```

### Étape 3 : Configurer les clés API
Créez un fichier `.env` à la racine du dossier `versel/` et configurez vos jetons d'API :
```env
# Clé API Mistral (Indispensable pour le chatbot et le rapport B2B)
MISTRAL_API_KEY=votre_cle_mistral_ici

# Clé API OpenWeather (Pour récupérer les données réelles)
OPENWEATHER_API_KEY=votre_cle_openweather_ici

# Clé secrète Flask pour chiffrer la session de l'utilisateur
SECRET_KEY=cle_securisee_generique_pfe_2026
```

---

## 🚀 Démarrage Rapide

1. Activez votre environnement virtuel si ce n'est pas déjà fait.
2. Lancez le serveur Flask :
   ```bash
   python web_server.py
   ```
3. Ouvrez votre navigateur et accédez à : **`http://127.0.0.1:5000`**

---

## 🏭 Module Entreprises & Industries (B2B)

Le module **Entreprises & Industries** est accessible via la route `/entreprise`. Il permet à des entités tierces (Usines, Villes, Pays) de téléverser des données de capteurs de pollution pour analyser leur profil de pollution et obtenir un plan d'action de décarbonation.

### Fonctionnalités Clés :
*   **Authentification simplifiée** : Login sécurisé via `admin` / `pfe2026` pour accéder au tableau de bord.
*   **Téléversement de fichier CSV** : Upload de données de capteurs internes avec contrôle strict côté serveur.
*   **Traitement en mémoire** : Le CSV est parsé et stocké en session Flask pour éviter des requêtes répétitives.
*   **Calcul d'indice d'impact** : Les polluants sont comparés aux seuils critiques recommandés.
*   **Dashboard SSR Premium** :
    *   Filtres et tris applicables côté serveur sans recharger la page complète grâce aux paramètres d'URL.
    *   Visualisations avec des barres de progression en CSS pur (Vert : bon ≤ 50%, Orange : modéré ≤ 100%, Rouge : critique > 100%).
    *   Carte géographique interactive avec marqueurs d'indice de qualité de l'air (générée par Folium).
    *   **Audit de l'IA (Mistral)** : Analyse automatisée et plan de réduction d'émissions généré directement en HTML brut sans markdown parasite.

---

## 🚀 Routes de l'Application

### 🌍 Espace Public
*   `GET /` : Accueil et dashboard principal avec données en temps réel.
*   `GET /analytics` : Graphiques avancés et métriques détaillées.
*   `GET /predictions` : Formulaire interactif effectuant des prédictions de qualité de l'air via le modèle ML entraîné.
*   `GET /chatbot` : Discussion interactive avec le chatbot météo grand public.
*   `GET /news` : Articles et conseils écologiques d'actualité.

### 🏭 Espace Entreprise
*   `GET /entreprise` : Redirige vers `/entreprise/login` ou `/entreprise/upload` selon l'état de la session.
*   `GET /entreprise/login` : Page de connexion B2B.
*   `POST /entreprise/login` : Traitement de la connexion.
*   `GET /entreprise/upload` : Formulaire sécurisé d'upload de fichier CSV pour les entreprises connectées.
*   `POST /entreprise/upload` : Traitement de l'upload, parsing des données CSV, calcul de la pollution et redirection.
*   `GET /entreprise/dashboard` : Dashboard d'analyse de pollution de l'entité avec tris, carte Folium et rapport Mistral AI.
*   `GET /entreprise/logout` : Clôture de la session entreprise.
*   `GET /map-view` : Route interne affichant la carte générée par Folium (utilisée dans l'iframe du Dashboard).

---

## 📊 Format des Fichiers CSV de Test

Le fichier CSV téléversé dans le module entreprise doit posséder des en-têtes (headers) explicites correspondant aux polluants mesurés.

### Colonnes supportées :
*   `pm2_5` : Particules fines PM2.5 (seuil : 35.0 µg/m³)
*   `pm10` : Particules grossières PM10 (seuil : 50.0 µg/m³)
*   `co` : Monoxyde de carbone CO (seuil : 5.0 ppm)
*   `no2` : Dioxyde d'azote NO2 (seuil : 40.0 ppb)
*   `so2` : Dioxyde de soufre SO2 (seuil : 20.0 ppb)
*   `co2` : Dioxyde de carbone CO2 (seuil : 800.0 ppm)

### Exemple de structure de fichier CSV valide :
```csv
timestamp,pm2_5,pm10,co,no2,so2,co2,temperature
2026-06-12 08:00,28.5,45.2,2.3,35.1,12.5,550,22.5
2026-06-12 09:00,32.1,48.7,2.8,38.5,14.2,610,23.1
2026-06-12 10:00,26.8,42.1,2.1,32.8,11.3,520,24.0
```
*Note : Les colonnes non listées ci-dessus (comme timestamp, temperature, etc.) sont ignorées lors du calcul des taux de pollution.*

---

## 🔐 Sécurité et Robustesse

*   **Validation stricte des fichiers** : Seuls les fichiers avec l'extension `.csv` sont acceptés.
*   **Limitation de taille** : Configuration Flask pour rejeter les fichiers volumineux.
*   **Prévention des injections XSS** : Les templates Jinja2 échappent les variables par défaut. Le rapport IA de Mistral est généré sous forme de balises HTML propres filtrées avant d'être marqué comme sûr (`|safe`).
*   **Indépendance Client** : L'absence totale de scripts JS sur l'espace entreprise supprime les vulnérabilités de scripts intersites (XSS client).

---

## 🐛 Dépannage (Troubleshooting)

### ❌ Erreur : "Format de fichier invalide"
Vérifiez que votre fichier possède l'extension `.csv` (en minuscules ou majuscules) et qu'il n'est pas corrompu.

### ❌ Erreur : "Aucun polluant valide détecté dans le CSV"
Assurez-vous que les en-têtes de votre fichier CSV contiennent au moins une des colonnes supportées (`pm2_5`, `pm10`, `co`, `no2`, `so2`, `co2`).

### ❌ Le rapport d'IA affiche "Recommandations indisponibles"
Vérifiez que votre clé `MISTRAL_API_KEY` est correctement configurée dans votre fichier `.env` et que vous disposez d'un accès internet fonctionnel.

### ❌ La carte géographique ne s'affiche pas
Vérifiez que la bibliothèque `folium` est correctement installée dans votre environnement virtuel :
```bash
pip install folium==0.14.0
```
Si Folium n'est pas installé, le dashboard affichera un message d'information alternatif sans bloquer l'application.
