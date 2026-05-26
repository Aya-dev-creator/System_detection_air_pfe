"""
Module de Machine Learning pour la prédiction de la qualité de l'air
Utilise Random Forest pour prédire les pics de pollution

Ce module implémente un système de prédiction de la qualité de l'air basé sur
l'apprentissage automatique (Machine Learning). Il utilise l'algorithme Random Forest
pour prédire la qualité de l'air future et détecter les pics de pollution.

Fonctionnalités:
- Entraînement de modèles ML sur des données historiques
- Prédiction de la qualité de l'air pour les prochaines 24 heures
- Détection des pics de pollution prévus
- Génération de recommandations personnalisées
- Génération de données synthétiques pour l'entraînement initial

Architecture:
- AirQualityPredictor: Classe principale pour les prédictions
- RandomForestRegressor: Algorithme ML utilisé (robuste et performant)
- StandardScaler: Normalisation des features
- Feature Engineering: Création de features temporelles et de lag

Optimisation pour Raspberry Pi:
- Modèle léger (Random Forest avec 100 arbres)
- Gestion d'erreurs robuste
- Fallback quand le modèle n'est pas disponible
- Prédictions synthétiques réalistes en cas d'échec
"""

import numpy as np  # Bibliothèque pour le calcul numérique
import pandas as pd  # Bibliothèque pour la manipulation de données
from datetime import datetime, timedelta  # Modules pour les dates et heures
import logging  # Module pour la journalisation
import joblib  # Module pour sauvegarder/charger les modèles ML
import os  # Module pour les opérations système

