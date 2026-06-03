# Module Entreprises & Industries - Guide Complet

## 🎯 Vue d'ensemble

Le module **Entreprises & Industries** permet aux entités (usines, villes, pays) de téléverser des fichiers CSV contenant des données de capteurs de pollution internes et de recevoir :

1. **Dashboard analytique** avec tris/filtres côté serveur
2. **Barres de progression CSS** visualisant les pourcentages de pollution
3. **Recommandations IA (Mistral)** personnalisées pour réduire l'impact environnemental
4. **Carte statique** (Folium) montrant la localisation et l'indice AQI

## 📋 Architecture SSR (Server-Side Rendering)

**Aucun JavaScript** n'est utilisé. Tous les tris, filtres et affichages sont gérés côté serveur Python :

- **Parsing CSV** : `parse_csv_pollution_data()` calcule les moyennes et pourcentages
- **Tri** : Paramètres URL (`?sort_by=rate&order=desc`) traités en Python
- **Barres CSS** : Largeur contrôlée par Jinja2 `{{ facteur.pourcentage }}%`
- **Carte Folium** : Générée côté serveur, sauvegardée en HTML statique

## 🚀 Routes de l'application

### 1. `GET /entreprise`
**Page d'accueil** avec formulaire d'upload CSV

**Paramètres formulaire :**
- `entity_name` (str) : Nom de l'entité (ex. "Usine Nord Casablanca")
- `entity_type` (select) : "Usine", "Ville" ou "Pays"
- `file` (file) : Fichier CSV (.csv uniquement)

**Redirection :**
- Succès → `/entreprise/dashboard`
- Erreur → `/entreprise?error=...`

---

### 2. `POST /entreprise/upload`
**Traitement du fichier CSV**

**Workflow :**
1. Valide l'extension (.csv uniquement)
2. Appelle `parse_csv_pollution_data()` pour analyser le CSV
3. Calcule la moyenne de chaque polluant (pm2_5, pm10, co, no2, so2, co2)
4. Calcule le pourcentage par rapport aux seuils critiques AQI
5. Stocke les résultats en **session Flask** (évite re-parsing)
6. Redirige vers `/entreprise/dashboard`

**Exemple de sortie `parse_csv_pollution_data()` :**
```python
{
    'success': True,
    'average_factors': {
        'pm2_5': 30.14,
        'pm10': 47.25,
        'co': 2.6,
        'no2': 37.14,
        'so2': 13.36,
        'co2': 590.0
    },
    'pollution_summary': {
        'PM2.5': 86.1,  # 30.14 / 35.0 * 100
        'PM10': 94.5,   # 47.25 / 50.0 * 100
        'CO': 52.0,     # 2.6 / 5.0 * 100
        'NO2': 92.9,    # 37.14 / 40.0 * 100
        'SO2': 66.8,    # 13.36 / 20.0 * 100
        'CO2': 73.8     # 590.0 / 800.0 * 100
    },
    'num_records': 10
}
```

---

### 3. `GET /entreprise/dashboard`
**Dashboard analytique avec tris/filtres**

**Paramètres URL (optionnels) :**
- `sort_by` : "name", "rate" ou "value" (tri des polluants)
- `order` : "asc" ou "desc" (ordre croissant/décroissant)

**Exemple :**
```
GET /entreprise/dashboard?sort_by=rate&order=desc
```

**Processus côté serveur :**
1. Récupère les données stockées en **session**
2. Applique le tri Python sur `pollution_items`
3. Appelle `chatbot.generate_industrial_recommendations()` (Mistral AI)
4. Génère la carte Folium via `generate_folium_map()`
5. Retourne le template avec toutes les données

**Données transmises au template :**
```python
{
    'entity_name': 'Usine Nord Casablanca',
    'entity_type': 'Usine',
    'pollution_items': [  # Déjà triés
        {
            'name': 'PM2.5',
            'percentage': 86.1,
            'value': 30.14,
            'color_threshold': '#ef4444'  # Rouge
        },
        # ...
    ],
    'ai_report': '<h3>...</h3><p>...</p><ul>...',  # HTML brut
    'stats': {
        'total_pollutants': 6,
        'average_pollution': 77.7,
        'max_pollution': 94.5,
        'num_records_analyzed': 10
    },
    'sort_by': 'rate',
    'order': 'desc',
    'map_file': '/path/to/static_map_render.html'
}
```

---

### 4. `GET /map-view`
**Affiche la carte Folium générée** (utilisée en iframe dans le dashboard)

## 📊 Format CSV attendu

Le CSV doit contenir au minimum une ou plusieurs des colonnes suivantes :

| Colonne | Type | Unité | Seuil critique |
|---------|------|-------|----------------|
| pm2_5 | float | µg/m³ | 35 µg/m³ |
| pm10 | float | µg/m³ | 50 µg/m³ |
| co | float | ppm | 5 ppm |
| no2 | float | ppb | 40 ppb |
| so2 | float | ppb | 20 ppb |
| co2 | float | ppm | 800 ppm |

**Exemple de CSV valide :**
```csv
timestamp,pm2_5,pm10,co,no2,so2,co2,temperature,humidity
2024-01-15 08:00:00,28.5,45.2,2.3,35.1,12.5,550,22.5,65
2024-01-15 09:00:00,32.1,48.7,2.8,38.5,14.2,610,23.1,62
```

