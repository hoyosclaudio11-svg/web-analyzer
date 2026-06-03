import os
import requests, base64

user = 'a0110133'
pwd = os.getenv('WP_APP_PASSWORD', '')
auth = base64.b64encode(f'{user}:{pwd}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}'}
BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'

# 1. Ver tema activo
r = requests.get(f'{BASE}/themes', headers=headers, params={'status': 'active'})
print("=== TEMA ACTIVO ===")
for t in r.json():
    print(f"  {t['name']} - {t['stylesheet']} (v{t['version']})")

# 2. Ver temas instalados
r2 = requests.get(f'{BASE}/themes', headers=headers)
print("\n=== TEMAS INSTALADOS ===")
for t in r2.json():
    active = " [ACTIVO]" if t['status'] == 'active' else ""
    print(f"  {t['name']}{active}")

# 3. Ver info del sitio
r3 = requests.get(f'{BASE}/settings', headers=headers)
s = r3.json()
print(f"\n=== SITE INFO ===")
print(f"  title: {s.get('title')}")
print(f"  description: {s.get('description')}")
print(f"  url: {s.get('url')}")

# 4. Ver paginas existentes
r4 = requests.get(f'{BASE}/pages', headers=headers)
print(f"\n=== PAGINAS ({len(r4.json())}) ===")
for p in r4.json():
    print(f"  [{p['status']}] {p['title']['rendered']} - {p['slug']}")

# 5. Ver posts existentes
r5 = requests.get(f'{BASE}/posts', headers=headers)
print(f"\n=== POSTS ({len(r5.json())}) ===")
for p in r5.json():
    print(f"  [{p['status']}] {p['title']['rendered']}")