# ============= IMPORTS MACHINE LEARNING =============
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor  # Algorithmes de régression
from sklearn.preprocessing import StandardScaler  # Normalisation des features
from sklearn.model_selection import train_test_split  # Division train/test
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error  # Métriques d'évaluation

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class AirQualityPredictor:
    """
    Classe pour créer et utiliser des modèles de prédiction de qualité de l'air
    
    Cette classe encapsule toutes les fonctionnalités liées au Machine Learning:
    - Entraînement de modèles Random Forest
    - Feature engineering (création de features temporelles, lag, rolling statistics)
    - Prédiction de la qualité de l'air future
    - Détection des pics de pollution
    - Génération de recommandations personnalisées
    - Sauvegarde et chargement des modèles
    
    Méthodes principales:
    - create_features(): Crée les features pour le modèle ML
    - train_model(): Entraîne le modèle sur des données historiques
    - predict(): Fait des prédictions pour les prochaines heures
    - detect_pollution_peak(): Détecte les pics de pollution prévus
    - generate_recommendations(): Génère des recommandations personnalisées
    - save_model(): Sauvegarde le modèle entraîné
    - load_model(): Charge un modèle sauvegardé
    """
    
    def __init__(self, model_path='./models/air_quality_model.pkl'):
        """
        Initialise le prédicteur de qualité de l'air
        
        Cette méthode configure le prédicteur avec:
        - Le chemin de sauvegarde du modèle
        - Le chemin de sauvegarde du scaler (normalisation)
        - La liste des features utilisées par le modèle
        - Le scaler pour normaliser les features
        
        Args:
            model_path (str): Chemin pour sauvegarder/charger le modèle
                             Par défaut: './models/air_quality_model.pkl'
        """
        self.model_path = model_path  # Chemin du fichier du modèle
        self.scaler_path = model_path.replace('.pkl', '_scaler.pkl')  # Chemin du scaler
        self.model = None  # Instance du modèle ML (sera chargé ou entraîné)
        self.scaler = StandardScaler()  # Scaler pour normaliser les features
        
        # Liste des features utilisées par le modèle
        # Ces features sont créées par la méthode create_features()
        self.feature_names = [
            'hour',  # Heure de la journée (0-23)
            'day_of_week',  # Jour de la semaine (0-6, 0=lundi)
            'month',  # Mois de l'année (1-12)
            'temperature',  # Température en °C
            'humidity',  # Humidité en %
            'air_quality_lag_1',  # Qualité de l'air il y a 1 heure
            'air_quality_lag_2',  # Qualité de l'air il y a 2 heures
            'air_quality_lag_3',  # Qualité de l'air il y a 3 heures
            'air_quality_rolling_mean_3',  # Moyenne mobile sur 3 heures
            'air_quality_rolling_mean_6',  # Moyenne mobile sur 6 heures
            'air_quality_rolling_std_3'  # Écart-type mobile sur 3 heures
        ]
        
        # Créer les dossiers nécessaires s'ils n'existent pas
        os.makedirs('./models', exist_ok=True)  # Dossier pour les modèles
        os.makedirs('./data', exist_ok=True)  # Dossier pour les données
        
        logger.info("Prédicteur de qualité de l'air initialisé")
    def create_features(self, df):
        """
        Crée les features pour le modèle ML à partir des données brutes
        
        Cette méthode effectue du "feature engineering" pour créer des features
        informatives à partir des données brutes des capteurs. Le feature engineering
        est essentiel pour améliorer les performances du modèle ML.
        
        Features créées:
        1. Features temporelles: hour, day_of_week, month
           - Capturent les patterns saisonniers et horaires
        2. Features de lag: air_quality_lag_1, lag_2, lag_3
           - Capturent la dépendance temporelle (valeurs précédentes)
        3. Features de rolling statistics: rolling_mean_3, rolling_mean_6, rolling_std_3
           - Capturent les tendances et la volatilité
        
        Args:
            df (DataFrame): DataFrame avec colonnes timestamp, air_quality_ppm, temperature, humidity
        
        Returns:
            DataFrame: DataFrame avec features engineered
                      Les lignes avec NaN sont supprimées (créées par lag/rolling)
        """
        logger.info("Creation des features...")
        df = df.copy()  # Copier le DataFrame pour éviter de modifier l'original
        
        # Convertir timestamp en datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Trier par timestamp (nécessaire pour les features de lag et rolling)
        df = df.sort_values('timestamp')
        
        # ============= FEATURES TEMPORELLES =============
        # Ces features capturent les patterns saisonniers et horaires
        df['hour'] = df['timestamp'].dt.hour  # Heure de la journée (0-23)
        df['day_of_week'] = df['timestamp'].dt.dayofweek  # Jour de la semaine (0-6)
        df['month'] = df['timestamp'].dt.month  # Mois de l'année (1-12)
        
        # ============= FEATURES DE LAG =============
        # Ces features capturent la dépendance temporelle
        # shift(1): valeur de l'heure précédente
        # shift(2): valeur de 2 heures avant
        # shift(3): valeur de 3 heures avant
        df['air_quality_lag_1'] = df['air_quality_ppm'].shift(1)
        df['air_quality_lag_2'] = df['air_quality_ppm'].shift(2)
        df['air_quality_lag_3'] = df['air_quality_ppm'].shift(3)
        
        # ============= FEATURES DE ROLLING STATISTICS =============
        # Ces features capturent les tendances et la volatilité
        # rolling(window=3).mean(): moyenne des 3 dernières heures
        # rolling(window=6).mean(): moyenne des 6 dernières heures
        # rolling(window=3).std(): écart-type des 3 dernières heures
        df['air_quality_rolling_mean_3'] = df['air_quality_ppm'].rolling(window=3).mean()
        df['air_quality_rolling_mean_6'] = df['air_quality_ppm'].rolling(window=6).mean()
        df['air_quality_rolling_std_3'] = df['air_quality_ppm'].rolling(window=3).std()
        
        # Supprimer les lignes avec des NaN créées par les opérations de lag/rolling
        # Les premières lignes auront NaN car il n'y a pas assez de données historiques
        df = df.dropna()
        
        logger.info(f"✓ {len(df)} échantillons avec features créés")
        return df
    def train_model(self, data, test_size=0.2):
        """
        Entraîne le modèle de prédiction Random Forest
        
        Cette méthode entraîne un modèle Random Forest pour prédire la qualité de l'air.
        Le processus d'entraînement comprend:
        1. Création des features (feature engineering)
        2. Division des données en train/test
        3. Normalisation des features (StandardScaler)
        4. Entraînement du modèle Random Forest
        5. Évaluation des performances (RMSE, MAE, R²)
        6. Sauvegarde du modèle entraîné
        
        Args:
            data (DataFrame): Données d'entraînement avec colonnes requises
                             (timestamp, air_quality_ppm, temperature, humidity)
            test_size (float): Proportion des données pour le test (défaut: 0.2 = 20%)
        
        Returns:
            dict: Métriques de performance du modèle:
                  - train: Métriques sur les données d'entraînement (RMSE, MAE, R²)
                  - test: Métriques sur les données de test (RMSE, MAE, R²)
        """
        logger.info("Debut de l'entraînement du modèle...")
        
        # ============= 1. CRÉATION DES FEATURES =============
        df = self.create_features(data)  # Créer les features ML
        
        # ============= 2. PRÉPARATION DES DONNÉES =============
        X = df[self.feature_names]  # Features (variables indépendantes)
        y = df['air_quality_ppm']  # Target (variable dépendante)
        
        # ============= 3. DIVISION TRAIN/TEST =============
        # Diviser les données en ensemble d'entraînement et de test
        # shuffle=False: important pour les données temporelles (ne pas mélanger)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )
        
        logger.info(f"Données d'entraînement: {len(X_train)} échantillons")
        logger.info(f"Données de test: {len(X_test)} échantillons")
        
        # ============= 4. NORMALISATION DES FEATURES =============
        # Normaliser les features pour avoir une moyenne de 0 et un écart-type de 1
        # Cela améliore la convergence et les performances du modèle
        X_train_scaled = self.scaler.fit_transform(X_train)  # Fit sur train, transform train
        X_test_scaled = self.scaler.transform(X_test)  # Transform test avec le scaler du train
        
        # ============= 5. ENTRAÎNEMENT DU MODÈLE RANDOM FOREST =============
        logger.info("Entraînement Random Forest...")
        self.model = RandomForestRegressor(
            n_estimators=100,  # Nombre d'arbres dans la forêt
            max_depth=15,  # Profondeur maximale des arbres
            min_samples_split=5,  # Nombre minimum d'échantillons pour diviser un nœud
            min_samples_leaf=2,  # Nombre minimum d'échantillons dans une feuille
            random_state=42,  # Seed pour la reproductibilité
            n_jobs=-1  # Utiliser tous les cœurs CPU disponibles
        )
        self.model.fit(X_train_scaled, y_train)  # Entraîner le modèle
        
        # ============= 6. PRÉDICTIONS ET ÉVALUATION =============
        y_pred_train = self.model.predict(X_train_scaled)  # Prédictions sur train
        y_pred_test = self.model.predict(X_test_scaled)  # Prédictions sur test
        
        # Calculer les métriques de performance
        metrics = {
            'train': {
                'rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),  # Root Mean Squared Error
                'mae': mean_absolute_error(y_train, y_pred_train),  # Mean Absolute Error
                'r2': r2_score(y_train, y_pred_train)  # R² Score (coefficient de détermination)
            },
            'test': {
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
                'mae': mean_absolute_error(y_test, y_pred_test),
                'r2': r2_score(y_test, y_pred_test)
            }
        }
        
        # ============= 7. AFFICHAGE DES RÉSULTATS =============
        logger.info("\n" + "="*50)
        logger.info("RÉSULTATS DE L'ENTRAÎNEMENT")
        logger.info("="*50)
        logger.info(f"Train RMSE: {metrics['train']['rmse']:.2f}")
        logger.info(f"Train MAE:  {metrics['train']['mae']:.2f}")
        logger.info(f"Train R²:   {metrics['train']['r2']:.3f}")
        logger.info("-"*50)
        logger.info(f"Test RMSE:  {metrics['test']['rmse']:.2f}")
        logger.info(f"Test MAE:   {metrics['test']['mae']:.2f}")
        logger.info(f"Test R²:    {metrics['test']['r2']:.3f}")
        logger.info("="*50 + "\n")
        
        # ============= 8. IMPORTANCE DES FEATURES =============
        # Afficher les 5 features les plus importantes
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        logger.info("Importance des features:")
        for idx, row in feature_importance.head(5).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.3f}")
        
        # ============= 9. SAUVEGARDE DU MODÈLE =============
        self.save_model()
        
        return metrics
    def predict(self, current_data, hours_ahead=24):
        """
        Fait des prédictions pour les prochaines heures
        Optimisé pour Raspberry Pi avec gestion d'erreurs améliorée
        Args:
            current_data (dict): Données actuelles des capteurs
            hours_ahead (int): Nombre d'heures à prédire
        Returns:
            list: Liste de prédictions avec timestamps
        """
        if self.model is None:
            logger.warning("Modèle non chargé. Tentative de chargement...")
            if not self.load_model():
                logger.error("Modèle non disponible. Retour aux valeurs simulées.")
                return self._generate_fallback_predictions(current_data, hours_ahead)
        
        try:
            logger.info(f"Prédiction pour les {hours_ahead} prochaines heures...")
            predictions = []
            current_time = datetime.now()
            current_aqi = float(current_data.get('air_quality_ppm', 100))
            
            # Préparer les features de base
            for hour in range(hours_ahead):
                try:
                    pred_time = current_time + timedelta(hours=hour)
                    # Créer les features pour cette heure
                    features = {
                        'hour': pred_time.hour,
                        'day_of_week': pred_time.weekday(),
                        'month': pred_time.month,
                        'temperature': float(current_data.get('temperature', 25)),
                        'humidity': float(current_data.get('humidity', 50)),
                        'air_quality_lag_1': current_aqi,
                        'air_quality_lag_2': current_aqi * 0.98,
                        'air_quality_lag_3': current_aqi * 0.97,
                        'air_quality_rolling_mean_3': current_aqi,
                        'air_quality_rolling_mean_6': current_aqi,
                        'air_quality_rolling_std_3': 10
                    }
                    # Préparer l'input pour le modèle
                    X = np.array([[features[f] for f in self.feature_names]], dtype=np.float32)
                    X_scaled = self.scaler.transform(X)
                    # Faire la prédiction avec gestion d'erreur
                    predicted_aqi = float(self.model.predict(X_scaled)[0])
                    # Ajouter une variation réaliste
                    noise = np.random.normal(0, 5)
                    predicted_aqi = max(0, predicted_aqi + noise)
                    
                    predictions.append({
                        'timestamp': pred_time.isoformat(),
                        'predicted_aqi': max(0, round(predicted_aqi, 2)),
                        'hour': pred_time.hour,
                        'confidence': 0.85
                    })
                except Exception as hour_err:
                    logger.warning(f"Erreur prédiction heure {hour}: {hour_err}")
                    # Fallback pour cette heure
                    pred_time = current_time + timedelta(hours=hour)
                    predictions.append({
                        'timestamp': pred_time.isoformat(),
                        'predicted_aqi': max(0, current_aqi + np.random.normal(0, 10)),
                        'hour': pred_time.hour,
                        'confidence': 0.6
                    })
            
            logger.info(f"✓ {len(predictions)} prédictions générées")
            return predictions
        except Exception as e:
            logger.error(f"Erreur prédiction globale: {e}")
            return self._generate_fallback_predictions(current_data, hours_ahead)
    
    def _generate_fallback_predictions(self, current_data, hours_ahead):
        """Génère des prédictions de fallback quand le modèle n'est pas disponible (Raspberry Pi)."""
        logger.info(f"Génération de prédictions de fallback pour {hours_ahead} heures...")
        predictions = []
        current_time = datetime.now()
        current_aqi = float(current_data.get('air_quality_ppm', 80))
        
        # Pattern réaliste: hausse graduelle puis baisse
        for hour in range(hours_ahead):
            pred_time = current_time + timedelta(hours=hour)
            # Variation réaliste: pic vers 18h, baisse la nuit
            hour_effect = 20 * np.sin((pred_time.hour - 6) * np.pi / 12)
            trend = current_aqi + hour_effect + np.random.normal(0, 8)
            trend = max(10, trend)
            
            predictions.append({
                'timestamp': pred_time.isoformat(),
                'predicted_aqi': max(0, round(trend, 2)),
                'hour': pred_time.hour,
                'confidence': 0.6
            })
        
        logger.info(f"✓ {len(predictions)} prédictions de fallback générées")
        return predictions
    def detect_pollution_peak(self, predictions, threshold=150):
        """
        Détecte les pics de pollution prévus
        Args:
            predictions (list): Liste des prédictions
            threshold (float): Seuil de pollution critique (PPM)
        Returns:
            list: Liste des alertes de pics de pollution
        """
        alerts = []
        for pred in predictions:
            if pred['predicted_aqi'] > threshold:
                alerts.append({
                    'timestamp': pred['timestamp'],
                    'predicted_aqi': pred['predicted_aqi'],
                    'severity': 'HIGH' if pred['predicted_aqi'] > 200 else 'MEDIUM',
                    'message': f"Pic de pollution prévu: {pred['predicted_aqi']:.0f} PPM"
                })
        if alerts:
            logger.warning(f"{len(alerts)} pic(s) de pollution détecté(s)")
        else:
            logger.info("Aucun pic de pollution prévu")
        return alerts
    def generate_recommendations(self, current_aqi, predicted_peaks):
        """
        Génère des recommandations personnalisées basées sur les prédictions
        Args:
            current_aqi (float): Qualité de l'air actuelle
            predicted_peaks (list): Liste des pics prévus
        Returns:
            dict: Recommandations personnalisées
        """
        recommendations = {
            'current_status': '',
            'actions': [],
            'health_advice': [],
            'time_periods_to_avoid': []
        }
        # Statut actuel
        if current_aqi <= 50:
            recommendations['current_status'] = "Qualité de l'air excellente"
            recommendations['actions'].append("Profitez des activités en plein air")
        elif current_aqi <= 100:
            recommendations['current_status'] = "Qualité de l'air acceptable"
            recommendations['actions'].append("Les activités en plein air sont généralement sûres")
        elif current_aqi <= 150:
            recommendations['current_status'] = "Qualité de l'air modérée"
            recommendations['actions'].append("Limitez les activités extérieures prolongées")
            recommendations['health_advice'].append("Les personnes sensibles doivent être prudentes")
        else:
            recommendations['current_status'] = "Qualité de l'air mauvaise"
            recommendations['actions'].append("Évitez les activités extérieures intenses")
            recommendations['health_advice'].append("Restez à l'intérieur si possible")
        # Analyser les pics prévus
        if predicted_peaks:
            for peak in predicted_peaks:
                timestamp = datetime.fromisoformat(peak['timestamp'])
                time_str = timestamp.strftime('%H:%M')
                recommendations['time_periods_to_avoid'].append(
                    f"{time_str} - Pic prévu: {peak['predicted_aqi']:.0f} PPM"
                )
            recommendations['actions'].append(
                f"{len(predicted_peaks)} pic(s) de pollution prévu(s) dans les prochaines heures"
            )
        return recommendations
    def save_model(self):
        """Sauvegarde le modèle et le scaler"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info(f"Modèle sauvegardé: {self.model_path}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde modèle: {e}")
    def load_model(self):
        """Charge le modèle et le scaler depuis le disque"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"Modèle chargé: {self.model_path}")
                return True
            else:
                logger.warning("Fichiers de modèle non trouvés")
                return False
        except Exception as e:
            logger.error(f"Erreur chargement modèle: {e}")
            return False
