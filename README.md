# 🌍 AirPredict — Système de Surveillance et Prédiction de la Qualité de l'Air

AirPredict (AirWatch) est une application web moderne et robuste basée sur **Flask (Python)** et le **Server-Side Rendering (SSR)**. Elle permet de surveiller la qualité de l'air en temps réel, de prédire l'indice de pollution à l'aide de modèles de Machine Learning, d'agréger des flux d'actualités environnementales et d'accompagner les entreprises industrielles dans leur transition écologique grâce à un chatbot IA (Mistral AI) et un simulateur de décarbonation (**CO2 Wash**).

---

## 📖 Sommaire
1. [✨ Caractéristiques Principales](#-caractéristiques-principales)
2. [🏗️ Architecture & Technologies](#-architecture--technologies)
3. [📁 Structure du Projet & Composants](#-structure-du-projet--composants)
4. [🧠 Module de Machine Learning (ML)](#-module-de-machine-learning-ml)
5. [🏭 Espace Entreprise B2B & CO2 Wash](#-espace-entreprise-b2b--co2-wash)
6. [⚙️ Installation et Configuration](#%EF%B8%8F-installation-et-configuration)
7. [🚀 Démarrage Rapide](#-démarrage-rapide)
8. [📊 Formats des Fichiers CSV](#-formats-des-fichiers-csv)
9. [☁️ Déploiement sur Vercel](#%EF%B8%8F-déploiement-sur-vercel)
10. [🔐 Sécurité, Performance et Caching](#-sécurité-performance-et-caching)
11. [🐛 Dépannage (Troubleshooting)](#-dépannage-troubleshooting)

---

## ✨ Caractéristiques Principales

*   **Rendu Côté Serveur (SSR) & Sans JS (No-JS)** : L'application génère tout le HTML côté serveur, éliminant le besoin de scripts JavaScript complexes côté client. Cela garantit une rapidité maximale, une sécurité accrue et une compatibilité optimale (y compris sur de vieux navigateurs ou des systèmes à faibles ressources comme le Raspberry Pi).
*   **Géolocalisation du Visiteur** : Grâce à l'adresse IP publique du visiteur (détectée via les en-têtes HTTP de reverse proxies comme Cloudflare ou Nginx), le système affiche automatiquement la météo et la carte centrées sur la position de l'utilisateur final.
*   **Modèle Prédictif de Pollution** : Un modèle d'apprentissage automatique basé sur l'algorithme Random Forest estime l'indice de qualité de l'air pour les 24 prochaines heures avec détection des pics critiques.
*   **Assistant IA Météo & Industriel** : Intégration de l'API Mistral AI pour fournir des conseils météo au grand public et des rapports d'audit de décarbonation personnalisés aux industriels.
*   **Simulateur CO2 Wash (Lavage du Carbone)** : Outil d'analyse des émissions de CO2 industrielles brutes et nettes avec estimation du nombre d'arbres équivalents sauvegardés et projection à J+7.

---

## 🏗️ Architecture & Technologies

Le système repose sur un stack technique moderne et allégé :

*   **Backend** : Python 3.10+ & Flask 3.0.0 (gestion du routage, de la session, du parsing des fichiers).
*   **Base de Données** : SQLite 3 (stockage local léger des mesures de qualité de l'air, des alertes et des prédictions).
*   **Machine Learning** : `scikit-learn`, `pandas`, `numpy` et `joblib` pour l'entraînement et la sérialisation du modèle.
*   **Intelligence Artificielle** : Client `mistralai` officiel utilisant le modèle `mistral-small-latest`.
*   **Visualisation Cartographique** : Cartographie interactive générée via Folium avec un repli (fallback) d'image statique généré localement via `staticmap`.
*   **Frontend** : HTML5 sémantique, Jinja2 (moteur de templates) et CSS3 pur. Gestion d'un mode Sombre/Clair persistant via la session Flask.

---

## 📁 Structure du Projet & Composants

```text
versel/
├── 🐍 Code Backend Principal
│   ├── main.py                        # Script d'orchestration principal (multithreading et planificateur)
│   ├── web_server.py                  # Serveur Flask principal (routes web, endpoints API, parsing CSV)
│   ├── database.py                    # Module d'interface CRUD avec la base de données SQLite3
│   ├── config.py                      # Configurations globales du système, seuils AQI et valeurs par défaut
│   ├── ml_model.py                    # Algorithmes ML, feature engineering et prédictions
│   ├── weather_chatbot.py             # Chatbot IA grand public et expert industriel via Mistral AI
│   └── openweather_data_provider.py   # Module de collecte de données météo et AQI via l'API OpenWeatherMap
│
├── 🎨 Interface Utilisateur (Templates HTML & CSS)
│   ├── static/
│   │   └── css/
│   │       ├── dashboard.css          # Design global moderne, responsive et premium
│   │       └── responsive.css         # Adaptations CSS pour mobiles et tablettes
│   └── templates/
│       ├── base.html                  # Squelette HTML global (barre de navigation, pied de page)
│       ├── dashboard.html             # Tableau de bord public (météo, IQA, stats 24h)
│       ├── analytics.html             # Analyses graphiques et liste des évènements NASA
│       ├── map.html                   # Cartographie interactive et image statique
│       ├── news.html                  # Flux d'actualités agrégé
│       ├── predictions.html           # Interface interactive des prédictions et simulateur IQA
│       ├── chatbot.html               # Chatbot météo grand public
│       ├── co2_wash.html              # Tableau de bord CO2 Wash Entreprise
│       ├── login_entreprise.html      # Formulaire de connexion sécurisé B2B
│       ├── entreprise_base.html       # Squelette HTML pour l'espace Entreprise
│       ├── entreprise_upload.html     # Formulaire d'importation de fichiers CSV de pollution
│       ├── entreprise_dashboard.html  # Dashboard de pollution industrielle (tris, carte, rapport Mistral)
│       ├── entreprise_chatbot.html    # Chatbot IA expert en décarbonation
│       ├── entreprise_predictions.html# Projections CO2 Wash à 7 jours
│       └── static_map_render.html     # Conteneur de rendu pour la carte Folium
│
├── 📊 Données & Modèles (Générés localement)
│   ├── data/
│   │   ├── air_quality.db             # Fichier SQLite contenant la base de données
│   │   └── uploads/                   # Répertoire temporaire de réception des imports CSV
│   └── models/
│       ├── air_quality_model.pkl      # Modèle RandomForest sérialisé
│       └── air_quality_model_scaler.pkl # Scaler StandardScaler sérialisé
│
└── ⚙️ Fichiers de Configuration
    ├── requirements.txt               # Dépendances Python du projet
    ├── pyproject.toml                 # Définition du projet et point d'entrée pour le déploiement Vercel
    └── .env                           # Fichier d'environnement local (Clés API secrètes)
```

### Description des fichiers clés :
*   **[main.py](file:///c:/Users/PC/Desktop/pfe10/versel/main.py)** : Démarre le serveur Flask dans un thread séparé et utilise la bibliothèque `schedule` dans le thread principal pour planifier la collecte régulière des données météo (toutes les X secondes), la génération des prédictions ML (toutes les heures) et le nettoyage de la base de données.
*   **[web_server.py](file:///c:/Users/PC/Desktop/pfe10/versel/web_server.py)** : Le cœur applicatif contenant l'ensemble des routes web, le calcul des caches pour les API externes, la géolocalisation IP et le traitement des formulaires d'importation CSV.
*   **[database.py](file:///c:/Users/PC/Desktop/pfe10/versel/database.py)** : Contient la classe `AirQualityDatabase` chargée de créer les tables (`sensor_data`, `predictions`, `alerts`, `calibration`, `users`), de gérer les transactions SQL de façon sécurisée (requêtes paramétrées) et de calculer les statistiques agrégées (min, max, moyennes).
*   **[ml_model.py](file:///c:/Users/PC/Desktop/pfe10/versel/ml_model.py)** : Fichier définissant l'entraînement du modèle Random Forest, le nettoyage et le feature engineering sur les séries temporelles.
*   **[weather_chatbot.py](file:///c:/Users/PC/Desktop/pfe10/versel/weather_chatbot.py)** : Configure les prompts systèmes Mistral AI pour formater directement le texte en HTML brut de façon sécurisée afin de s'intégrer proprement dans l'interface No-JS.

---

## 🧠 Module de Machine Learning (ML)

AirPredict intègre un prédicteur d'indice de qualité de l'air basé sur l'algorithme **Random Forest Regressor** :

### 1. Feature Engineering (Ingénierie des caractéristiques)
Le modèle ne se base pas uniquement sur les valeurs instantanées, mais crée des caractéristiques temporelles avancées :
*   **Variables Temporelles** : Heure de la journée (0-23), Jour de la semaine (0-6), Mois (1-12) pour capturer la saisonnalité et les pics d'activité.
*   **Variables de Décalage (Lag)** : Valeurs de pollution mesurées à $t-1$, $t-2$ et $t-3$ heures.
*   **Statistiques Mobiles (Rolling)** : Moyennes mobiles sur 3h et 6h, ainsi que l'écart-type mobile sur 3h (pour capter la volatilité de la qualité de l'air).

### 2. Entraînement & Fallback
*   **Entraînement** : Le modèle s'entraîne avec 100 estimateurs (arbres) et une profondeur maximale de 15. Si aucune donnée historique n'est présente au premier démarrage, une fonction génère automatiquement 2000 échantillons de données synthétiques réalistes (combinant tendances diurnes et bruit gaussien) pour entraîner le modèle initial.
*   **Mode Simulation / Repli** : Si le chargement des bibliothèques ML échoue ou si le modèle n'est pas encore entraîné (par exemple sur des plateformes à ressources restreintes), le système bascule automatiquement sur un algorithme de simulation de séries temporelles basé sur des fonctions sinusoïdales pour afficher des prévisions réalistes.

---

## 🏭 Espace Entreprise B2B & CO2 Wash

L'espace B2B est accessible à l'adresse `/entreprise`. Il est protégé par un système de session standard (Identifiants par défaut : **`admin` / `pfe2026`**).

### 1. Analyse de Pollution Industrielle (CSV)
Les entreprises téléversent un fichier CSV contenant les relevés de leurs capteurs internes de polluants. Le système calcule la moyenne de chaque polluant et affiche un tableau de bord comparatif indiquant la conformité de l'entreprise par rapport aux seuils critiques internationaux :
*   **PM2.5** (seuil : 35.0 µg/m³)
*   **PM10** (seuil : 50.0 µg/m³)
*   **CO** (seuil : 5.0 ppm)
*   **NO2** (seuil : 40.0 ppb)
*   **SO2** (seuil : 20.0 ppb)
*   **CO2** (seuil : 800.0 ppm)

Un tri interactif côté serveur (par nom, valeur brute ou taux de pollution) permet d'analyser rapidement les facteurs d'impact majeurs. De plus, un **Rapport d'Audit Écologique** complet et personnalisé est généré dynamiquement par Mistral AI à partir de ces données.

### 2. Simulateur de Filtre CO2 Wash
Le module **CO2 Wash** modélise l'efficacité d'un système de lavage/filtrage de CO2 industriel :
*   **Calculs** : À partir des émissions brutes ($kg/h$) importées par CSV, le système applique le taux d'efficacité du filtre pour déterminer les émissions capturées, les émissions nettes rejetées, et l'équivalent en arbres plantés par jour nécessaires pour compenser ce carbone.
*   **Projections à 7 jours** : En analysant la série temporelle du CSV, l'application estime la régression/progression linéaire des émissions brutes et de l'efficacité du filtre pour projeter les émissions sur la semaine à venir.
*   **Exportation** : Les projections calculées peuvent être exportées d'un simple clic au format CSV.

---

## ⚙️ Configuration et Installation

### Prérequis
*   Python 3.10 ou supérieur installé.
*   Un compte et une clé API sur [OpenWeatherMap](https://openweathermap.org/) (Gratuit).
*   Un compte et une clé API sur [Mistral AI](https://console.mistral.ai/) (Indispensable pour le fonctionnement des chatbots et des rapports).

### Étape 1 : Cloner le dépôt et configurer l'environnement virtuel
```bash
# Entrer dans le répertoire du projet
cd versel

# Créer l'environnement virtuel Python
python -m venv .venv

# Activer l'environnement virtuel
# Sur Windows :
.venv\Scripts\activate
# Sur Linux / macOS :
source .venv/bin/activate
```

### Étape 2 : Installer les dépendances nécessaires
```bash
pip install -r requirements.txt
```

### Étape 3 : Configurer les variables d'environnement
Créez un fichier nommé `.env` à la racine du dossier `versel/` et configurez les clés d'API :

```env
# Clé API Mistral AI (Obligatoire pour les Chatbots et Audits)
MISTRAL_API_KEY=votre_cle_mistral_ici

# Clé API OpenWeather (Pour les données réelles de météo et pollution)
OPENWEATHER_API_KEY=votre_cle_openweather_ici

# Clé secrète de session Flask (Indispensable pour chiffrer les cookies de session)
SECRET_KEY=cle_securisee_generique_pfe_2026

# Optionnel : Clé API NewsData.io pour les actualités réelles
NEWSDATA_API_KEY=votre_cle_newsdata_ici

# Optionnel : Clé API NASA pour filtrer les évènements environnementaux proches
NASA_API_KEY=votre_cle_nasa_ici

# Optionnel : Clé API Carbon Interface pour l'équivalent d'émissions réelles
CARBON_INTERFACE_API_KEY=votre_cle_carbon_interface_ici

# Configuration du serveur web
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# Paramètres géographiques par défaut (Casablanca)
MAP_CENTER_LAT=33.565318
MAP_CENTER_LON=-7.663939
WEATHER_DEFAULT_QUERY=Casablanca,MA
```

---

## 🚀 Démarrage Rapide

### Mode 1 : Orchestrateur Complet (Recommandé en local et Raspberry Pi)
Ce mode lance en parallèle les tâches de collecte planifiées en arrière-plan et le serveur Flask.
```bash
python main.py
```

### Mode 2 : Serveur Web Flask Seul (Recommandé pour le débogage simple)
```bash
python web_server.py
```

Une fois démarré, ouvrez votre navigateur et accédez à : **`http://localhost:5000`**

---

## 📊 Formats des Fichiers CSV

Pour importer vos données industrielles dans l'espace Entreprise, vos fichiers doivent respecter les en-têtes suivants :

### 1. Fichier de Pollution Industrielle (`/entreprise/upload`)
Le fichier doit comporter au moins une colonne de polluant parmi les suivantes. Les colonnes non identifiées ou vides sont automatiquement ignorées.

```csv
timestamp,pm2_5,pm10,co,no2,so2,co2,temperature,humidity
2026-06-12 08:00,28.5,45.2,2.3,35.1,12.5,550.0,22.5,48.0
2026-06-12 09:00,32.1,48.7,2.8,38.5,14.2,610.0,23.1,49.5
2026-06-12 10:00,26.8,42.1,2.1,32.8,11.3,520.0,24.0,45.0
```

### 2. Fichier CO2 Wash (`/entreprise/co2-wash`)
Ce fichier permet de suivre les émissions brutes de CO2 et l'efficacité de filtration. Il doit comporter au moins une colonne d'émissions brutes (`gross_emissions_kg_h`, `gross_kg_h` ou `emissions`).

```csv
timestamp,gross_emissions_kg_h,efficiency_percent
2026-06-24 10:00,1240.0,88.5
2026-06-24 11:00,1285.0,89.0
2026-06-24 12:00,1210.0,87.8
```

---

## ☁️ Déploiement sur Vercel

Le projet est configuré pour être déployé en un clic sur Vercel grâce au support des builds de serveurs Python configurés dans le fichier `pyproject.toml` :

```toml
[tool.vercel]
entrypoint = "web_server:app"
```

> [!NOTE]
> Lors d'un déploiement sur Vercel, la base de données SQLite stockée en mémoire disque locale est réinitialisée à chaque redémarrage du conteneur serverless. Pour une production durable, il est conseillé de brancher un service de base de données externe ou d'utiliser le mode lecture seule.

---

## 🔐 Sécurité, Performance et Caching

Afin d'éviter de surcharger les API tierces gratuites et de maximiser la vitesse d'affichage, plusieurs systèmes de cache en mémoire ont été implémentés dans `web_server.py` :

1.  **Cache Météo (10 minutes)** : Met en cache la météo courante d'une position GPS donnée.
2.  **Cache Géolocalisation IP (1 heure)** : Associe l'adresse IP à ses coordonnées GPS pour éviter d'excéder la limite de 45 requêtes par minute de l'API gratuite d'ip-api.com.
3.  **Cache Évènements NASA (6 heures)** : Conserve la liste des évènements climatiques mondiaux récoltés via NASA EONET.
4.  **Cache Actualités (30 minutes)** : Sauvegarde le flux d'actualités généré via NewsData.io ou les flux RSS.
5.  **Sécurisation XSS** : Les templates Jinja2 échappent par défaut les variables. Les blocs HTML générés par Mistral AI sont strictement épurés avant d'être injectés avec le filtre `|safe`.

---

## 🐛 Dépannage (Troubleshooting)

### ❌ Erreur : "Format de fichier invalide" lors de l'upload
Vérifiez que votre fichier possède bien l'extension `.csv` (en minuscules) et qu'il n'est pas corrompu.

### ❌ Erreur : "Aucun polluant valide détecté dans le CSV"
Assurez-vous que la première ligne de votre fichier CSV contient les en-têtes exacts (ex: `pm2_5`, `pm10`, `co`, `no2`, `so2`, `co2`). L'application effectue un nettoyage des espaces et des minuscules, mais les noms de base doivent correspondre.

### ❌ Le rapport d'IA affiche "Service IA temporairement indisponible"
Vérifiez que la clé `MISTRAL_API_KEY` est correctement orthographiée et présente dans le fichier `.env`. Assurez-vous également que la machine dispose d'une connexion Internet active.

### ❌ La carte géographique ne s'affiche pas ou reste statique
Si la bibliothèque `folium` n'est pas installée, le système génère automatiquement une image statique en local via `staticmap`. Si `staticmap` n'est pas non plus disponible, un conteneur SVG stylisé s'affiche pour garantir la fluidité de l'interface utilisateur. Vous pouvez installer folium via :
```bash
pip install folium==0.14.0
```
