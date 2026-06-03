import os
import requests, base64, json

BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
_wp_user = os.getenv("WP_USER", "a0110133")
_wp_pass = os.getenv("WP_APP_PASSWORD", "")
auth = base64.b64encode(f"{_wp_user}:{_wp_pass}".encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# Probar con HTTP sin redirect
session = requests.Session()
session.trust_env = False

PAYLOAD = {
    'title': 'Precios',
    'slug': 'precios',
    'status': 'publish',
    'content': '<h2>Planes</h2><p>Pagina de precios de Web Analyzer.</p>',
}

# Intento 1: POST sin redirect
print('=== Intento 1: POST (allow_redirects=False) ===')
r = session.post(f'{BASE}/pages', headers=headers, json=PAYLOAD, allow_redirects=False)
print(f'Status: {r.status_code}')
print(f'Location: {r.headers.get("Location", "N/A")}')
print(f'Response: {r.text[:500]}')

# Intento 2: Probar con HTTPS
print('\n=== Intento 2: POST HTTPS ===')
BASE2 = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
r = session.post(f'{BASE2}/pages', headers=headers, json=PAYLOAD, allow_redirects=False)
print(f'Status: {r.status_code}')
print(f'Location: {r.headers.get("Location", "N/A")}')
print(f'Response: {r.text[:500]}')

# Intento 3: Probar creando un post en vez de page
print('\n=== Intento 3: POST post ===')
r = session.post(f'{BASE}/posts', headers=headers, json={
    'title': 'Test Precios',
    'slug': 'test-precios',
    'status': 'draft',
    'content': 'Test',
}, allow_redirects=False)
print(f'Status: {r.status_code}')
print(f'Response: {r.text[:300]}')
