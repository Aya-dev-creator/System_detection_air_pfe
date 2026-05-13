"""
Module de gestion des capteurs Raspberry Pi
Gère la lecture des capteurs: MQ-135 (qualité de l'air), DHT11 (température/humidité), GPS NEO-6M

Ce module fournit une interface pour interagir avec les capteurs physiques connectés
au Raspberry Pi. Il inclut des modes de simulation pour permettre le développement
sur des ordinateurs qui ne sont pas des Raspberry Pi.

Capteurs supportés:
1. MQ-135: Capteur de qualité de l'air (détecte CO2, fumée, gaz combustibles)
   - Utilise l'ADC ADS1115 pour la lecture analogique
   - Fournit une sortie digitale DOUT pour les alertes de seuil
2. DHT11: Capteur de température et d'humidité
   - Lecture numérique via protocole propriétaire
   - Précision: ±2°C pour la température, ±5% pour l'humidité
3. GPS NEO-6M: Module GPS pour la localisation
   - Communication série via gpsd
   - Fournit latitude, longitude, altitude, vitesse

Architecture:
- MQ135Sensor: Classe pour le capteur MQ-135
- DHT11Sensor: Classe pour le capteur DHT11
- GPSSensor: Classe pour le module GPS
- SensorManager: Gestionnaire central qui coordonne tous les capteurs

Mode simulation:
Si les modules Raspberry Pi ne sont pas disponibles, le système fonctionne en mode simulation
en générant des données aléatoires réalistes. Cela permet le développement et les tests
sans matériel Raspberry Pi.
"""

import time  # Module pour les pauses et le timing
import logging  # Module pour la journalisation
from datetime import datetime  # Module pour les dates et heures

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= IMPORTS CONDITIONNELS RASPBERRY PI =============
# Ces imports sont conditionnels pour permettre le développement hors Raspberry Pi
# Si les modules ne sont pas disponibles, le système fonctionne en mode simulation

# Import des modules GPIO et DHT11
try:
    import RPi.GPIO as GPIO  # type: ignore  # Bibliothèque pour les broches GPIO
    import adafruit_dht  # type: ignore  # Bibliothèque pour le capteur DHT11
    import board  # type: ignore  # Bibliothèque pour les broches du Raspberry Pi
    RPI_AVAILABLE = True
    logger.info("✓ Modules Raspberry Pi chargés avec succès")
except ImportError:
    RPI_AVAILABLE = False
    logger.warning("⚠ Modules Raspberry Pi non disponibles - Mode simulation activé")

# Import du module GPS
try:
    from gpsd import gps, WATCH_ENABLE  # type: ignore  # Bibliothèque pour le GPS via gpsd
    GPS_AVAILABLE = True
except ImportError:
    GPS_AVAILABLE = False
    logger.warning("⚠ Module GPS non disponible")

# Import des modules ADS1115 (ADC pour le MQ-135)
try:
    import board  # type: ignore  # Bibliothèque pour les broches I2C
    import busio  # type: ignore  # Bibliothèque pour le bus I2C
    import adafruit_ads1x15.ads1115 as ADS  # type: ignore  # Bibliothèque pour l'ADC ADS1115
    from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore  # Lecture analogique
    ADS_AVAILABLE = True
except ImportError:
    ADS_AVAILABLE = False
    logger.warning("⚠ Module ADS1115 non disponible")

# Modification de la classe MQ135Sensor

