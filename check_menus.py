"""Revisar menus de WordPress y agregar Inicio a revista-espectaculos."""
import os
import requests, base64, ftplib, ssl, io, os

WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

# 1. Listar menus disponibles
print("=== MENUS ===")
r = requests.get(f'{BASE}/menus', headers=headers)
if r.status_code == 200:
    menus = r.json()
    for m in menus:
        print(f"  Menu: {m.get('name')} (ID={m.get('id')}, slug={m.get('slug')})")
        print(f"  Locations: {m.get('locations', [])}")
else:
    print(f"Error menus: {r.status_code}")

# 2. Listar ubicaciones de menu
print("\n=== MENU LOCATIONS ===")
r2 = requests.get(f'{BASE}/menu-locations', headers=headers)
if r2.status_code == 200:
    locs = r2.json()
    for loc, menu_id in locs.items():
        print(f"  {loc}: menu_id={menu_id}")
else:
    print(f"Error locations: {r.status_code} (puede no estar soportado)")

# 3. Listar items de cada menu
print("\n=== ITEMS DE MENU ===")
r3 = requests.get(f'{BASE}/menu-items', headers=headers, params={'per_page': 50})
if r3.status_code == 200:
    items = r3.json()
    for item in items:
        print(f"  ID={item.get('id')}: '{item.get('title')}' -> {item.get('url')} (menu={item.get('menu')}, parent={item.get('parent')})")
else:
    print(f"Error items: {r3.status_code}")
    print(r3.text[:300])

# 4. Revisar paginas
print("\n=== PAGINAS ===")
r4 = requests.get(f'{BASE}/pages', headers=headers, params={'per_page': 20})
if r4.status_code == 200:
    pages = r4.json()
    for p in pages:
        print(f"  ID={p.get('id')}: '{p.get('title',{}).get('rendered','')}' slug={p.get('slug')} status={p.get('status')}")
