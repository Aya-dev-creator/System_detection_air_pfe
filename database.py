"""
Module de gestion de la base de données SQLite3
Gère toutes les opérations CRUD pour les données de qualité de l'air

Ce module fournit une interface pour interagir avec la base de données SQLite3
qui stocke toutes les données du système:
- Données des capteurs (qualité de l'air, température, humidité, GPS)
- Prédictions du modèle ML
- Alertes déclenchées
- Données de calibration des capteurs
- Utilisateurs du système

SQLite est choisi car:
- C'est une base de données légère (un seul fichier)
- Idéale pour Raspberry Pi (pas de serveur séparé)
- Supporte les requêtes SQL standard
- Fiable et performante pour les petites/moyennes applications

Architecture:
- AirQualityDatabase: Classe principale qui gère toutes les opérations DB
- Tables: sensor_data, predictions, alerts, calibration, users
- Index: Pour améliorer les performances des requêtes fréquentes
"""

import sqlite3  # Module pour interagir avec SQLite3
from datetime import datetime, timedelta  # Modules pour manipuler les dates et heures
import logging  # Module pour la journalisation
from config import config  # Configuration centrale du système

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirQualityDatabase:
    """
    Classe pour gérer toutes les interactions avec la base de données
    
    Cette classe fournit une interface orientée objet pour interagir avec SQLite3.
    Elle encapsule toutes les opérations CRUD (Create, Read, Update, Delete)
    et gère la connexion à la base de données.
    
    Méthodes principales:
    - connect(): Établit la connexion à la base de données
    - create_tables(): Crée toutes les tables nécessaires
    - insert_sensor_data(): Insère des données de capteurs
    - get_latest_readings(): Récupère les dernières lectures
    - get_statistics(): Calcule des statistiques
    - insert_prediction(): Insère une prédiction ML
    - insert_alert(): Insère une alerte
    - get_active_alerts(): Récupère les alertes actives
    - resolve_alert(): Marque une alerte comme résolue
    - close(): Ferme la connexion à la base de données
    """
    
    def __init__(self, db_path='air_quality.db'):
        """
        Initialise la connexion à la base de données
        
        Cette méthode est appelée lors de la création de l'instance.
        Elle stocke le chemin du fichier de base de données mais n'établit
        pas encore la connexion (cela se fait via connect()).
        
        Args:
            db_path (str): Chemin vers le fichier de base de données SQLite
                          Par défaut: 'air_quality.db' dans le répertoire courant
        
        Note:
            La connexion n'est pas établie immédiatement pour éviter
            les erreurs si le fichier n'existe pas encore.
        """
        self.db_path = db_path  # Stocker le chemin du fichier DB
        self.connection = None  # Connexion sera établie plus tard via connect()
    
    def connect(self):
        """
        Établit la connexion à la base de données SQLite
        
        Cette méthode crée le fichier de base de données s'il n'existe pas
        et établit la connexion. Elle configure également des options
        importantes pour le bon fonctionnement de la base de données.
        
        Configuration:
        - check_same_thread=False: Permet d'utiliser la connexion depuis plusieurs threads
        - foreign_keys=ON: Active les contraintes de clés étrangères
        - row_factory=sqlite3.Row: Retourne les résultats comme dictionnaires (plus facile à utiliser)
        
        Returns:
            bool: True si la connexion a réussi, False sinon
        
        Note:
            Cette méthode doit être appelée avant toute autre opération sur la base de données.
        """
        try:
            # Établir la connexion au fichier SQLite
            # check_same_thread=False permet d'utiliser la connexion depuis plusieurs threads
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # Activer les clés étrangères pour garantir l'intégrité référentielle
            # Cela empêche de supprimer des données référencées par d'autres tables
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Configurer row_factory pour retourner les résultats comme dictionnaires
            # Cela permet d'accéder aux colonnes par leur nom (ex: row['air_quality_ppm'])
            # au lieu de leur index (ex: row[2])
            self.connection.row_factory = sqlite3.Row
            
            logger.info("✓ Connexion à la base de données établie avec succès")
            return True
        except Exception as e:
            logger.error(f"✗ Erreur de connexion à la base de données: {e}")
            return False
    
    def create_tables(self):
        """
        Crée toutes les tables nécessaires pour le système
        
        Cette méthode crée toutes les tables de la base de données si elles
        n'existent pas déjà. Utilise "IF NOT EXISTS" pour éviter les erreurs
        si les tables existent déjà.
        
        Tables créées:
        1. sensor_data: Stocke les lectures des capteurs (MQ-135, DHT11, GPS)
        2. predictions: Stocke les prédictions du modèle ML
        3. alerts: Stocke les alertes déclenchées par le système
        4. calibration: Stocke les données de calibration des capteurs
        
        Index créés:
        - idx_sensor_timestamp: Accélère les requêtes sur les données capteurs par date
        - idx_predictions_time: Accélère les requêtes sur les prédictions par date
        - idx_alerts_created: Accélère les requêtes sur les alertes par date
        
        Returns:
            bool: True si les tables ont été créées avec succès, False sinon
        """
        try:
            cursor = self.connection.cursor()
            
            # ============= TABLE PRINCIPALE: DONNÉES CAPTEURS =============
            # Cette table stocke toutes les lectures des capteurs
            # Chaque ligne représente une lecture à un instant donné
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID unique auto-incrémenté
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Heure de la lecture
                    air_quality_ppm REAL NOT NULL,  -- Qualité de l'air en PPM (MQ-135)
                    temperature REAL NOT NULL,  -- Température en °C (DHT11)
                    humidity REAL NOT NULL,  -- Humidité en % (DHT11)
                    latitude REAL,  -- Latitude GPS (optionnel)
                    longitude REAL,  -- Longitude GPS (optionnel)
                    air_quality_level TEXT,  -- Niveau de qualité (ex: 'Bon', 'Modéré')
                    air_quality_color TEXT,  -- Couleur associée (ex: '#00E400')
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Heure d'insertion
                );
            """)
            
            # ============= TABLE DES PRÉDICTIONS ML =============
            # Cette table stocke les prédictions du modèle ML
            # Chaque ligne représente une prédiction pour une heure future
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID unique auto-incrémenté
                    prediction_time TIMESTAMP NOT NULL,  -- Heure où la prédiction a été faite
                    predicted_for TIMESTAMP NOT NULL,  -- Heure pour laquelle la prédiction est faite
                    predicted_aqi REAL NOT NULL,  -- Valeur AQI prédite
                    confidence_score REAL,  -- Score de confiance du modèle (0-1)
                    model_version TEXT,  -- Version du modèle utilisé (ex: 'RF_v1.0')
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Heure d'insertion
                );
            """)
            
            # ============= TABLE DES ALERTES =============
            # Cette table stocke toutes les alertes déclenchées par le système
            # Les alertes peuvent être actives (resolved=0) ou résolues (resolved=1)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID unique auto-incrémenté
                    alert_type TEXT NOT NULL,  -- Type d'alerte (ex: 'HIGH_POLLUTION')
                    severity TEXT NOT NULL,  -- Sévérité (ex: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
                    message TEXT NOT NULL,  -- Message descriptif de l'alerte
                    air_quality_value REAL,  -- Valeur qui a déclenché l'alerte
                    latitude REAL,  -- Latitude où l'alerte a été déclenchée
                    longitude REAL,  -- Longitude où l'alerte a été déclenchée
                    resolved INTEGER DEFAULT 0,  -- 0 = active, 1 = résolue
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Heure de création
                    resolved_at TIMESTAMP  -- Heure de résolution (NULL si active)
                );
            """)
            
            # ============= TABLE DE CALIBRATION =============
            # Cette table stocke les données de calibration des capteurs
            # Utile pour ajuster les lectures des capteurs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calibration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID unique auto-incrémenté
                    sensor_type TEXT NOT NULL,  -- Type de capteur (ex: 'MQ135', 'DHT11')
                    calibration_factor REAL NOT NULL,  -- Facteur de multiplication
                    offset REAL DEFAULT 0,  -- Offset à ajouter
                    notes TEXT,  -- Notes sur la calibration
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Heure de création
                );
            """)
            
            # ============= CRÉATION DES INDEX =============
            # Les index améliorent les performances des requêtes fréquentes
            # Ils accélèrent les recherches sur les colonnes indexées
            
            # Index sur le timestamp des données capteurs (pour les requêtes par date)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sensor_timestamp
                ON sensor_data(timestamp DESC);
            """)
            
            # Index sur l'heure prédite (pour les requêtes de prédictions)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_predictions_time
                ON predictions(predicted_for DESC);
            """)
            
            # Index sur la date de création des alertes (pour les requêtes d'alertes)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_created
                ON alerts(created_at DESC);
            """)
            
            # Valider toutes les modifications
            self.connection.commit()
            logger.info("✓ Toutes les tables ont été créées avec succès")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la création des tables: {e}")
            self.connection.rollback()  # Annuler les modifications en cas d'erreur
            return False
    
    def upsert_user(self, name, email):
        """
        Crée ou met à jour un utilisateur (identifié par email).
        
        Cette méthode utilise une opération "upsert" (insert or update):
        - Si l'email n'existe pas: crée un nouvel utilisateur
        - Si l'email existe déjà: met à jour le nom de l'utilisateur
        
        L'email est utilisé comme identifiant unique (UNIQUE constraint).
        
        Args:
            name (str): Nom complet de l'utilisateur
            email (str): Adresse email (doit être unique)
        
        Returns:
            int: ID de l'utilisateur inséré ou mis à jour, ou None si erreur
        """
        try:
            cursor = self.connection.cursor()
            
            # Créer la table users si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID unique auto-incrémenté
                    name TEXT NOT NULL,  -- Nom complet de l'utilisateur
                    email TEXT NOT NULL UNIQUE,  -- Email unique (identifiant)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Heure de création
                );
            """)
            
            # Insérer ou mettre à jour l'utilisateur
            # ON CONFLICT(email) DO UPDATE: Si l'email existe déjà, met à jour le nom
            # excluded.name fait référence au nouveau nom fourni dans l'INSERT
            cursor.execute("""
                INSERT INTO users (name, email)
                VALUES (?, ?)
                ON CONFLICT(email) DO UPDATE SET name=excluded.name;
            """, (name, email))
            
            self.connection.commit()
            user_id = cursor.lastrowid  # Récupérer l'ID de l'utilisateur
            logger.info(f"✓ Utilisateur enregistré/ajouté: {email}")
            return user_id
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'enregistrement de l'utilisateur: {e}")
            self.connection.rollback()  # Annuler les modifications en cas d'erreur
            return None
    
    def insert_sensor_data(self, air_quality, temperature, humidity, latitude=None, longitude=None):
        """
        Insère une nouvelle lecture de capteur dans la base de données
        
        Cette méthode insère les données des capteurs dans la table sensor_data.
        Elle calcule automatiquement le niveau de qualité de l'air et la couleur
        associée en utilisant la fonction config.get_air_quality_level().
        
        Args:
            air_quality (float): Valeur du capteur MQ-135 en PPM (parts per million)
            temperature (float): Température en degrés Celsius
            humidity (float): Humidité relative en pourcentage
            latitude (float): Latitude GPS (optionnel, None si pas de GPS)
            longitude (float): Longitude GPS (optionnel, None si pas de GPS)
        
        Returns:
            int: ID de l'enregistrement inséré, ou None si erreur
        
        Note:
            Le niveau de qualité de l'air et la couleur sont calculés automatiquement
            à partir de la valeur air_quality en utilisant les seuils configurés.
        """
        try:
            cursor = self.connection.cursor()
            
            # Déterminer le niveau de qualité de l'air et la couleur associée
            # Cette fonction utilise les seuils configurés dans config.py
            quality_info = config.get_air_quality_level(air_quality)
            
            # Préparer la requête SQL d'insertion
            # Les paramètres sont passés sous forme de tuple pour éviter les injections SQL
            query = """
                INSERT INTO sensor_data
                (air_quality_ppm, temperature, humidity, latitude, longitude,
                 air_quality_level, air_quality_color)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            
            # Exécuter la requête avec les valeurs fournies
            cursor.execute(query, (
                air_quality,  # Valeur PPM du capteur MQ-135
                temperature,  # Température en °C
                humidity,  # Humidité en %
                latitude,  # Latitude GPS (peut être NULL)
                longitude,  # Longitude GPS (peut être NULL)
                quality_info['level'],  # Niveau calculé (ex: 'Bon', 'Modéré')
                quality_info['color']  # Couleur calculée (ex: '#00E400')
            ))
            
            record_id = cursor.lastrowid  # Récupérer l'ID auto-généré
            self.connection.commit()  # Valider la transaction
            
            logger.info(f"✓ Données capteur insérées avec ID: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'insertion des données: {e}")
            self.connection.rollback()  # Annuler les modifications en cas d'erreur
            return None
    
    def get_latest_readings(self, limit=10):
        """
        Récupère les dernières lectures des capteurs
        
        Cette méthode récupère les N lectures les plus récentes de la table sensor_data,
        triées par ordre chronologique décroissant (du plus récent au plus ancien).
        
        Args:
            limit (int): Nombre de lectures à récupérer (défaut: 10)
        
        Returns:
            list: Liste de dictionnaires contenant les lectures
                  Chaque dictionnaire représente une ligne de la table
                  Retourne une liste vide en cas d'erreur
        
        Note:
            Les résultats sont convertis en dictionnaires grâce à row_factory=sqlite3.Row
            configuré dans la méthode connect().
        """
        try:
            cursor = self.connection.cursor()
            
            # Requête SQL pour récupérer les N lectures les plus récentes
            # ORDER BY timestamp DESC: trie par date décroissante (plus récent en premier)
            # LIMIT ?: limite le nombre de résultats
            query = """
                SELECT * FROM sensor_data
                ORDER BY timestamp DESC
                LIMIT ?;
            """
            
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            
            # Convertir chaque ligne (Row) en dictionnaire
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la récupération des données: {e}")
            return []
    
    def get_readings_by_timerange(self, start_time, end_time):
        """
        Récupère les lectures dans un intervalle de temps
        
        Cette méthode récupère toutes les lectures de capteurs comprises entre
        deux dates/heures spécifiées. Utile pour analyser les données sur une
        période donnée (ex: dernières 24 heures, semaine dernière, etc.).
        
        Args:
            start_time (datetime): Début de l'intervalle (inclus)
            end_time (datetime): Fin de l'intervalle (inclus)
        
        Returns:
            list: Liste de dictionnaires contenant les lectures dans l'intervalle
                  Retourne une liste vide en cas d'erreur
        
        Note:
            Les résultats sont triés par ordre chronologique croissant (ASC).
        """
        try:
            cursor = self.connection.cursor()
            
            # Requête SQL pour récupérer les lectures dans l'intervalle
            # BETWEEN ? AND ?: sélectionne les lignes où timestamp est entre start_time et end_time
            # ORDER BY timestamp ASC: trie par date croissante (plus ancien en premier)
            query = """
                SELECT * FROM sensor_data
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC;
            """
            
            cursor.execute(query, (start_time, end_time))
            results = cursor.fetchall()
            
            # Convertir chaque ligne (Row) en dictionnaire
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la récupération par intervalle: {e}")
            return []
    
    def get_statistics(self, hours=24):
        """
        Calcule des statistiques sur les dernières heures
        
        Cette méthode calcule des statistiques agrégées sur les données de capteurs
        pour une période donnée (par défaut: dernières 24 heures). Utile pour
        générer des résumés quotidiens et des rapports.
        
        Statistiques calculées:
        - Moyenne de la qualité de l'air (AQI)
        - Minimum de la qualité de l'air
        - Maximum de la qualité de l'air
        - Moyenne de la température
        - Moyenne de l'humidité
        - Nombre total de lectures
        
        Args:
            hours (int): Nombre d'heures à analyser (défaut: 24)
        
        Returns:
            dict: Dictionnaire contenant les statistiques
                  Clés: avg_aqi, min_aqi, max_aqi, avg_temp, avg_humidity, total_readings
                  Retourne un dictionnaire vide en cas d'erreur
        """
        try:
            cursor = self.connection.cursor()
            
            # Calculer l'heure de début de la période
            # datetime.now() - timedelta(hours=hours): heure actuelle moins X heures
            start_time = datetime.now() - timedelta(hours=hours)
            
            # Requête SQL pour calculer les statistiques agrégées
            # AVG(): moyenne, MIN(): minimum, MAX(): maximum, COUNT(): nombre de lignes
            query = """
                SELECT
                    AVG(air_quality_ppm) as avg_aqi,
                    MIN(air_quality_ppm) as min_aqi,
                    MAX(air_quality_ppm) as max_aqi,
                    AVG(temperature) as avg_temp,
                    AVG(humidity) as avg_humidity,
                    COUNT(*) as total_readings
                FROM sensor_data
                WHERE timestamp >= ?;
            """
            
            cursor.execute(query, (start_time,))
            result = cursor.fetchone()
            
            # Convertir le résultat en dictionnaire
            return dict(result) if result else {}
            
        except Exception as e:
            logger.error(f"✗ Erreur lors du calcul des statistiques: {e}")
            return {}
    
    def insert_prediction(self, predicted_for, predicted_aqi, confidence, model_version):
        """
        Insère une prédiction ML dans la base de données
        
        Cette méthode insère une prédiction du modèle ML dans la table predictions.
        Chaque prédiction représente une estimation de la qualité de l'air pour
        une heure future. Les prédictions sont utilisées pour anticiper les pics
        de pollution et informer les utilisateurs.
        
        Args:
            predicted_for (datetime): Heure pour laquelle la prédiction est faite
                                     (ex: dans 1 heure, dans 6 heures, etc.)
            predicted_aqi (float): Valeur AQI prédite par le modèle
            confidence (float): Score de confiance du modèle (0.0 à 1.0)
                               Plus proche de 1.0 = plus confiance
            model_version (str): Version du modèle utilisé (ex: 'RF_v1.0')
                               Utile pour suivre les améliorations du modèle
        
        Returns:
            int: ID de la prédiction insérée, ou None si erreur
        """
        try:
            cursor = self.connection.cursor()
            
            # Requête SQL d'insertion
            # prediction_time: heure actuelle (quand la prédiction est faite)
            # predicted_for: heure future pour laquelle la prédiction est faite
            query = """
                INSERT INTO predictions
                (prediction_time, predicted_for, predicted_aqi, confidence_score, model_version)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?);
            """
            
            cursor.execute(query, (predicted_for, predicted_aqi, confidence, model_version))
            prediction_id = cursor.lastrowid  # Récupérer l'ID auto-généré
            self.connection.commit()  # Valider la transaction
            
            logger.info(f"✓ Prédiction insérée avec ID: {prediction_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de l'insertion de la prédiction: {e}")
            self.connection.rollback()  # Annuler les modifications en cas d'erreur
            return None
    
    def insert_alert(self, alert_type, severity, message, air_quality_value=None, lat=None, lon=None):
        """
        Insère une alerte dans la base de données
        
        Cette méthode insère une alerte dans la table alerts. Les alertes sont
        déclenchées automatiquement par le système quand la qualité de l'air
        dépasse les seuils configurés ou quand une erreur est détectée.
        
        Types d'alertes courants:
        - HIGH_POLLUTION: Qualité de l'air élevée
        - SENSOR_ERROR: Erreur de lecture des capteurs
        - PREDICTION_PEAK: Pic de pollution prévu
        
        Niveaux de sévérité:
        - LOW: Information mineure
        - MEDIUM: Attention requise
        - HIGH: Action recommandée
        - CRITICAL: Action immédiate requise
        
        Args:
            alert_type (str): Type d'alerte (ex: 'HIGH_POLLUTION', 'SENSOR_ERROR')
            severity (str): Sévérité ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
            message (str): Message descriptif de l'alerte
            air_quality_value (float): Valeur qui a déclenché l'alerte (optionnel)
            lat (float): Latitude où l'alerte a été déclenchée (optionnel)
            lon (float): Longitude où l'alerte a été déclenchée (optionnel)
        
        Returns:
            int: ID de l'alerte insérée, ou None si erreur
        """
        try:
            cursor = self.connection.cursor()
            
            # Requête SQL d'insertion
            # resolved=0 par défaut (alerte active)
            query = """
                INSERT INTO alerts
                (alert_type, severity, message, air_quality_value, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?);
            """
            
            cursor.execute(query, (alert_type, severity, message, air_quality_value, lat, lon))
            alert_id = cursor.lastrowid  # Récupérer l'ID auto-généré
            self.connection.commit()  # Valider la transaction
            
            logger.info(f"✓ Alerte créée avec ID: {alert_id} - Sévérité: {severity}")
            return alert_id
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la création de l'alerte: {e}")
            self.connection.rollback()  # Annuler les modifications en cas d'erreur
            return None
    
    def get_active_alerts(self):
        """
        Récupère toutes les alertes actives (non résolues)
        
        Cette méthode récupère toutes les alertes qui n'ont pas encore été résolues
        (resolved=0). Les alertes actives sont celles qui nécessitent encore
        une attention de l'utilisateur ou du système.
        
        Returns:
            list: Liste de dictionnaires contenant les alertes actives
                  Retourne une liste vide en cas d'erreur
        
        Note:
            Les résultats sont triés par date de création décroissante
            (alertes les plus récentes en premier).
        """
        try:
            cursor = self.connection.cursor()
            
            # Requête SQL pour récupérer les alertes non résolues
            # WHERE resolved = 0: filtre uniquement les alertes actives
            # ORDER BY created_at DESC: trie par date décroissante
            query = """
                SELECT * FROM alerts
                WHERE resolved = 0
                ORDER BY created_at DESC;
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convertir chaque ligne (Row) en dictionnaire
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la récupération des alertes: {e}")
            return []
    
    def get_recent_alerts(self, limit=10):
        """
        Récupère les alertes les plus récentes (résolues ou non)
        
        Cette méthode récupère les N alertes les plus récentes, qu'elles soient
        actives ou résolues. Utile pour afficher l'historique des alertes
        dans l'interface web.
        
        Args:
            limit (int): Nombre d'alertes à récupérer (défaut: 10)
        
        Returns:
            list: Liste de dictionnaires contenant les alertes récentes
                  Retourne une liste vide en cas d'erreur
        """
        try:
            cursor = self.connection.cursor()
            
            # Requête SQL pour récupérer les N alertes les plus récentes
            # ORDER BY created_at DESC: trie par date décroissante
            # LIMIT ?: limite le nombre de résultats
            query = """
                SELECT * FROM alerts
                ORDER BY created_at DESC
                LIMIT ?;
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            
            # Convertir chaque ligne (Row) en dictionnaire
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"✗ Erreur get_recent_alerts: {e}")
            return []
    
    def resolve_alert(self, alert_id):
        """
        Marque une alerte comme résolue
        
        Cette méthode marque une alerte comme résolue en mettant le flag
        resolved à 1 et en enregistrant l'heure de résolution. Les alertes
        résolues ne sont plus considérées comme actives.
        
        Args:
            alert_id (int): ID de l'alerte à résoudre
        
        Returns:
            bool: True si la résolution a réussi, False sinon
        
        Note:
            Cette méthode est appelée automatiquement par le système
            quand la qualité de l'air revient à des niveaux normaux.
        """
        try:
            cursor = self.connection.cursor()
            
            # Requête SQL pour mettre à jour l'alerte
            # SET resolved = 1: marque comme résolue
            # SET resolved_at = CURRENT_TIMESTAMP: enregistre l'heure de résolution
            query = """
                UPDATE alerts
                SET resolved = 1, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """
            
            cursor.execute(query, (alert_id,))
            self.connection.commit()  # Valider la transaction
            
            logger.info(f"✓ Alerte {alert_id} marquée comme résolue")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erreur lors de la résolution de l'alerte: {e}")
            self.connection.rollback()  # Annuler les modifications en cas d'erreur
            return False
    
    def close(self):
        """
        Ferme la connexion à la base de données
        
        Cette méthode ferme proprement la connexion à la base de données SQLite.
        Elle doit être appelée avant de terminer le programme pour éviter
        les fuites de ressources et les problèmes de verrouillage du fichier.
        
        Note:
            Une fois fermée, la connexion ne peut plus être utilisée.
            Il faut appeler connect() à nouveau pour rétablir une nouvelle connexion.
        """
        if self.connection:
            self.connection.close()  # Fermer la connexion SQLite
            logger.info("✓ Connexion à la base de données fermée")

# Instance globale de la base de données
# Cette instance est créée au chargement du module et peut être importée
# dans d'autres modules pour accéder à la base de données
db = AirQualityDatabase()