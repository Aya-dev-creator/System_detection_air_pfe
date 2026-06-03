import requests
import io

BASE = 'http://127.0.0.1:5000'
s = requests.Session()

print('=' * 60)
print('TEST 1: /entreprise sans login -> doit rediriger vers login')
r = s.get(BASE + '/entreprise', allow_redirects=False)
loc = r.headers.get('Location', '')
print(f'  Status: {r.status_code}  Location: {loc}')
assert r.status_code == 302 and 'login' in loc, 'ECHEC: acces public non bloque!'
print('  [OK] acces public bloque')

print()
print('TEST 2: POST /entreprise/upload sans login -> bloque aussi')
r = s.post(BASE + '/entreprise/upload', allow_redirects=False)
loc = r.headers.get('Location', '')
print(f'  Status: {r.status_code}  Location: {loc}')
assert r.status_code == 302 and 'login' in loc, 'ECHEC: POST public non bloque!'
print('  [OK] POST public bloque')

print()
print('TEST 3: Login entreprise avec credentials corrects')
r = s.post(
    BASE + '/entreprise/login',
    data={'username': 'admin', 'password': 'pfe2026'},
    allow_redirects=True
)
print(f'  Status final: {r.status_code}  URL: {r.url}')
assert r.status_code == 200 and 'entreprise' in r.url, 'ECHEC: login echoue!'
print('  [OK] Login OK, session etablie')

print()
print('TEST 4: /entreprise apres login -> page upload visible')
r = s.get(BASE + '/entreprise')
print(f'  Status: {r.status_code}')
has_csv = 'csv' in r.text.lower() or 'Analyse' in r.text
has_sidebar = 'AirWatch B2B' in r.text
print(f'  Contenu CSV present: {has_csv}')
print(f'  Sidebar industrielle: {has_sidebar}')
assert r.status_code == 200, 'ECHEC: page upload non accessible apres login!'
assert has_csv, 'ECHEC: contenu CSV absent!'
assert has_sidebar, 'ECHEC: sidebar B2B absente!'
print('  [OK] Page upload B2B correctement affichee avec template industriel')

print()
print('TEST 5: Upload CSV avec le fichier de test')
csv_path = r'c:\Users\PC\Desktop\pfe10\versel\data\test_capteurs_usine.csv'
with open(csv_path, 'rb') as f:
    csv_bytes = f.read()

files = {'file': ('test_capteurs_usine.csv', io.BytesIO(csv_bytes), 'text/csv')}
data = {'entity_name': 'Usine Test PFE', 'entity_type': 'Usine'}
r = s.post(BASE + '/entreprise/upload', files=files, data=data, allow_redirects=True)
print(f'  Status final: {r.status_code}  URL: {r.url}')
assert r.status_code == 200, 'ECHEC: upload retourne statut ' + str(r.status_code)
assert 'error' not in r.url.lower(), 'ECHEC: erreur dans URL: ' + r.url
print('  [OK] CSV uploade et parse sans erreur')
print('  Dashboard atteint: ' + str('dashboard' in r.url))

print()
print('TEST 6: Dashboard contient les donnees de pollution')
has_pollutants = any(p in r.text for p in ['PM2', 'PM10', 'CO2', 'NO2', 'SO2', 'Usine Test'])
print(f'  Donnees polluants affichees: {has_pollutants}')
assert has_pollutants, 'ECHEC: polluants absents du dashboard!'
print('  [OK] Polluants affiches dans le dashboard')

print()
print('=' * 60)
print('TOUS LES TESTS PASSES AVEC SUCCES!')
print('=' * 60)