class MQ135Sensor:
    """
    Classe pour gérer le capteur MQ-135 (qualité de l'air)
    
    Le capteur MQ-135 est un capteur de qualité de l'air qui détecte:
    - CO2 (dioxyde de carbone)
    - Fumée
    - Gaz combustibles (méthane, propane, butane, etc.)
    - Alcool
    - Ammoniac
    
    Fonctionnement:
    - Le capteur a une résistance interne (Rs) qui varie en fonction de la concentration de gaz
    - La résistance est mesurée via un ADC (ADS1115) sur le bus I2C
    - La valeur analogique est convertie en PPM (parts per million)
    - Le capteur fournit également une sortie digitale DOUT pour les alertes de seuil
    
    Calibration:
    - Le capteur doit être calibré dans un environnement d'air propre
    - La calibration détermine R0 (résistance dans l'air propre)
    - R0 est utilisé pour calculer le ratio Rs/R0 et convertir en PPM
    
    Utilise l'ADS1115 pour la lecture analogique (convertisseur analogique-numérique 16-bit)
    """
    
    def __init__(self, digital_pin=17, adc_channel=0, pin=None):
        """
        Initialise le capteur MQ-135
        
        Cette méthode configure le capteur MQ-135 en:
        1. Initialisant l'ADC ADS1115 sur le bus I2C
        2. Configurant le canal ADC spécifié
        3. Configurant la broche GPIO pour la sortie digitale DOUT (optionnel)
        4. Définissant la résistance de calibration R0 (par défaut: 10.0 kΩ)
        
        Args:
            digital_pin (int): Pin GPIO pour sortie digitale DOUT (par défaut: GPIO 17)
                              La sortie DOUT passe à LOW quand le seuil de gaz est dépassé
            adc_channel (int): Canal ADC de l'ADS1115 (0-3, par défaut: 0)
                              L'ADS1115 a 4 canaux analogiques (A0, A1, A2, A3)
            pin (int): Paramètre de compatibilité avec l'ancienne signature
                      Si fourni, remplace digital_pin (pour compatibilité)
        """
        # Compatibilité avec l'ancienne signature MQ135Sensor(pin=17)
        if pin is not None:
            digital_pin = pin

        self.digital_pin = digital_pin  # Broche GPIO pour DOUT
        self.adc_channel = adc_channel  # Canal ADC (0-3)
        self.r0 = 10.0  # Résistance de calibration R0 (en kΩ)
        self.ads = None  # Instance de l'ADC ADS1115
        self.adc_channel_obj = None  # Objet du canal ADC
        
        # ============= INITIALISATION DE L'ADS1115 (ADC) =============
        # L'ADS1115 est un convertisseur analogique-numérique 16-bit
        # Il communique via le bus I2C (adresse par défaut: 0x48)
        # Il a 4 canaux analogiques (A0, A1, A2, A3)
        if ADS_AVAILABLE:
            try:
                # Initialiser le bus I2C
                # SCL: Serial Clock (horloge), SDA: Serial Data (données)
                i2c = busio.I2C(board.SCL, board.SDA)
                
                # Attendre que le bus I2C soit disponible
                while not i2c.try_lock():
                    time.sleep(0.1)
                
                # Scanner les adresses I2C disponibles pour vérifier la connexion
                logger.info("Scanning I2C bus...")
                addresses = i2c.scan()
                i2c.unlock()
                
                if addresses:
                    logger.info(f"Adresses I2C trouvées: {[hex(addr) for addr in addresses]}")
                else:
                    logger.warning("Aucune adresse I2C trouvée")
                
                # Initialiser ADS1115 avec plusieurs tentatives (gestion d'erreur robuste)
                for attempt in range(3):
                    try:
                        self.ads = ADS.ADS1115(i2c, address=0x48)  # Adresse par défaut de l'ADS1115
                        
                        # Mapper le canal ADC (0-3) à l'attribut correspondant (ADS.P0-ADS.P3)
                        channel_map = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
                        channel_attr = channel_map.get(adc_channel, ADS.P0)
                        
                        # Créer l'objet de lecture analogique pour le canal spécifié
                        self.adc_channel_obj = AnalogIn(self.ads, channel_attr)
                        logger.info(f"✓ ADS1115 initialisé sur canal {adc_channel} (adresse 0x48)")
                        break  # Sortir de la boucle si l'initialisation a réussi
                    except ValueError as e:
                        if "0x48" in str(e):
                            logger.warning(f"Tentative {attempt + 1}/3: {e}")
                            time.sleep(1)  # Attendre avant de réessayer
                        else:
                            raise  # Propager l'erreur si ce n'est pas une erreur d'adresse
                    except Exception as e:
                        logger.error(f"Erreur initialisation ADS1115: {e}")
                        break  # Sortir de la boucle en cas d'erreur
                        
                if self.adc_channel_obj is None:
                    logger.error("Impossible d'initialiser l'ADS1115 après plusieurs tentatives")
                    
            except Exception as e:
                logger.error(f"✗ Erreur initialisation ADS1115/I2C: {e}")
                self.adc_channel_obj = None
        else:
            self.adc_channel_obj = None
            logger.warning("⚠ Mode simulation MQ-135 activé (ADS1115 non disponible)")
            
        # ============= INITIALISATION DU PIN DIGITAL DOUT =============
        # La sortie DOUT passe à LOW quand le seuil de gaz est dépassé
        # Ce seuil est réglable via le potentiomètre sur le module MQ-135
        if RPI_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)  # Utiliser la numérotation BCM des broches
                GPIO.setup(self.digital_pin, GPIO.IN)  # Configurer la broche en entrée
                logger.info(f"✓ Capteur MQ-135 DOUT initialisé sur GPIO {self.digital_pin}")
            except Exception as e:
                logger.error(f"Erreur initialisation GPIO: {e}")
        else:
            logger.warning("⚠ GPIO non disponible pour MQ-135")
    
    def read_analog_value(self):
        """
        Lit la valeur analogique du capteur MQ-135 via ADS1115
        
        Cette méthode lit la valeur analogique brute du capteur MQ-135 via l'ADC ADS1115.
        L'ADS1115 est un convertisseur analogique-numérique 16-bit qui retourne
        des valeurs entre 0 et 26400 (pour la plage ±4.096V par défaut).
        
        En mode simulation (si ADS1115 non disponible), génère une valeur aléatoire
        réaliste entre 5000 et 20000.
        
        Returns:
            int: Valeur analogique (0-26400 pour ADS1115 16-bit)
                  Retourne 0 en cas d'erreur
        """
        if not ADS_AVAILABLE or self.adc_channel_obj is None:
            # Mode simulation: générer une valeur aléatoire réaliste
            import random
            return random.randint(5000, 20000)
        
        try:
            # Lire la valeur brute de l'ADS1115
            value = self.adc_channel_obj.value  # Valeur brute (0-26400)
            voltage = self.adc_channel_obj.voltage  # Tension correspondante (0-4.096V)
            logger.debug(f"ADS1115 - Raw: {value}, Voltage: {voltage:.3f}V")
            return value
        except Exception as e:
            logger.error(f"✗ Erreur lecture ADS1115: {e}")
            return 0
    
    def read_digital(self):
        """
        Lit la sortie digitale DOUT du MQ-135
        
        La sortie DOUT du MQ-135 passe à LOW quand le seuil de gaz est dépassé.
        Ce seuil est réglable via le potentiomètre sur le module MQ-135.
        Quand la concentration de gaz dépasse le seuil, DOUT = LOW (0).
        Quand la concentration est sous le seuil, DOUT = HIGH (1).
        
        Returns:
            bool: True si le seuil est dépassé (DOUT = LOW), False sinon
                  Retourne False en cas d'erreur ou si GPIO non disponible
        """
        if not RPI_AVAILABLE:
            return False  # Mode simulation: toujours False
        
        try:
            # DOUT est LOW quand le seuil de gaz est dépassé
            return GPIO.input(self.digital_pin) == GPIO.LOW
        except Exception as e:
            logger.error(f"✗ Erreur lecture DOUT: {e}")
            return False
    
    def calculate_ppm(self, analog_value):
        """
        Convertit la valeur analogique en PPM (parts per million)
        
        Cette méthode convertit la valeur analogique brute de l'ADS1115 en une
        concentration de gaz en PPM en utilisant la courbe de calibration du
        capteur MQ-135.
        
        Le calcul se fait en plusieurs étapes:
        1. Conversion de la valeur analogique en tension
        2. Calcul de la résistance du capteur (Rs)
        3. Calcul du ratio Rs/R0
        4. Application de la formule empirique pour obtenir la concentration en PPM
        
        La formule utilisée est basée sur la courbe du datasheet du MQ-135 pour le CO2.
        
        Args:
            analog_value (int): Valeur de l'ADS1115 (0-26400)
        
        Returns:
            float: Concentration en PPM (parts per million)
                   Retourne 0 si la tension est trop basse ou si Rs <= 0
        """
        # ============= 1. CONVERSION EN TENSION =============
        # Convertir la valeur brute (0-26400) en tension (0-4.096V)
        # ADS1115: 16-bit, plage ±4.096V par défaut
        voltage = (analog_value / 26400.0) * 4.096
        
        # ============= 2. VALIDATION DE LA TENSION =============
        # Éviter la division par zéro et les valeurs invalides
        if voltage <= 0.1:
            return 0  # Tension trop basse, retourner 0
        
        # ============= 3. CALCUL DE RS (RÉSISTANCE DU CAPTEUR) =============
        # Circuit: 5V -- RL=10kΩ -- MQ135(Rs) -- GND
        # La tension mesurée est aux bornes de RL (résistance de charge)
        # Formule: Rs = ((Vcc - Vout) * RL) / Vout
        rs = ((5.0 - voltage) * 10.0) / voltage
        
        if rs <= 0:
            return 0  # Résistance invalide, retourner 0
        
        # ============= 4. CALCUL DU RATIO RS/R0 =============
        # R0 est la résistance du capteur dans l'air pur (valeur de calibration)
        # Le ratio Rs/R0 est utilisé pour normaliser la mesure
        ratio = rs / self.r0
        
        # ============= 5. CONVERSION EN PPM =============
        # Formule empirique basée sur la courbe du datasheet du MQ-135 pour le CO2
        # ppm = 116.6020682 * (ratio ^ -2.769034857)
        ppm = 116.6020682 * (ratio ** -2.769034857)
        
        # S'assurer que la valeur est positive
        return max(0, ppm)
    
    def read(self):
        """
        Effectue une lecture complète du capteur MQ-135
        
        Cette méthode effectue une lecture complète du capteur en:
        1. Lisant la valeur analogique via l'ADS1115
        2. Convertissant la valeur analogique en PPM
        3. Lisant la sortie digitale DOUT pour vérifier si le seuil est dépassé
        4. Retournant un dictionnaire avec toutes les données
        
        Returns:
            dict: Dictionnaire contenant les données du capteur:
                  - sensor: Nom du capteur ('MQ-135')
                  - timestamp: Heure de la lecture (ISO format)
                  - raw_value: Valeur analogique brute
                  - ppm: Concentration en PPM
                  - unit: Unité de mesure ('PPM')
                  - alert: True si le seuil est dépassé, False sinon
                  Retourne None en cas d'erreur
        """
        try:
            # Lire la valeur analogique brute
            analog_value = self.read_analog_value()
            
            # Convertir en PPM
            ppm = self.calculate_ppm(analog_value)
            
            # Lire la sortie digitale DOUT
            digital_alert = self.read_digital()
            
            # Construire le dictionnaire de données
            data = {
                'sensor': 'MQ-135',
                'timestamp': datetime.now().isoformat(),
                'raw_value': analog_value,
                'ppm': round(ppm, 2),
                'unit': 'PPM',
                'alert': digital_alert
            }
            
            # Afficher les données dans les logs
            alert_msg = " ⚠️ ALERTE!" if digital_alert else ""
            logger.info(f"📊 MQ-135: {ppm:.2f} PPM{alert_msg}")
            return data
            
        except Exception as e:
            logger.error(f"✗ Erreur lecture MQ-135: {e}")
            return None
    
    def calibrate(self, clean_air_samples=50):
        """
        Calibre le capteur MQ-135 dans un environnement d'air propre
        
        La calibration est essentielle pour obtenir des mesures précises.
        Le capteur MQ-135 doit être calibré dans un environnement d'air propre
        (sans fumée, sans gaz, sans pollution) pour déterminer R0, la résistance
        du capteur dans l'air pur.
        
        Recommandations:
        - Laisser le capteur chauffer pendant au moins 24 heures avant la calibration
        - Effectuer la calibration dans un environnement bien ventilé
        - Éviter toute source de gaz ou de fumée pendant la calibration
        
        Le processus de calibration:
        1. Prendre plusieurs échantillons de lecture dans l'air propre
        2. Calculer la résistance moyenne Rs
        3. Calculer R0 = Rs / 3.6 (ratio typique dans l'air pur selon le datasheet)
        
        Args:
            clean_air_samples (int): Nombre d'échantillons à prendre (défaut: 50)
        
        Returns:
            float: La nouvelle valeur de R0 calculée
        """
        logger.info("🔧 Calibration MQ-135 (laissez le capteur dans l'air propre 24h avant)...")
        rs_sum = 0  # Somme des résistances Rs mesurées
        
        # Prendre plusieurs échantillons pour calculer la moyenne
        for i in range(clean_air_samples):
            # Lire la valeur analogique
            analog_value = self.read_analog_value()
            
            # Convertir en tension
            voltage = (analog_value / 26400.0) * 4.096
            
            # Calculer Rs si la tension est valide
            if voltage > 0.1:
                rs = ((5.0 - voltage) * 10.0) / voltage
                rs_sum += rs
            
            # Afficher la progression tous les 10 échantillons
            if (i + 1) % 10 == 0:
                logger.info(f"Calibration: {i + 1}/{clean_air_samples}")
            
            # Attendre entre chaque lecture
            time.sleep(0.5)
        
        # Calculer R0 = Rs_moyenne / 3.6
        # Le ratio 3.6 est typique pour l'air pur selon le datasheet du MQ-135
        self.r0 = (rs_sum / clean_air_samples) / 3.6
        logger.info(f"✓ Calibration terminée - R0 = {self.r0:.2f}Ω")
        return self.r0
