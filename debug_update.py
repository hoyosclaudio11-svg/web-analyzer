"""Debug: diagnosticar por que WP rechaza la actualizacion."""
import os
import requests, base64, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# 1. Verificar capacidades del usuario
print("=== USUARIO ===")
r = requests.get(f'{BASE}/users/me', headers=headers)
if r.status_code == 200:
    u = r.json()
    print(f"User: {u.get('name')} (ID={u.get('id')})")
    print(f"Roles: {u.get('roles')}")
    print(f"Capabilities keys: {list(u.get('capabilities', {}).keys())[:10]}")
else:
    print(f"Error: {r.status_code}")

# 2. Verificar si la pagina 10 existe y es editable
print("\n=== PAGINA 10 ===")
r = requests.get(f'{BASE}/pages/10', headers=headers, params={'context': 'edit'})
data = r.json()
print(f"Status: {r.status_code}")
print(f"Title: {data.get('title', {}).get('rendered', 'N/A')}")
print(f"Status: {data.get('status')}")
print(f"Template: {data.get('template')}")
# Verificar meta fields relevantes
meta = data.get('meta', {})
print(f"Meta keys: {list(meta.keys()) if meta else 'empty'}")

# 3. Probar con un campo simple primero (solo title)
print("\n=== ACTUALIZAR SOLO TITLE ===")
r = requests.post(f'{BASE}/pages/10', headers=headers, json={
    'title': 'TEST TITLE CHANGE'
})
print(f"POST status: {r.status_code}")
data2 = r.json()
print(f"Title after: {data2.get('title', {}).get('rendered', 'N/A')}")
print(f"Modified: {data2.get('modified')}")

# 4. Ver headers de respuesta
print("\n=== HEADERS DE RESPUESTA POST ===")
print(f"X-WP-Total: {r.headers.get('X-WP-Total', 'N/A')}")
for h in ['X-Robots-Tag', 'X-Content-Type-Options', 'Allow']:
    print(f"{h}: {r.headers.get(h, 'N/A')}")

# 5. Revisar si hay algo raro con el post
print("\n=== REVISION DE PAGINA ===")
r3 = requests.get(f'{BASE}/pages/10/revisions', headers=headers, params={'per_page': 5})
if r3.status_code == 200:
    revs = r3.json()
    print(f"Revisions: {len(revs)}")
    for rev in revs[:3]:
        print(f"  Rev {rev.get('id')}: {rev.get('date')} by {rev.get('author')}")
else:
    print(f"Revisions error: {r3.status_code}")
    # Try without auth
    r3b = requests.get(f'{BASE}/pages/10/revisions', params={'per_page': 5})
    print(f"  Without auth: {r3b.status_code}")