Les colonnes supplémentaires (timestamp, temperature, humidity) sont ignorées.

## 🤖 Recommandations Mistral IA

**Méthode :** `WeatherChatbot.generate_industrial_recommendations()`

**Prompt système :**
```
Vous êtes un Expert senior en ingénierie environnementale et décarbonation industrielle...
```

**Entrées :**
- `entity_name` : Nom de l'entité
- `entity_type` : Type (Usine, Ville, Pays)
- `pollution_summary` : Dict des polluants en % du seuil critique

**Sortie :**
- HTML brut (`<h3>`, `<p>`, `<ul>`, `<li>`, `<strong>` uniquement)
- Pas de bloc Markdown
- ~600 tokens max

**Exemple de rapport IA :**
```html
<h3>Analyse du profil de pollution — Usine Nord Casablanca</h3>
<p>Votre entité affiche des niveaux de pollution <strong>élevés</strong> pour la majorité des polluants. PM2.5 (86%), PM10 (94%) et NO2 (92%) dépassent largement les seuils critiques...</p>

<h3>Plan d'action prioritaire</h3>
<ul>
<li><strong>1. Filtration avancée des particules fines (PM2.5/PM10)</strong> — Installation de filtres HEPA multi-étages ciblant la réduction de 50% en 3 mois.</li>
...
</ul>

<h3>Indicateurs de suivi recommandés</h3>
<ul>
<li>Mesurer PM2.5 hebdomadaire (objectif : &lt; 35 µg/m³)</li>
...
</ul>
```

## 🗺️ Carte Folium (Optionnelle)

**Fonction :** `generate_folium_map()`

Si **Folium n'est pas installé**, la carte est simplement ignorée.

**Installation :**
```bash
pip install folium==0.14.0
```

**Fonctionnalités de la carte :**
- 🎯 Marqueur coloré selon l'AQI (vert/jaune/orange/rouge)
- 🔴 Cercle de rayon proportionnel à la pollution
- 📍 Pop-up avec nom, type et AQI

## 💾 Stockage en Session

Pour éviter de re-parser le CSV à chaque clic de tri, les données sont stockées en **session Flask** :

```python
session['entreprise_data'] = {
    'entity_name': 'Usine Nord',
    'entity_type': 'Usine',
    'pollution_summary': {...},
    'average_factors': {...},
    'num_records': 10,
    'upload_timestamp': '2024-01-15T14:30:00'
}
```

Durée : Jusqu'à la fermeture de la session utilisateur (par défaut 30 minutes).

## 🔒 Sécurité

✅ **Extensions validées** : Uniquement `.csv`  
✅ **Taille fichier** : Vérifiée par Flask (max 16MB par défaut)  
✅ **CSV injection** : Mitigée par `csv.DictReader()`  
✅ **HTML injection (rapport IA)** : Filtrage Mistral + injection sécurisée via Jinja2 `|safe`  
✅ **XSS** : Aucune, pas de JS côté client

## 📝 Fichier d'exemple

Un CSV de test est fourni : `data/uploads/sample_pollution_data.csv`

**Étapes de test :**
1. Aller sur `GET /entreprise`
2. Remplir le formulaire (ex. "Test Casablanca", type "Ville")
3. Uploader `sample_pollution_data.csv`
4. Observer le dashboard avec barres CSS et rapport IA
5. Cliquer sur les boutons de tri pour voir le changement côté serveur

## 🛠️ Troubleshooting

### Erreur "Format fichier invalide"
- Vérifier que le fichier a l'extension `.csv`
- Vérifier l'encoding (UTF-8)

### Erreur "Le fichier CSV est vide"
- Vérifier que le CSV contient des données

### Carte non affichée
- Installer folium : `pip install folium==0.14.0`
- Vérifier les logs pour erreurs Folium

### Rapport IA non généré
- Vérifier la clé API Mistral dans `.env`
- Vérifier la limite d'appels API Mistral

## 📚 Fichiers impliqués

```
versel/
├── config.py                          # ✅ Config UPLOAD_FOLDER + ALLOWED_EXTENSIONS
├── weather_chatbot.py                 # ✅ Nouvelle méthode generate_industrial_recommendations()
├── web_server.py                      # ✅ Nouvelles routes + parsing CSV
├── requirements.txt                   # ✅ Ajout de folium
├── templates/
│   ├── entreprise_upload.html        # ✅ Formulaire d'upload (SSR, CSS pur)
│   ├── entreprise_dashboard.html     # ✅ Dashboard avec barres CSS (SSR, CSS pur)
│   └── static_map_render.html        # ✅ Placeholder carte Folium
└── data/
    └── uploads/
        └── sample_pollution_data.csv  # ✅ Fichier de test
```

## 🚢 Déploiement

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. S'assurer que le dossier uploads existe
mkdir -p data/uploads

# 3. Configurer la clé Mistral API dans .env
echo "MISTRAL_API_KEY=votre_clé_api" >> .env

# 4. Démarrer le serveur
python web_server.py

# 5. Accéder à la page
# https://localhost:5000/entreprise
```

---

**Version :** 2026-01-15  
**Auteur :** AirWatch Engineering Team  
**Contrainte :** Aucun JavaScript, SSR uniquement, CSS pur
