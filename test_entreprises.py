#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test du module Entreprises & Industries
Valide les imports, la configuration et les fonctionnalités principales

Utilisation:
    python test_entreprises.py
"""

import sys
import os
import io

# Ajouter le répertoire courant au path
sys.path.insert(0, '.')

def test_imports():
    """Teste les imports"""
    print("\n✓ TEST 1: Imports")
    print("  " + "-"*60)
    
    try:
        from config import config
        print("  ✅ config.py")
    except Exception as e:
        print(f"  ❌ config.py: {e}")
        return False
    
    try:
        from weather_chatbot import WeatherChatbot, get_chatbot
        print("  ✅ weather_chatbot.py")
    except Exception as e:
        print(f"  ❌ weather_chatbot.py: {e}")
        return False
    
    try:
        from web_server import app, allowed_file, parse_csv_pollution_data, generate_folium_map
        print("  ✅ web_server.py (app + fonctions)")
    except Exception as e:
        print(f"  ❌ web_server.py: {e}")
        return False
    
    try:
        import folium
        print("  ✅ folium (optionnel)")
    except Exception as e:
        print(f"  ⚠️  folium (optionnel): {e}")
    
    return True


def test_config():
    """Teste la configuration"""
    print("\n✓ TEST 2: Configuration")
    print("  " + "-"*60)
    
    from config import config
    
    # Vérifier ALLOWED_EXTENSIONS
    allowed = config.FLASK_CONFIG.get('ALLOWED_EXTENSIONS', set())
    if 'csv' in allowed:
        print("  ✅ ALLOWED_EXTENSIONS contient 'csv'")
    else:
        print(f"  ❌ ALLOWED_EXTENSIONS: {allowed} (devrait contenir 'csv')")
        return False
    
    # Vérifier UPLOAD_FOLDER
    upload_folder = config.FLASK_CONFIG.get('UPLOAD_FOLDER', '')
    if upload_folder:
        print(f"  ✅ UPLOAD_FOLDER configuré: {upload_folder}")
    else:
        print("  ❌ UPLOAD_FOLDER non configuré")
        return False
    
    # Vérifier que le dossier existe
    os.makedirs(upload_folder, exist_ok=True)
    print(f"  ✅ Dossier d'upload existe: {upload_folder}")
    
    return True


def test_allowed_file():
    """Teste la validation des extensions"""
    print("\n✓ TEST 3: Validation des extensions")
    print("  " + "-"*60)
    
    from web_server import allowed_file
    
    test_cases = [
        ("data.csv", True),
        ("pollution.CSV", True),
        ("data.txt", False),
        ("file.xlsx", False),
        ("", False),
    ]
    
    all_passed = True
    for filename, expected in test_cases:
        result = allowed_file(filename)
        status = "✅" if result == expected else "❌"
        print(f"  {status} allowed_file('{filename}'): {result} (attendu: {expected})")
        all_passed = all_passed and (result == expected)
    
    return all_passed


def test_csv_parsing():
    """Teste le parsing CSV"""
    print("\n✓ TEST 4: Parsing CSV")
    print("  " + "-"*60)
    
    from web_server import parse_csv_pollution_data
    
    # Créer un CSV d'exemple
    csv_content = """timestamp,pm2_5,pm10,co,no2,so2,co2