class DHT11Sensor:
    """
    Classe pour gérer le capteur DHT11 (température et humidité)
    
    Le capteur DHT11 est un capteur numérique de température et d'humidité.
    Caractéristiques:
    - Plage de température: 0°C à 50°C (précision: ±2°C)
    - Plage d'humidité: 20% à 90% (précision: ±5%)
    - Fréquence d'échantillonnage: 1 Hz (une lecture par seconde maximum)
    - Communication: Protocole propriétaire sur une seule broche de données
    
    Fonctionnement:
    - Le capteur utilise un protocole de communication numérique propriétaire
    - La bibliothèque adafruit_dht gère ce protocole automatiquement
    - Le capteur doit être alimenté en 3.3V ou 5V
    - Une résistance de pull-up (10kΩ) est recommandée sur la broche de données
    
    Note:
    - Le capteur DHT11 est lent et ne peut être lu qu'une fois par seconde
    - Des lectures fréquentes peuvent causer des erreurs
    - Le capteur a besoin de temps pour se stabiliser après le démarrage
    """
    
    def __init__(self, pin=4):
        """
        Initialise le capteur DHT11
        
        Cette méthode configure le capteur DHT11 sur la broche GPIO spécifiée.
        La broche par défaut est GPIO 4 (broche physique 7 sur Raspberry Pi).
        
        Args:
            pin (int): Numéro du pin GPIO (défaut: 4)
                      Sur Raspberry Pi, GPIO 4 est couramment utilisé pour le DHT11
        """
        self.pin = pin  # Stocker le numéro de broche GPIO
        
        if RPI_AVAILABLE:
            try:
                # Essayer d'abord avec board.D4, sinon utiliser le numéro de pin directement
                # board.D4 est la notation préférée pour la bibliothèque adafruit_dht
                try:
                    pin_board = getattr(board, f'D{pin}')
                except AttributeError:
                    # Si D4 n'existe pas, utiliser la notation BOARD directe
                    pin_board = pin
                
                # Initialiser le capteur DHT11 avec la bibliothèque adafruit_dht
                self.sensor = adafruit_dht.DHT11(pin_board)
                logger.info(f"✓ Capteur DHT11 initialisé sur GPIO {self.pin}")
            except Exception as e:
                logger.error(f"✗ Erreur initialisation DHT11: {e}")
                logger.info("Essaie avec l'initialisation alternative...")
                self.sensor = None  # Marquer comme non initialisé
        else:
            self.sensor = None
            logger.warning("⚠ Mode simulation DHT11 activé")
    
    def read(self):
        """
        Lit la température et l'humidité du capteur DHT11
        
        Cette méthode lit les données de température et d'humidité du capteur DHT11.
        Elle inclut une gestion d'erreur robuste avec plusieurs tentatives de lecture
        car le capteur DHT11 est connu pour être instable.
        
        En mode simulation (si Raspberry Pi non disponible), génère des valeurs
        aléatoires réalistes:
        - Température: 15°C à 35°C
        - Humidité: 30% à 80%
        
        Returns:
            dict: Dictionnaire contenant les données du capteur:
                  - sensor: Nom du capteur ('DHT11')
                  - timestamp: Heure de la lecture (ISO format)
                  - temperature: Température en °C (None si erreur)
                  - humidity: Humidité en % (None si erreur)
                  - temp_unit: Unité de température ('°C')
                  - humidity_unit: Unité d'humidité ('%')
                  Retourne un dictionnaire avec None pour les valeurs en cas d'erreur
        """
        try:
            if not RPI_AVAILABLE or self.sensor is None:
                # Mode simulation: générer des valeurs aléatoires réalistes
                import random
                temperature = round(random.uniform(15.0, 35.0), 1)
                humidity = round(random.uniform(30.0, 80.0), 1)
            else:
                # Lecture réelle du capteur avec gestion d'erreur améliorée
                try:
                    # Première tentative de lecture
                    temperature = self.sensor.temperature
                    humidity = self.sensor.humidity
                    
                    # Réessayer si la lecture a échoué (valeurs None)
                    if temperature is None or humidity is None:
                        time.sleep(1)  # Attendre avant de réessayer
                        temperature = self.sensor.temperature
                        humidity = self.sensor.humidity
                        
                except RuntimeError as e:
                    # RuntimeError est courant avec le DHT11 (timeout, checksum error, etc.)
                    logger.warning(f"RuntimeError DHT11: {e}, réessai...")
                    time.sleep(2)  # Attendre plus longtemps avant de réessayer
                    temperature = self.sensor.temperature
                    humidity = self.sensor.humidity
                    
            # Vérifier la validité des données après toutes les tentatives
            if temperature is None or humidity is None:
                raise Exception("Données DHT11 invalides après plusieurs tentatives")
                
            # Construire le dictionnaire de données
            data = {
                'sensor': 'DHT11',
                'timestamp': datetime.now().isoformat(),
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'temp_unit': '°C',
                'humidity_unit': '%'
            }
            logger.info(f"🌡️ DHT11: {temperature}°C, {humidity}%")
            return data
            
        except Exception as e:
            logger.error(f"✗ Erreur lecture DHT11: {e}")
            # Retourner des données par défaut avec None au lieu de None complet
            # Cela permet au système de continuer à fonctionner même si le capteur échoue
            return {
                'sensor': 'DHT11',
                'timestamp': datetime.now().isoformat(),
                'temperature': None,
                'humidity': None,
                'temp_unit': '°C',
                'humidity_unit': '%'
            }
    def cleanup(self):
        """
        Nettoie les ressources du capteur DHT11
        
        Cette méthode libère les ressources GPIO utilisées par le capteur DHT11.
        Elle doit être appelée avant de terminer le programme pour éviter
        les problèmes de verrouillage des broches GPIO.
        """
        if RPI_AVAILABLE and self.sensor:
            self.sensor.exit()  # Libérer les ressources du capteur

