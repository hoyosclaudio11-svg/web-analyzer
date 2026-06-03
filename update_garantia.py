""
import os"Actualizar garantia de 7 a 30 dias en la pagina de Precios."""
import requests, base64

BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
_wp_user = os.getenv("WP_USER", "a0110133")
_wp_pass = os.getenv("WP_APP_PASSWORD", "")
auth = base64.b64encode(f"{_wp_user}:{_wp_pass}".encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

r = requests.get(f'{BASE}/pages/67?context=edit', headers=headers)
page = r.json()
content = page['content']['raw']

old = 'Garantia de 7 dias'
new = 'Garantia de 30 dias'
if old in content:
    content = content.replace(old, new)
else:
    print(f'No se encontro "{old}" en el contenido')
    exit(1)

payload = {'content': content}
r = requests.put(f'{BASE}/pages/67', headers=headers, json=payload)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    if new in data['content']['rendered']:
        print('OK: Garantia actualizada a 30 dias')
    else:
        print('WARN: Cambio no reflejado')
else:
    print(f'Error: {r.text[:300]}')