2024-01-15 08:00,28.5,45.2,2.3,35.1,12.5,550
2024-01-15 09:00,32.1,48.7,2.8,38.5,14.2,610
2024-01-15 10:00,26.8,42.1,2.1,32.8,11.3,520"""
    
    file_stream = io.BytesIO(csv_content.encode('utf-8'))
    
    result = parse_csv_pollution_data(file_stream)
    
    if not result['success']:
        print(f"  ❌ Parsing échoué: {result.get('error', 'Erreur inconnue')}")
        return False
    
    print(f"  ✅ Parsing réussi")
    print(f"  ✅ Nombre d'enregistrements: {result.get('num_records', 0)}")
    
    factors = result.get('average_factors', {})
    summary = result.get('pollution_summary', {})
    
    if factors:
        print(f"  ✅ Moyennes calculées: {len(factors)} polluants")
        for key, val in list(factors.items())[:3]:
            print(f"     • {key}: {val:.2f}")
    else:
        print(f"  ❌ Aucune moyenne calculée")
        return False
    
    if summary:
        print(f"  ✅ Pourcentages calculés: {len(summary)} polluants")
        for key, val in list(summary.items())[:3]:
            print(f"     • {key}: {val:.1f}%")
    else:
        print(f"  ❌ Aucun pourcentage calculé")
        return False
    
    return True


def test_mistral_method():
    """Teste l'existence de la méthode Mistral"""
    print("\n✓ TEST 5: Méthode generate_industrial_recommendations")
    print("  " + "-"*60)
    
    try:
        from weather_chatbot import WeatherChatbot
        
        # Vérifier que la méthode existe
        if hasattr(WeatherChatbot, 'generate_industrial_recommendations'):
            print("  ✅ Méthode generate_industrial_recommendations existe")
        else:
            print("  ❌ Méthode generate_industrial_recommendations n'existe pas")
            return False
        
        # Vérifier la signature
        import inspect
        sig = inspect.signature(WeatherChatbot.generate_industrial_recommendations)
        params = list(sig.parameters.keys())
        expected_params = ['self', 'entity_name', 'entity_type', 'pollution_summary']
        
        if params == expected_params:
            print(f"  ✅ Signature correcte: {', '.join(params)}")
        else:
            print(f"  ⚠️  Signature: {params} (attendu: {expected_params})")
        
        return True
    
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def test_routes():
    """Teste l'existence des routes"""
    print("\n✓ TEST 6: Routes Flask")
    print("  " + "-"*60)
    
    from web_server import app
    
    required_routes = [
        '/entreprise',
        '/entreprise/upload',
        '/entreprise/dashboard',
        '/map-view',
    ]
    
    # Obtenir toutes les routes enregistrées
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(rule.rule)
    
    all_found = True
    for route in required_routes:
        if route in routes:
            print(f"  ✅ Route {route}")
        else:
            print(f"  ❌ Route {route} manquante")
            all_found = False
    
    return all_found


def test_templates():
    """Teste l'existence des templates"""
    print("\n✓ TEST 7: Templates HTML")
    print("  " + "-"*60)
    
    templates_dir = 'templates'
    required_templates = [
        'entreprise_upload.html',
        'entreprise_dashboard.html',
        'static_map_render.html',
    ]
    
    all_found = True
    for template in required_templates:
        path = os.path.join(templates_dir, template)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✅ {template} ({size} bytes)")
        else:
            print(f"  ❌ {template} manquant")
            all_found = False
    
    return all_found


def test_sample_csv():
    """Teste la présence du CSV d'exemple"""
    print("\n✓ TEST 8: Fichier CSV d'exemple")
    print("  " + "-"*60)
    
    csv_path = 'data/uploads/sample_pollution_data.csv'
    
    if os.path.exists(csv_path):
        size = os.path.getsize(csv_path)
        with open(csv_path, 'r') as f:
            lines = len(f.readlines())
        print(f"  ✅ sample_pollution_data.csv ({size} bytes, {lines} lignes)")
        return True
    else:
        print(f"  ❌ sample_pollution_data.csv manquant")
        return False


def main():
    """Exécute tous les tests"""
    print("\n" + "="*80)
    print("🧪 Tests du module Entreprises & Industries")
    print("="*80)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Validation extensions", test_allowed_file),
        ("Parsing CSV", test_csv_parsing),
        ("Méthode Mistral", test_mistral_method),
        ("Routes Flask", test_routes),
        ("Templates HTML", test_templates),
        ("CSV d'exemple", test_sample_csv),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Erreur lors du test '{name}': {e}")
            results.append((name, False))
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status:8} {name}")
    
    print(f"\n  Total: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n✅ Tous les tests réussis! Le module est prêt.")
        print("\n🚀 Prochaines étapes:")
        print("   1. pip install -r requirements.txt")
        print("   2. Configurer MISTRAL_API_KEY dans .env")
        print("   3. python web_server.py")
        print("   4. Aller à http://localhost:5000/entreprise")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) échoué(s). Vérifier les erreurs ci-dessus.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