class GPSSensor:
    """
    Classe pour gérer le GPS NEO-6M
    
    Le module GPS NEO-6M est un récepteur GPS qui fournit:
    - Latitude et longitude (position géographique)
    - Altitude (hauteur au-dessus du niveau de la mer)
    - Vitesse (vitesse de déplacement)
    - Date et heure UTC
    - Nombre de satellites visibles
    
    Caractéristiques:
    - Fréquence: 1575.42 MHz (bande L1 GPS)
    - Précision: ~2.5m CEP (Circle Error Probable)
    - Communication: Série (UART) à 9600 bauds par défaut
    - Protocole: NMEA 0183 (standard pour les données GPS)
    
    Fonctionnement:
    - Le module communique via le port série avec le Raspberry Pi
    - Le daemon gpsd (GPS Daemon) gère la communication avec le module GPS
    - La bibliothèque python-gpsd fournit une interface pour lire les données GPS
    - Le module peut prendre plusieurs minutes pour obtenir un fix GPS au démarrage
    
    Note:
    - Le GPS nécessite une vue dégagée du ciel pour fonctionner correctement
    - En intérieur, le GPS peut ne pas obtenir de fix ou avoir une précision réduite
    - Le module a besoin d'une antenne GPS externe pour une meilleure réception
    """
    
    def __init__(self):
        """
        Initialise le GPS NEO-6M
        
        Cette méthode initialise la connexion avec le module GPS via le daemon gpsd.
        Le daemon gpsd doit être en cours d'exécution sur le système pour que
        le GPS fonctionne.
        
        Pour démarrer gpsd:
            sudo systemctl start gpsd
            sudo gpsd /dev/ttyAMA0 -F /var/run/gpsd.sock
        
        Args:
            Aucun argument requis
        """
        self.gps_session = None  # Session GPS
        
        if GPS_AVAILABLE:
            try:
                # Initialiser la session GPS avec le mode WATCH_ENABLE
                # WATCH_ENABLE: active le mode streaming pour recevoir les données en continu
                self.gps_session = gps(mode=WATCH_ENABLE)
                logger.info("✓ GPS NEO-6M initialisé")
            except Exception as e:
                logger.error(f"✗ Erreur initialisation GPS: {e}")
                self.gps_session = None
        else:
            logger.warning("⚠ Mode simulation GPS activé")
    def read(self):
        """
        Lit les coordonnées GPS actuelles
        
        Cette méthode lit les données de position GPS du module NEO-6M via le daemon gpsd.
        Elle retourne la latitude, longitude, altitude, vitesse et d'autres informations.
        
        En mode simulation (si GPS non disponible), retourne des coordonnées par défaut
        (Tunis, Tunisie: 36.8065, 10.1815).
        
        Returns:
            dict: Dictionnaire contenant les données GPS:
                  - sensor: Nom du capteur ('GPS NEO-6M')
                  - timestamp: Heure de la lecture (ISO format)
                  - latitude: Latitude en degrés décimaux (None si pas de fix)
                  - longitude: Longitude en degrés décimaux (None si pas de fix)
                  - altitude: Altitude en mètres (0 si pas disponible)
                  - speed: Vitesse en m/s (0 si pas disponible)
                  - fix: True si fix GPS obtenu, False sinon
                  - satellites: Nombre de satellites visibles (0 si pas disponible)
                  Retourne un dictionnaire avec None pour latitude/longitude si pas de fix
        """
        try:
            if not GPS_AVAILABLE or self.gps_session is None:
                # Mode simulation: coordonnées d'exemple (Tunis, Tunisie)
                data = {
                    'sensor': 'GPS NEO-6M',
                    'timestamp': datetime.now().isoformat(),
                    'latitude': 36.8065,
                    'longitude': 10.1815,
                    'altitude': 0,
                    'fix': True,
                    'satellites': 0
                }
            else:
                # Lecture réelle du GPS via gpsd
                report = self.gps_session.next()  # Attendre le prochain rapport GPS
                
                # Vérifier si le rapport est de type TPV (Time-Position-Velocity)
                # TPV contient les données de position et de vitesse
                if report['class'] == 'TPV':
                    data = {
                        'sensor': 'GPS NEO-6M',
                        'timestamp': datetime.now().isoformat(),
                        'latitude': getattr(report, 'lat', 0.0),  # Latitude
                        'longitude': getattr(report, 'lon', 0.0),  # Longitude
                        'altitude': getattr(report, 'alt', 0.0),  # Altitude
                        'speed': getattr(report, 'speed', 0.0),  # Vitesse
                        'fix': True,  # Fix GPS obtenu
                        'satellites': getattr(report, 'satellites', 0)  # Nombre de satellites
                    }
                else:
                    raise Exception("Pas de fix GPS")
            
            logger.info(f"📍 GPS: {data['latitude']:.6f}, {data['longitude']:.6f}")
            return data
        except Exception as e:
            logger.error(f"✗ Erreur lecture GPS: {e}")
            # Retourner des données par défaut avec fix=False
            return {
                'sensor': 'GPS NEO-6M',
                'timestamp': datetime.now().isoformat(),
                'latitude': None,
                'longitude': None,
                'fix': False
            }
