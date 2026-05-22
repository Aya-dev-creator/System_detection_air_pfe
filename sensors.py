"""
Single sensor module (merged) for the project.

This file is a direct copy of the cleaned `sensors2.py` implementation
but placed at `sensors.py` so the project has a single sensor module.
"""

import os
import platform
import time
from datetime import datetime
import logging
import requests
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IS_RPI = platform.system() == "Linux" and platform.machine().lower().startswith(("arm", "aarch64"))

board = None
busio = None
adafruit_dht = None
GPIO = None
ADS = None
AnalogIn = None
HARDWARE_AVAILABLE = False

if IS_RPI:
    try:
        import board
        import busio
        import adafruit_dht
        import RPi.GPIO as GPIO
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn
        HARDWARE_AVAILABLE = True
    except Exception as e:
        logger.warning(f"Raspberry Pi hardware libraries unavailable: {e}")
        HARDWARE_AVAILABLE = False
else:
    logger.warning("Raspberry Pi hardware libraries are unavailable on this platform. Sensor hardware will run in fallback mode.")

logger.info(f"Platform detection: system={platform.system()}, machine={platform.machine()}, IS_RPI={IS_RPI}, HARDWARE_AVAILABLE={HARDWARE_AVAILABLE}")


class MQ135Sensor:
    def __init__(self, digital_pin=17, adc_channel=0, pin=None):
        if pin is not None:
            digital_pin = pin

        self.digital_pin = digital_pin
        self.adc_channel = adc_channel
        self.r0 = 10.0
        self.ads = None
        self.adc_channel_obj = None
        self.available = HARDWARE_AVAILABLE

        if not self.available:
            logger.warning("MQ-135 hardware unavailable; fonction de lecture en mode simulation.")
            return

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            while not i2c.try_lock():
                time.sleep(0.1)
            logger.info("Scanning I2C bus...")
            addresses = i2c.scan()
            i2c.unlock()
            if addresses:
                logger.info(f"Adresses I2C trouvées: {[hex(addr) for addr in addresses]}")
            else:
                logger.warning("Aucune adresse I2C trouvée")

            for attempt in range(3):
                try:
                    self.ads = ADS.ADS1115(i2c, address=0x48)
                    channel_map = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
                    channel_attr = channel_map.get(adc_channel, ADS.P0)
                    self.adc_channel_obj = AnalogIn(self.ads, channel_attr)
                    logger.info(f"ADS1115 initialisé sur canal {adc_channel} (adresse 0x48)")
                    break
                except ValueError as e:
                    if "0x48" in str(e):
                        logger.warning(f"Tentative {attempt + 1}/3: {e}")
                        time.sleep(1)
                    else:
                        raise
                except Exception as e:
                    logger.error(f"Erreur initialisation ADS1115: {e}")
                    break

            if self.adc_channel_obj is None:
                logger.error("Impossible d'initialiser l'ADS1115 après plusieurs tentatives")
                self.available = False
                return

        except Exception as e:
            logger.error(f"Erreur initialisation ADS1115/I2C: {e}")
            self.available = False
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.digital_pin, GPIO.IN)
            logger.info(f"Capteur MQ-135 DOUT initialisé sur GPIO {self.digital_pin}")
        except Exception as e:
            logger.error(f"Erreur initialisation GPIO: {e}")
            self.available = False
            return

    def read_analog_value(self):
        if self.adc_channel_obj is None:
            logger.error("ADS1115 channel object unavailable; cannot read analog value.")
            return 0

        try:
            value = self.adc_channel_obj.value
            voltage = self.adc_channel_obj.voltage
            logger.debug(f"ADS1115 - Raw: {value}, Voltage: {voltage:.3f}V")
            return value
        except Exception as e:
            logger.error(f"Erreur lecture ADS1115: {e}")
            return 0

    def read_digital(self):
        if not getattr(self, 'available', False):
            logger.warning("MQ-135 digital read unavailable; returning False.")
            return False
        try:
            return GPIO.input(self.digital_pin) == GPIO.LOW
        except Exception as e:
            logger.error(f"Erreur lecture DOUT: {e}")
            return False

    def calculate_ppm(self, analog_value):
        voltage = (analog_value / 26400.0) * 4.096
        if voltage <= 0.1:
            return 0
        rs = ((5.0 - voltage) * 10.0) / voltage
        if rs <= 0:
            return 0
        ratio = rs / self.r0
        ppm = 116.6020682 * (ratio ** -2.769034857)
        return max(0, ppm)

    def read(self):
        if not getattr(self, 'available', False):
            logger.warning("MQ-135 hardware unavailable, renvoyant valeurs par défaut.")
            return {
                'sensor': 'MQ-135',
                'timestamp': datetime.now().isoformat(),
                'raw_value': None,
                'ppm': None,
                'unit': 'PPM',
                'alert': False
            }
        try:
            analog_value = self.read_analog_value()
            ppm = self.calculate_ppm(analog_value)
            digital_alert = self.read_digital()
            data = {
                'sensor': 'MQ-135',
                'timestamp': datetime.now().isoformat(),
                'raw_value': analog_value,
                'ppm': round(ppm, 2),
                'unit': 'PPM',
                'alert': digital_alert
            }
            alert_msg = " ALERTE!" if digital_alert else ""
            logger.info(f"MQ-135: {ppm:.2f} PPM{alert_msg}")
            return data
        except Exception as e:
            logger.error(f"Erreur lecture MQ-135: {e}")
            return None

    def calibrate(self, clean_air_samples=50):
        logger.info("Calibration MQ-135 (laissez le capteur dans l'air propre 24h avant)...")
        rs_sum = 0
        for i in range(clean_air_samples):
            analog_value = self.read_analog_value()
            voltage = (analog_value / 26400.0) * 4.096
            if voltage > 0.1:
                rs = ((5.0 - voltage) * 10.0) / voltage
                rs_sum += rs
            if (i + 1) % 10 == 0:
                logger.info(f"Calibration: {i + 1}/{clean_air_samples}")
            time.sleep(0.5)
        self.r0 = (rs_sum / clean_air_samples) / 3.6
        logger.info(f"Calibration terminée - R0 = {self.r0:.2f}Ω")
        return self.r0


