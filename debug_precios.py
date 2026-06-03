import os
import requests, base64, json

BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
_wp_user = os.getenv("WP_USER", "a0110133")
_wp_pass = os.getenv("WP_APP_PASSWORD", "")
auth = base64.b64encode(f"{_wp_user}:{_wp_pass}".encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# Revisar si ya existe pagina con slug precios
r = requests.get(f'{BASE}/pages?slug=precios', headers=headers)
print('Existing precios:', r.status_code)
print(r.text[:500])

# Crear pagina simple primero
payload = {
    'title': 'Precios',
    'slug': 'precios',
    'content': '<h2>Planes</h2><p>Test</p>',
    'status': 'publish',
}
r = requests.post(f'{BASE}/pages', headers=headers, json=payload)
print(f'\nCreate status: {r.status_code}')
print(f'Response type: {type(r.json())}')
data = r.json()
if isinstance(data, list):
    print(f'List length: {len(data)}')
    for item in data:
        print(f'  {json.dumps(item, ensure_ascii=False)[:200]}')
else:
    print(f'  ID={data.get("id")} slug={data.get("slug")}')
    print(f'  link={data.get("link")}')