class SensorManager:
    """
    Gestionnaire central pour tous les capteurs
    
    Cette classe coordonne la lecture de tous les capteurs et agrège les données
    dans un format unifié. Elle agit comme une interface unique pour accéder
    à tous les capteurs du système.
    
    Capteurs gérés:
    - MQ135Sensor: Capteur de qualité de l'air
    - DHT11Sensor: Capteur de température et d'humidité
    - GPSSensor: Module GPS pour la localisation
    
    Fonctionnement:
    - Initialise tous les capteurs au démarrage
    - Lit tous les capteurs simultanément
    - Agrège les données dans un dictionnaire structuré
    - Gère le nettoyage des ressources à l'arrêt
    
    Avantages:
    - Interface unifiée pour tous les capteurs
    - Gestion centralisée des erreurs
    - Format de données cohérent
    - Facile à étendre avec de nouveaux capteurs
    """
    
    def __init__(self, mq135_pin=17, dht11_pin=4, gps_enabled=True):
        """
        Initialise tous les capteurs
        
        Cette méthode initialise tous les capteurs du système avec leurs
        configurations respectives (broches GPIO, activation/désactivation).
        
        Args:
            mq135_pin (int): Pin GPIO pour le MQ-135 (défaut: GPIO 17)
            dht11_pin (int): Pin GPIO pour le DHT11 (défaut: GPIO 4)
            gps_enabled (bool): Activer ou désactiver le GPS (défaut: True)
                             Le GPS peut être désactivé si non utilisé
        """
        logger.info("🚀 Initialisation du système de capteurs...")
        
        # Initialiser chaque capteur
        self.mq135 = MQ135Sensor(mq135_pin)  # Capteur de qualité de l'air
        self.dht11 = DHT11Sensor(dht11_pin)  # Capteur de température/humidité
        self.gps = GPSSensor() if gps_enabled else None  # GPS (optionnel)
        
        logger.info("✓ Tous les capteurs sont initialisés")
    
    def read_all_sensors(self):
        """
        Lit tous les capteurs et retourne les données agrégées
        
        Cette méthode lit tous les capteurs simultanément et agrège les données
        dans un dictionnaire structuré. Si un capteur échoue, sa valeur est
        définie à None mais le système continue de fonctionner.
        
        Returns:
            dict: Dictionnaire contenant toutes les données des capteurs:
                  - timestamp: Heure de la lecture (ISO format)
                  - air_quality: Dictionnaire avec ppm et raw_value
                  - temperature: Température en °C (None si erreur)
                  - humidity: Humidité en % (None si erreur)
                  - location: Dictionnaire avec latitude, longitude, fix (None si GPS désactivé)
        """
        logger.info("📊 Lecture de tous les capteurs...")
        
        # Lire chaque capteur individuellement
        mq135_data = self.mq135.read()  # Lire le MQ-135
        dht11_data = self.dht11.read()  # Lire le DHT11
        gps_data = self.gps.read() if self.gps else None  # Lire le GPS si activé
        
        # Agréger les données dans un dictionnaire structuré
        aggregated_data = {
            'timestamp': datetime.now().isoformat(),
            'air_quality': {
                'ppm': mq135_data['ppm'] if mq135_data else None,
                'raw_value': mq135_data['raw_value'] if mq135_data else None
            },
            'temperature': dht11_data['temperature'] if dht11_data else None,
            'humidity': dht11_data['humidity'] if dht11_data else None,
            'location': {
                'latitude': gps_data['latitude'] if gps_data else None,
                'longitude': gps_data['longitude'] if gps_data else None,
                'fix': gps_data['fix'] if gps_data else False
            } if gps_data else None
        }
        
        logger.info("✓ Lecture de tous les capteurs terminée")
        return aggregated_data
    
    def cleanup(self):
        """
        Nettoie toutes les ressources des capteurs
        
        Cette méthode libère toutes les ressources GPIO utilisées par les capteurs.
        Elle doit être appelée avant de terminer le programme pour éviter
        les problèmes de verrouillage des broches GPIO.
        
        Opérations de nettoyage:
        - Nettoyage des broches GPIO (GPIO.cleanup())
        - Libération des ressources du DHT11 (sensor.exit())
        """
        logger.info("🧹 Nettoyage des ressources...")
        
        if RPI_AVAILABLE:
            GPIO.cleanup()  # Libérer toutes les broches GPIO
        
        self.dht11.cleanup()  # Libérer les ressources du DHT11
        
        logger.info("✓ Nettoyage terminé")