def generate_synthetic_training_data(num_samples=1000):
    """
    Génère des données synthétiques pour l'entraînement initial
    Utilisé pour démarrer le système avant d'avoir des données réelles
    Args:
        num_samples (int): Nombre d'échantillons à générer
    Returns:
        DataFrame: Données synthétiques
    """
    logger.info(f"Génération de {num_samples} échantillons synthétiques...")
    np.random.seed(42)
    # Générer des timestamps (derniers 30 jours)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    timestamps = pd.date_range(start=start_time, end=end_time, periods=num_samples)
    # Créer des patterns réalistes
    data = {
        'timestamp': timestamps,
        'air_quality_ppm': [],
        'temperature': [],
        'humidity': []
    }
    for i, ts in enumerate(timestamps):
        # Qualité de l'air avec patterns horaires et bruit
        hour = ts.hour
        base_aqi = 80  # Base
        hour_effect = 30 * np.sin((hour - 6) * np.pi / 12)  # Pic à 18h
        weekend_effect = -10 if ts.weekday() >= 5 else 0
        noise = np.random.normal(0, 15)
        aqi = max(10, base_aqi + hour_effect + weekend_effect + noise)
        # Température avec variation diurne
        temp_base = 25
        temp_hour = 8 * np.sin((hour - 6) * np.pi / 12)
        temp = temp_base + temp_hour + np.random.normal(0, 2)
        # Humidité inversement corrélée à température
        humidity = max(20, min(90, 70 - temp_hour * 2 + np.random.normal(0, 5)))
        data['air_quality_ppm'].append(round(aqi, 2))
        data['temperature'].append(round(temp, 1))
        data['humidity'].append(round(humidity, 1))
    df = pd.DataFrame(data)
    logger.info(f"{len(df)} échantillons synthétiques générés")
    return df
