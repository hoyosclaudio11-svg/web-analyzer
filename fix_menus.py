"""Revisar y agregar menu Inicio a revista-espectaculos."""
import os
import requests, ftplib, ssl, io, os
import urllib3
urllib3.disable_warnings()

FTP_HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")
BRIDGE_URL = "https://webanalyzer.com.ar/web/wa_bridge.php"
TOKEN = os.getenv("WA_BRIDGE_TOKEN", "")

def call_bridge(action, **extra):
    data = {'token': TOKEN, 'action': action}
    data.update(extra)
    r = requests.post(BRIDGE_URL, data=data, verify=False, timeout=15)
    return r.text

# Subir bridge
print("=== Subiendo bridge ===")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ftp = ftplib.FTP_TLS(FTP_HOST, timeout=15, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd("/public_html/web")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wa_bridge.php'), 'rb') as f:
    bio = io.BytesIO(f.read())
ftp.storbinary("STOR wa_bridge.php", bio)

# 1. Listar theme locations
print("\n=== MENU LOCATIONS ===")
resp = call_bridge('list_locations')
print(resp[:1000])

# 2. Listar menus
print("\n=== MENUS ===")
resp = call_bridge('list_menus')
print(resp)

import json
menus = json.loads(resp)
for m in menus:
    print(f"\n--- Menu: {m['name']} (ID={m['id']}) ---")
    print(f"    Locations: {m['locations']}")

    # Listar items
    resp2 = call_bridge('list_items', menu_id=m['id'])
    try:
        items = json.loads(resp2)
        for item in items:
            parent_str = f" (sub de {item['parent']})" if item['parent'] else ""
            print(f"    [{item['order']}] {item['title']} -> {item['url']}{parent_str}")
    except:
        print(f"    Error parseando items: {resp2[:300]}")

# 3. Ver si hay una pagina "Inicio" para agregar
# Buscar pagina de inicio
print("\n=== BUSCANDO PAGINA INICIO ===")
# La pagina ID=10 es "Inicio" en webanalyzer.com.ar/web/
# Para revista-espectaculos, la home es la misma instalacion WP

# Eliminar bridge
ftp.delete("wa_bridge.php")
ftp.quit()
print("\nBridge eliminado.")
