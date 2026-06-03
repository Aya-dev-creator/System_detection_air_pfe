#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de démonstration du module Entreprises & Industries
Montre comment utiliser les fonctions de parsing et de recommendations

Utilisation:
    python demo_entreprises.py
"""

import sys
import io
import json
from datetime import datetime

# Ajouter le répertoire courant au path
sys.path.insert(0, '.')

from web_server import parse_csv_pollution_data, generate_folium_map
from weather_chatbot import get_chatbot


def demo_parse_csv():
    """
    Démontre le parsing d'un fichier CSV
    """
    print("\n" + "="*80)
    print("📊 DÉMONSTRATION 1: Parsing CSV")
    print("="*80)
    
    # Créer un CSV d'exemple en mémoire
    csv_content = """timestamp,pm2_5,pm10,co,no2,so2,co2,temperature,humidity
2024-01-15 08:00:00,28.5,45.2,2.3,35.1,12.5,550,22.5,65
2024-01-15 09:00:00,32.1,48.7,2.8,38.5,14.2,610,23.1,62
2024-01-15 10:00:00,26.8,42.1,2.1,32.8,11.3,520,24.2,58
2024-01-15 11:00:00,35.2,51.3,3.2,41.2,15.8,680,25.5,55
2024-01-15 12:00:00,29.9,46.5,2.5,36.9,13.1,580,26.1,52"""
    
    # Convertir en BytesIO (simule un upload)
    file_stream = io.BytesIO(csv_content.encode('utf-8'))
    
    # Parser
    print("\n📁 CSV à parser:")
    print(csv_content[:200] + "...")
    
    result = parse_csv_pollution_data(file_stream)
    
    if result['success']:
        print("\n✅ Parsing réussi!")
        print(f"\n📈 Moyennes par polluant:")
        for key, value in result['average_factors'].items():
            print(f"   • {key}: {value:.2f}")
        
        print(f"\n📊 Pourcentages par rapport aux seuils critiques:")
        for pollutant, percentage in result['pollution_summary'].items():
            status = "🟢" if percentage <= 50 else "🟡" if percentage <= 100 else "🔴"
            print(f"   {status} {pollutant}: {percentage:.1f}%")
        
        print(f"\n📝 Nombre d'enregistrements: {result['num_records']}")
        return result
    else:
        print(f"\n❌ Erreur: {result['error']}")
        return None


def demo_mistral_recommendations(pollution_summary):
    """
    Démontre la génération de recommendations via Mistral AI
    """
    print("\n" + "="*80)
    print("🤖 DÉMONSTRATION 2: Recommandations Mistral AI")
    print("="*80)
    
    print("\n🏭 Contexte d'analyse:")
    print(f"   • Entité: Usine Nord Casablanca")
    print(f"   • Type: Usine")
    print(f"   • Polluants analysés: {len(pollution_summary)}")
    
    print("\n⏳ Génération du rapport via Mistral AI (peut prendre 5-10s)...")
    
    try:
        chatbot = get_chatbot()
        
        ai_report = chatbot.generate_industrial_recommendations(
            entity_name="Usine Nord Casablanca",
            entity_type="Usine",
            pollution_summary=pollution_summary
        )
        
        print("\n✅ Rapport généré avec succès!\n")
        print("-" * 80)
        print("📋 RAPPORT IA (HTML):")
        print("-" * 80)
        print(ai_report[:500] + "...")
        print("-" * 80)
        
        return ai_report
    
    except Exception as e:
        print(f"\n❌ Erreur Mistral: {str(e)}")
        return None


def demo_sorting():
    """
    Démontre le tri côté serveur
    """
    print("\n" + "="*80)
    print("📊 DÉMONSTRATION 3: Tri côté serveur (SSR)")
    print("="*80)
    
    pollution_items = [
        {'name': 'PM2.5', 'percentage': 86.1, 'value': 30.14},
        {'name': 'PM10', 'percentage': 94.5, 'value': 47.25},
        {'name': 'CO', 'percentage': 52.0, 'value': 2.6},
        {'name': 'NO2', 'percentage': 92.9, 'value': 37.14},
        {'name': 'SO2', 'percentage': 66.8, 'value': 13.36},
        {'name': 'CO2', 'percentage': 73.8, 'value': 590.0},
    ]
    
    print("\n📌 Données originales:")
    for item in pollution_items:
        print(f"   • {item['name']}: {item['percentage']:.1f}%")
    
    # Tri par taux croissant
    print("\n🔽 TRI 1: Taux croissant (?sort_by=rate&order=asc)")
    sorted_items = sorted(pollution_items, key=lambda x: x['percentage'])
    for item in sorted_items:
        print(f"   • {item['name']}: {item['percentage']:.1f}%")
    
    # Tri par taux décroissant
    print("\n🔼 TRI 2: Taux décroissant (?sort_by=rate&order=desc)")
    sorted_items = sorted(pollution_items, key=lambda x: x['percentage'], reverse=True)
    for item in sorted_items:
        print(f"   • {item['name']}: {item['percentage']:.1f}%")
    
    # Tri par nom
    print("\n📛 TRI 3: Nom alphabétique (?sort_by=name&order=asc)")
    sorted_items = sorted(pollution_items, key=lambda x: x['name'])
    for item in sorted_items:
        print(f"   • {item['name']}: {item['percentage']:.1f}%")


def demo_css_bars():
    """
    Démontre les barres CSS
    """
    print("\n" + "="*80)
    print("🎨 DÉMONSTRATION 4: Barres de progression CSS")
    print("="*80)
    
    pollution_items = [
        {'name': 'PM2.5', 'percentage': 86.1},
        {'name': 'PM10', 'percentage': 94.5},
        {'name': 'CO', 'percentage': 52.0},
        {'name': 'NO2', 'percentage': 92.9},
    ]
    
    print("\n📊 Rendu des barres CSS (simulation console):\n")
    
    for item in pollution_items:
        pct = item['percentage']
        
        # Déterminer la couleur
        if pct <= 50:
            color = "🟢"
        elif pct <= 100:
            color = "🟡"
        else:
            color = "🔴"
        
        # Créer la barre (10 caractères = 100%)
        bar_length = int(pct / 10)
        bar = "█" * bar_length + "░" * (10 - bar_length)
        
        print(f"{color} {item['name']:8} | {bar} | {pct:6.1f}%")


def demo_url_parameters():
    """
    Démontre les paramètres URL et le rendu SSR
    """
    print("\n" + "="*80)
    print("🔗 DÉMONSTRATION 5: Paramètres URL (SSR)")
    print("="*80)
    
    examples = [
        ("GET /entreprise/dashboard", "Affiche le dashboard avec tri par défaut (nom ASC)"),
        ("GET /entreprise/dashboard?sort_by=rate&order=desc", "Affiche trié par taux décroissant"),
        ("GET /entreprise/dashboard?sort_by=value&order=asc", "Affiche trié par valeur croissante"),
    ]
    
    print("\n📌 Exemples d'URLs et leur comportement:\n")
    
    for url, description in examples:
        print(f"   {url}")
        print(f"   → {description}\n")


def demo_session_flow():
    """
    Démontre le flux de stockage en session
    """
    print("\n" + "="*80)
    print("💾 DÉMONSTRATION 6: Stockage en session Flask")
    print("="*80)
    
    print("\n📋 Flux utilisateur:\n")
    
    steps = [
        ("1. POST /entreprise/upload", "Utilisateur envoie CSV + type + nom"),
        ("   ↓", ""),
        ("2. parse_csv_pollution_data()", "Serveur parse le CSV (1-5s)"),
        ("   ↓", ""),
        ("3. session['entreprise_data'] = {...}", "Données stockées en mémoire Flask"),
        ("   ↓", ""),
        ("4. redirect(/entreprise/dashboard)", "Redirection utilisateur"),
        ("   ↓", ""),
        ("5. GET /entreprise/dashboard", "Récupère données de la session"),
        ("   ↓", ""),
        ("6. Tri Python appliqué", "Tris côté serveur (aucun JS)"),
        ("   ↓", ""),
        ("7. render_template('...', data=...)", "Retourne HTML final"),
    ]
    
    for step, desc in steps:
        if desc:
            print(f"{step:40} → {desc}")
        else:
            print(step)


def main():
    """
    Fonction principale de démonstration
    """
    print("\n" + "="*80)
    print("🏭 AirWatch - Module Entreprises & Industries")
    print("📚 Démonstration complète")
    print("="*80)
    
    # Démo 1: Parsing CSV
    parse_result = demo_parse_csv()
    
    if not parse_result:
        print("\n❌ Impossible de continuer sans données de pollution")
        return
    
    # Démo 2: Recommendations Mistral
    # (Optionnel, car nécessite une clé API)
    try:
        ai_report = demo_mistral_recommendations(parse_result['pollution_summary'])
    except Exception as e:
        print(f"\n⚠️  Mistral AI non disponible: {str(e)}")
        ai_report = None
    
    # Démo 3: Tri
    demo_sorting()
    
    # Démo 4: Barres CSS
    demo_css_bars()
    
    # Démo 5: Paramètres URL
    demo_url_parameters()
    
    # Démo 6: Flux session
    demo_session_flow()
    
    print("\n" + "="*80)
    print("✅ Démonstration terminée!")
    print("="*80)
    print("\n📌 Prochaines étapes:")
    print("   1. Installer les dépendances: pip install -r requirements.txt")
    print("   2. Configurer la clé Mistral: MISTRAL_API_KEY=sk-... dans .env")
    print("   3. Démarrer le serveur: python web_server.py")
    print("   4. Accéder au formulaire: http://localhost:5000/entreprise")
    print("\n")


if __name__ == '__main__':
    main()
