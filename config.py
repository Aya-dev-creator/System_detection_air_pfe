"""
Configuration centrale du système de surveillance de qualité de l'air
Gère toutes les variables d'environnement et paramètres du système

Ce fichier est le point central de configuration pour toute l'application.
Il charge les variables depuis le fichier .env et fournit des valeurs par défaut.
Chaque section du fichier correspond à un composant du système.
"""
import os  # Module pour accéder aux variables d'environnement du système
from dotenv import load_dotenv  # Bibliothèque pour charger les variables depuis .env

# Charger les variables d'environnement depuis le fichier .env
# Le fichier .env contient les clés API, mots de passe, et configurations sensibles
# qui ne doivent pas être commités dans Git (voir .gitignore)
load_dotenv()

class Config:
    """
    Classe de configuration principale pour tout le système
    
    Cette classe contient tous les paramètres de configuration sous forme de
    dictionnaires et variables de classe. Chaque section correspond à un
    composant du système (base de données, capteurs, web, email, etc.)
    """
    
    # ============= CONFIGURATION BASE DE DONNÉES (SQLite3) =============
    # SQLite est une base de données légère qui stocke tout dans un seul fichier
    # Idéale pour Raspberry Pi car elle ne nécessite pas de serveur séparé
    DB_CONFIG = {
        # Chemin vers le fichier de base de données
        # Par défaut: ./data/air_quality.db (dans le dossier data du projet)
        'db_path': os.getenv('DB_PATH', './data/air_quality.db')
    }
    
    # ============= CONFIGURATION DES CAPTEURS (GPIO) =============
    # Ces paramètres définissent comment les capteurs sont connectés au Raspberry Pi
    # GPIO = General Purpose Input/Output (broches d'entrée/sortie)
    SENSOR_CONFIG = {
        # Numéro de la broche GPIO pour le capteur DHT11 (température/humidité)
        # Par défaut: GPIO 4 (broche physique 7 sur Raspberry Pi)
        'dht11_pin': int(os.getenv('DHT11_PIN', 4)),
        
        # Numéro de la broche GPIO pour le capteur MQ-135 (qualité de l'air)
        # Note: MQ-135 utilise un ADC (convertisseur analogique-numérique) comme ADS1115
        # Par défaut: GPIO 17 (broche physique 11)
        'mq135_pin': int(os.getenv('MQ135_PIN', 17)),
        
        # Active ou désactive le module GPS NEO-6M
        # 'true' = GPS activé, 'false' = GPS désactivé
        # Utile pour économiser de l'énergie si le GPS n'est pas connecté
        'gps_enabled': os.getenv('GPS_ENABLED', 'true').lower() == 'true',
        
        # Intervalle de lecture des capteurs en secondes
        # Combien de temps attendre entre deux lectures de tous les capteurs
        # Par défaut: 60 secondes (1 minute)
        'read_interval': int(os.getenv('SENSOR_READ_INTERVAL', 60))
    }
    
    # ============= SEUILS DE QUALITÉ DE L'AIR =============
    # Ces seuils définissent les niveaux de qualité de l'air basés sur l'AQI (Air Quality Index)
    # L'AQI est une échelle internationale pour mesurer la pollution atmosphérique
    # Valeurs en PPM (parts per million) pour le capteur MQ-135
    AIR_QUALITY_THRESHOLDS = {
        # Seuil pour qualité "Bon" (0-50 PPM)
        # Air satisfaisant, pollution faible ou nulle
        'good': int(os.getenv('THRESHOLD_GOOD', 50)),
        
        # Seuil pour qualité "Modéré" (51-100 PPM)
        # Qualité acceptable, pollution modérée
        'moderate': int(os.getenv('THRESHOLD_MODERATE', 100)),
        
        # Seuil pour qualité "Mauvais pour groupes sensibles" (101-150 PPM)
        # Les personnes sensibles (asthme, allergies) peuvent ressentir des effets
        'unhealthy': int(os.getenv('THRESHOLD_UNHEALTHY', 150)),
        
        # Seuil pour qualité "Mauvais" (151-200 PPM)
        # Tout le monde peut commencer à ressentir des effets
        'very_unhealthy': int(os.getenv('THRESHOLD_VERY_UNHEALTHY', 200)),
        
        # Seuil pour qualité "Très mauvais" (201-300 PPM)
        # Alerte sanitaire, effets plus graves pour la population
        'hazardous': int(os.getenv('THRESHOLD_HAZARDOUS', 300))
    }
    
    # ============= CONFIGURATION SERVEUR WEB =============
    # Configuration du serveur Flask qui fournit l'interface web et l'API REST
    FLASK_CONFIG = {
        # Adresse IP sur laquelle le serveur écoute
        # '0.0.0.0' = écoute sur toutes les interfaces (accessible depuis le réseau)
        # '127.0.0.1' = écoute uniquement en local (localhost)
        'host': os.getenv('FLASK_HOST', '0.0.0.0'),
        
        # Port TCP sur lequel le serveur écoute
        # Par défaut: 5000 (port standard pour Flask en développement)
        'port': int(os.getenv('FLASK_PORT', 5000)),
        
        # Mode debug: active le rechargement automatique et les messages d'erreur détaillés
        # 'true' = mode développement (NE PAS utiliser en production)
        # 'false' = mode production
        'debug': os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        
        # Clé secrète pour sécuriser les sessions Flask
        # DOIT être changée en production pour éviter les attaques
        'secret_key': os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    }
    
    # ============= CONFIGURATION EMAIL (ALERTES) =============
    # Configuration pour envoyer des alertes par email quand la qualité de l'air est mauvaise
    EMAIL_CONFIG = {
        # Serveur SMTP pour l'envoi d'emails
        # Par défaut: smtp.gmail.com (serveur SMTP de Gmail)
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        
        # Port SMTP (587 = STARTTLS, 465 = SSL)
        # 587 est le port standard pour Gmail avec STARTTLS
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        
        # Nom d'utilisateur pour l'authentification SMTP
        # Pour Gmail: votre adresse email complète
        'username': os.getenv('SMTP_USERNAME', ''),
        
        # Mot de passe pour l'authentification SMTP
        # Pour Gmail: utilisez un "mot de passe d'application" (pas votre mot de passe Google)
        'password': os.getenv('SMTP_PASSWORD', ''),
        
        # Adresse email qui recevra les alertes
        # Peut être la même que le username ou une adresse différente
        'alert_email': os.getenv('ALERT_EMAIL', ''),
        
        # Active ou désactive l'envoi d'emails
        # 'true' si un username SMTP est configuré, 'false' sinon
        'enabled': bool(os.getenv('SMTP_USERNAME'))
    }
    
    # ============= LOCALISATION (carte / météo par défaut) =============
    # Ces paramètres définissent la localisation par défaut pour la carte et la météo
    # Centre carte : météo OpenWeather (ville ci-dessous) sauf si MAP_FOLLOW_GPS=true
    WEATHER_DEFAULT_QUERY = os.getenv('WEATHER_DEFAULT_QUERY', 'Casablanca,MA')
    # Coordonnées GPS du centre de la carte (latitude, longitude)
    # Par défaut: Casablanca, Maroc (33.5731°N, 7.5898°W)
    MAP_CENTER_LAT = float(os.getenv('MAP_CENTER_LAT', '33.5731'))
    MAP_CENTER_LON = float(os.getenv('MAP_CENTER_LON', '-7.5898'))
    
    # Si 'true', la carte est toujours centrée sur le GPS du capteur
    # Même si le GPS est loin de la ville configurée (utile pour les capteurs mobiles)
    # 'false' = centre sur la ville configurée, utilise GPS seulement s'il est proche
    MAP_FOLLOW_GPS = os.getenv('MAP_FOLLOW_GPS', 'false').lower() in ('1', 'true', 'yes')
    
    # Distance maximale (en km) entre le GPS du capteur et le centre de la ville
    # Si le GPS est plus loin que cette distance, il est ignoré (évite les faux fixes GPS)
    # Par exemple: si le capteur est à Casablanca mais le GPS indique Tunis (320 km), on ignore le GPS
    MAP_GPS_MAX_DISTANCE_KM = float(os.getenv('MAP_GPS_MAX_DISTANCE_KM', '320'))

    # ============= PARAMÈTRES DU MODÈLE ML =============
    # Configuration pour le modèle de Machine Learning qui prédit la qualité de l'air
    ML_CONFIG = {
        # Chemin vers le fichier du modèle ML entraîné (format pickle)
        # Le modèle est sauvegardé après l'entraînement pour être réutilisé
        'model_path': './models/air_quality_model.pkl',
        
        # Chemin vers le fichier du scaler (normalisation des données)
        # Le scaler transforme les données pour qu'elles soient sur la même échelle
        'scaler_path': './models/scaler.pkl',
        
        # Chemin vers le fichier de données d'entraînement (format CSV)
        # Contient les données historiques utilisées pour entraîner le modèle
        'training_data_path': './data/training_data.csv',
        
        # Intervalle de ré-entraînement du modèle en heures
        # Le modèle est ré-entraîné périodiquement avec les nouvelles données
        # Par défaut: toutes les 24 heures
        'retrain_interval_hours': 24,
        
        # Fenêtre de prédiction en heures
        # Le modèle prédit la qualité de l'air pour les X prochaines heures
        # Par défaut: prédiction sur 24 heures
        'prediction_window_hours': 24
    }

    # ============= CONFIGURATION NASA (Données environnementales) =============
    # Configuration pour l'API NASA EONET (Earth Observatory Natural Event Tracker)
    # Fournit des données sur les événements environnementaux (feux, tempêtes, etc.)
    NASA_CONFIG = {
        # Clé API pour accéder à l'API NASA
        # Essayez d'abord la variable standard NASA_API_KEY, puis l'ancienne variable nasaapi
        # Si aucune n'est configurée, la chaîne vide est utilisée (pas d'accès à l'API)
        'api_key': os.getenv('NASA_API_KEY', os.getenv('nasaapi', ''))
    }
    
    # ============= CONFIGURATION HUGGING FACE (Assistant IA) =============
    # Configuration pour l'assistant IA utilisant Hugging Face
    # Hugging Face propose des modèles de langage gratuits via leur API
    # Modèle : carte Hub « Inference » / petits instruct (voir https://huggingface.co/models )
    # Défaut : SmolLM2-1.7B-Instruct — léger, adapté au routeur serverless HF.
    HF_CONFIG = {
        # Clé API pour accéder à l'API Hugging Face
        # Optionnel: sans clé, certaines fonctionnalités sont limitées
        'api_key': os.getenv('HF_API_KEY', ''),
        
        # Nom du modèle de chat à utiliser
        # SmolLM2-1.7B-Instruct est un modèle léger (1.7 milliards de paramètres)
        # Idéal pour Raspberry Pi car il consomme peu de ressources
        'chat_model': os.getenv(
            'HF_CHAT_MODEL',
            'HuggingFaceTB/SmolLM2-1.7B-Instruct',
        ),
        
        # URL de l'endpoint de chat Hugging Face
        # Utilise le routeur serverless qui redirige vers le modèle approprié
        'chat_url': os.getenv(
            'HF_CHAT_URL',
            'https://router.huggingface.co/v1/chat/completions',
        ),
    }

    # ============= OPENAI (repli assistant si Hugging Face renvoie 404 / erreur) =============
    # Configuration pour l'API OpenAI (ChatGPT) comme fallback si Hugging Face échoue
    # OpenAI est payant mais offre des modèles plus performants
    OPENAI_CONFIG = {
        # Clé API pour accéder à l'API OpenAI
        # Nécessaire pour utiliser ChatGPT
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        
        # Nom du modèle ChatGPT à utiliser
        # gpt-4o-mini est le modèle le plus économique et rapide
        'chat_model': os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini'),
        
        # URL de l'endpoint de chat OpenAI
        # Endpoint officiel de l'API OpenAI
        'chat_url': os.getenv(
            'OPENAI_CHAT_URL',
            'https://api.openai.com/v1/chat/completions',
        ),
    }

    # ============= GROQ (API compatible OpenAI, compte gratuit sur console.groq.com) =============
    # Groq propose des modèles LLaMA gratuits et très rapides
    # API compatible OpenAI, donc facile à intégrer comme fallback
    # Utile si Hugging Face renvoie 404 (modèle indisponible)
    GROQ_CONFIG = {
        # Clé API pour accéder à l'API Groq
        # Gratuite sur console.groq.com
        'api_key': os.getenv('GROQ_API_KEY', ''),
        
        # Nom du modèle Groq à utiliser
        # llama-3.1-70b-versatile est un modèle performant (70 milliards de paramètres)
        'chat_model': os.getenv('GROQ_CHAT_MODEL', 'llama-3.1-70b-versatile'),
        
        # URL de l'endpoint de chat Groq
        # API compatible OpenAI, même format de requête/réponse
        'chat_url': os.getenv(
            'GROQ_CHAT_URL',
            'https://api.groq.com/openai/v1/chat/completions',
        ),
    }
    
    @staticmethod
    def get_air_quality_level(value):
        """
        Détermine le niveau de qualité de l'air basé sur la valeur mesurée
        
        Args:
            value (float): Valeur mesurée par le capteur MQ-135 (PPM)
        
        Returns:
            dict: Niveau, couleur et description de la qualité
        """
        try:
            value = float(value) if value is not None else 0
        except (TypeError, ValueError):
            value = 0
        thresholds = Config.AIR_QUALITY_THRESHOLDS
        
        if value <= thresholds['good']:
            return {
                'level': 'Bon',
                'color': '#00E400',
                'description': 'Qualité de l\'air satisfaisante, pollution faible ou nulle'
            }
        elif value <= thresholds['moderate']:
            return {
                'level': 'Modéré',
                'color': '#FFFF00',
                'description': 'Qualité acceptable, pollution modérée'
            }
        elif value <= thresholds['unhealthy']:
            return {
                'level': 'Mauvais pour groupes sensibles',
                'color': '#FF7E00',
                'description': 'Les personnes sensibles peuvent ressentir des effets'
            }
        elif value <= thresholds['very_unhealthy']:
            return {
                'level': 'Mauvais',
                'color': '#FF0000',
                'description': 'Tout le monde peut commencer à ressentir des effets'
            }
        elif value <= thresholds['hazardous']:
            return {
                'level': 'Très mauvais',
                'color': '#8F3F97',
                'description': 'Alerte sanitaire, effets plus graves'
            }
        else:
            return {
                'level': 'Dangereux',
                'color': '#7E0023',
                'description': 'Alerte d\'urgence, toute la population est affectée'
            }

# Instance globale de configuration
config = Config()