class DHT11Sensor:
    def __init__(self, pin=4):
        self.pin = pin
        self.available = HARDWARE_AVAILABLE
        self.sensor = None
        if not self.available:
            logger.warning("DHT11 hardware unavailable; lecture en mode simulation.")
            return
        try:
            pin_board = getattr(board, f'D{pin}')
        except AttributeError:
            pin_board = pin
        try:
            self.sensor = adafruit_dht.DHT11(pin_board)
            logger.info(f"Capteur DHT11 initialisé sur GPIO {self.pin}")
        except Exception as e:
            logger.error(f"Erreur initialisation DHT11: {e}")
            self.available = False
            self.sensor = None
            logger.warning("DHT11 hardware unavailable; lecture en mode simulation.")

    def read(self):
        if not getattr(self, 'available', False):
            return {
                'sensor': 'DHT11',
                'timestamp': datetime.now().isoformat(),
                'temperature': None,
                'humidity': None,
                'temp_unit': '°C',
                'humidity_unit': '%'
            }
        try:
            try:
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity
                if temperature is None or humidity is None:
                    time.sleep(1)
                    temperature = self.sensor.temperature
                    humidity = self.sensor.humidity
            except RuntimeError as e:
                logger.warning(f"RuntimeError DHT11: {e}, réessai...")
                time.sleep(2)
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity
            if temperature is None or humidity is None:
                raise Exception("Données DHT11 invalides après plusieurs tentatives")
            data = {
                'sensor': 'DHT11',
                'timestamp': datetime.now().isoformat(),
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'temp_unit': '°C',
                'humidity_unit': '%'
            }
            logger.info(f"DHT11: {temperature}°C, {humidity}%")
            return data
        except Exception as e:
            logger.error(f"Erreur lecture DHT11: {e}")
            return {
                'sensor': 'DHT11',
                'timestamp': datetime.now().isoformat(),
                'temperature': None,
                'humidity': None,
                'temp_unit': '°C',
                'humidity_unit': '%'
            }

    def cleanup(self):
        if self.sensor is not None:
            self.sensor.exit()


class GPSSensor:
    def __init__(self):
        self.gps_session = None
        logger.info("Localisation initialisée (forcée sur Casablanca)")

    def read(self):
        try:
            latitude = float(config.MAP_CENTER_LAT)
            longitude = float(config.MAP_CENTER_LON)
            data = {
                'sensor': 'Device Location',
                'timestamp': datetime.now().isoformat(),
                'latitude': latitude,
                'longitude': longitude,
                'altitude': 0,
                'fix': True,
                'satellites': 0
            }
            logger.info(f"GPS forcé à Casablanca: {latitude:.6f}, {longitude:.6f}")
            return data
        except Exception as e:
            logger.error(f"Erreur lecture localisation (fallback Casablanca): {e}")
            return {
                'sensor': 'Device Location',
                'timestamp': datetime.now().isoformat(),
                'latitude': None,
                'longitude': None,
                'fix': False
            }


class SensorManager:
    def __init__(self, mq135_pin=17, dht11_pin=4, gps_enabled=True):
        logger.info("Initialisation du système de capteurs...")
        logger.info(f"SensorManager config: mq135_pin={mq135_pin}, dht11_pin={dht11_pin}, gps_enabled={gps_enabled}, HARDWARE_AVAILABLE={HARDWARE_AVAILABLE}")
        self.mq135 = MQ135Sensor(mq135_pin)
        self.dht11 = DHT11Sensor(dht11_pin)
        self.gps = GPSSensor() if gps_enabled else None
        logger.info("Tous les capteurs sont initialisés")

    def read_all_sensors(self):
        logger.info("Lecture de tous les capteurs...")
        mq135_data = self.mq135.read()
        dht11_data = self.dht11.read()
        gps_data = self.gps.read() if self.gps else None
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
        logger.info("Lecture de tous les capteurs terminée")
        return aggregated_data

    def cleanup(self):
        logger.info("Nettoyage des ressources...")
        try:
            if GPIO is not None:
                GPIO.cleanup()
        except Exception:
            pass
        try:
            self.dht11.cleanup()
        except Exception:
            pass
        logger.info("Nettoyage terminé")


if __name__ == "__main__":
    print("=== Test du système de capteurs ===\n")
    sensor_manager = SensorManager()
    try:
        for i in range(5):
            print(f"\n--- Lecture {i + 1}/5 ---")
            data = sensor_manager.read_all_sensors()
            print(f"Qualité de l'air: {data['air_quality']['ppm']} PPM")
            print(f"Température: {data['temperature']}°C")
            print(f"Humidité: {data['humidity']}%")
            if data['location']:
                print(f"Position: {data['location']['latitude']}, {data['location']['longitude']}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n\nArrêt demandé par l'utilisateur")
    finally:
        sensor_manager.cleanup()
        print("\nTest terminé")
