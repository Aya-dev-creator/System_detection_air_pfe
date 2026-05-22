"""
Minimal main script for presentation purposes.

Shows how the system is structured in 6-8 lines so you can explain
the flow to the jury without diving into hardware details.
"""
from sensors_simple import SensorSimple


def main():
    print('DÉMO: Système simplifié de surveillance de la qualité de l\'air')
    # 1. Initialiser (dans la version simple on n'a pas de DB/ML)
    sensors = SensorSimple()

    # 2. Lire les capteurs
    reading = sensors.read()

    # 3. Afficher les valeurs (ce bloc est ce que vous montrez au jury)
    print('Timestamp:', reading['timestamp'])
    print('Air quality (PPM):', reading['air_quality_ppm'])
    print('Temperature (°C):', reading['temperature_c'])
    print('Humidity (%):', reading['humidity_pct'])
    print('Location:', reading['latitude'], reading['longitude'])


if __name__ == '__main__':
    main()