# Test du module si exécuté directement
if __name__ == "__main__":
    print("=== Test du système de Machine Learning ===\n")
    # Créer le prédicteur
    predictor = AirQualityPredictor()
    # Générer des données synthétiques
    print("Génération de données d'entraînement...")
    training_data = generate_synthetic_training_data(num_samples=2000)
    # Entraîner le modèle
    print("\nEntraînement du modèle...")
    metrics = predictor.train_model(training_data)
    # Faire des prédictions
    print("\nPrédictions pour les prochaines 24 heures...")
    current_data = {
        'temperature': 25,
        'humidity': 60,
        'air_quality_ppm': 95
    }
    predictions = predictor.predict(current_data, hours_ahead=24)
    # Détecter les pics
    peaks = predictor.detect_pollution_peak(predictions, threshold=120)
    # Générer des recommandations
    recommendations = predictor.generate_recommendations(
        current_aqi=95,
        predicted_peaks=peaks
    )
    print("\n📋 RECOMMANDATIONS:")
    print(f"Statut: {recommendations['current_status']}")
    print("\nActions:")
    for action in recommendations['actions']:
        print(f"  • {action}")
    if recommendations['time_periods_to_avoid']:
        print("\nPériodes à éviter:")
        for period in recommendations['time_periods_to_avoid']:
            print(f"  • {period}")
    print("\n✓ Test terminé")