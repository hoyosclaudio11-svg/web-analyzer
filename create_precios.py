import os
import requests, base64, json

BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
_wp_user = os.getenv("WP_USER", "a0110133")
_wp_pass = os.getenv("WP_APP_PASSWORD", "")
auth = base64.b64encode(f"{_wp_user}:{_wp_pass}".encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

PAYLOAD = {
    'title': 'Precios',
    'slug': 'precios',
    'status': 'publish',
    'content': '<h2>Planes simples, sin vueltas</h2><p>Un solo pago. Sin suscripciones.</p>',
}

r = requests.post(f'{BASE}/pages', headers=headers, json=PAYLOAD)

print(f'Status: {r.status_code}')
print(f'Headers: {dict(r.headers)}')
print(f'Response: {r.text[:1000]}')