# ============= TEST DU MODULE =============
# Ce bloc de code est exécuté uniquement si le script est lancé directement
# (pas lorsqu'il est importé comme module). Il permet de tester les capteurs
# individuellement sans lancer le système complet.

if __name__ == "__main__":
    print("=== Test du système de capteurs ===\n")
    
    # Créer le gestionnaire de capteurs avec les broches par défaut
    sensor_manager = SensorManager()
    
    try:
        # Lire les capteurs 5 fois avec un délai de 3 secondes entre chaque lecture
        for i in range(5):
            print(f"\n--- Lecture {i + 1}/5 ---")
            
            # Lire tous les capteurs
            data = sensor_manager.read_all_sensors()
            
            # Afficher les données de chaque capteur
            print(f"Qualité de l'air: {data['air_quality']['ppm']} PPM")
            print(f"Température: {data['temperature']}°C")
            print(f"Humidité: {data['humidity']}%")
            
            # Afficher les coordonnées GPS si disponibles
            if data['location']:
                print(f"Position: {data['location']['latitude']}, {data['location']['longitude']}")
            
            # Attendre 3 secondes avant la prochaine lecture
            time.sleep(3)
            
    except KeyboardInterrupt:
        # Gérer l'interruption par Ctrl+C
        print("\n\n⚠ Arrêt demandé par l'utilisateur")
    finally:
        # Nettoyer les ressources avant de quitter
        sensor_manager.cleanup()
        print("\n✓ Test terminé")
