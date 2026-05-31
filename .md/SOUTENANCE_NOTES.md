# Notes pour la soutenance

Objectif: présenter une version simple et claire du système pour le jury.

Fichiers fournis:
- `sensors_simple.py`: lecture simulée, petite classe `SensorSimple.read()`.
- `main_simple.py`: script d'exécution minimal qui montre le flux (init -> read -> affichage).
- `sensors2.py`: version complète (conserver pour questions techniques). Ne pas présenter en détail, mais mentionner les améliorations (fallback météo, GPS forcé).

Conseils pour la présentation (2-3 minutes):
1. Start: expliquer l'objectif (mesurer qualité de l'air, sauvegarder, prédire).
2. Architecture: 3 couches simples - acquisition (sensors), stockage & traitement (DB + ML), interface (Flask)
3. Démo: exécuter `python main_simple.py` et lire les valeurs.
4. Points techniques clés à mentionner:
   - MQ-135 (analogique via ADS1115), DHT11 (température/humidité), GPS forcé à Casablanca.
   - Fallback: si capteur DHT11 indisponible, on récupère météo via API.
   - Robustesse: la version complète gère absences matérielles et évite d'insérer des NULL en base.
5. Scénarios d'amélioration: collecte MQTT, UI en temps réel, calibration automatique MQ-135.

Commandes utiles pour la démo:
```bash
python versel/main_simple.py
```

Questions probables & réponses brèves:
- Q: Que se passe-t-il si le capteur n'est pas connecté ?
  R: Le système remonte des valeurs de secours (API météo) et évite l'insertion de données incomplètes.
- Q: Pourquoi forcer Casablanca ?
  R: Demande du projet pour restreindre la géolocalisation à la zone d'étude.
