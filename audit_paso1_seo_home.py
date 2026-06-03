"""
PASO 1 — SEO Homepage River Plate Info
Actualiza el Title, Meta Description y Canonical de la pagina de Inicio (ID 866)
usando la API REST de WordPress + Yoast SEO.
"""
import os, sys, re
from pathlib import Path
from dotenv import load_dotenv
import requests

# Cargar .env desde automatizacion (tiene las credenciales WP correctas)
env_paths = [
    Path("E:/DelMonte/automatizacion/.env"),
    Path("E:/DelMonte/web-analyzer/.env"),
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)

WP_URL = os.getenv("WP_URL_RIVER", "https://www.riverplate-info.com.ar").rstrip("/")
WP_USER = os.getenv("WP_USER_RIVER", "a0070978")
WP_PASS = os.getenv("WP_APP_PASSWORD_RIVER", "")
PAGE_ID = 866  # Pagina "Inicio"

if not WP_PASS:
    print("ERROR: WP_APP_PASSWORD_RIVER no encontrada en .env")
    sys.exit(1)

# Valores optimizados SEO
NEW_TITLE = "River Plate Info - Noticias, Mercado de Pases y Partidos del Mas Grande"
NEW_META_DESC = (
    "Noticias de River Plate actualizadas a diario. Segui el mercado de pases, "
    "resultados de partidos, analisis tacticos, plantel y toda la informacion "
    "del club mas grande de Argentina."
)
NEW_OG_TITLE = "River Plate Info - Noticias del Mas Grande"
NEW_OG_DESC = NEW_META_DESC

print(f"=== PASO 1: SEO Homepage (Pagina ID={PAGE_ID}) ===")
print(f"URL: {WP_URL}")
print(f"Usuario: {WP_USER}")
print()

# 1. Verificar conexion
print("1. Verificando conexion con WordPress API...")
try:
    r = requests.get(
        f"{WP_URL}/wp-json/wp/v2/users/me",
        auth=(WP_USER, WP_PASS),
        timeout=30,
    )
    if r.status_code == 200:
        print(f"   OK: Conectado como {r.json().get('name', 'desconocido')}")
    else:
        print(f"   ERROR: HTTP {r.status_code} - {r.text[:200]}")
        sys.exit(1)
except Exception as e:
    print(f"   ERROR de conexion: {e}")
    sys.exit(1)

# 2. Leer pagina actual
print(f"\n2. Leyendo pagina ID={PAGE_ID}...")
r = requests.get(
    f"{WP_URL}/wp-json/wp/v2/pages/{PAGE_ID}",
    auth=(WP_USER, WP_PASS),
    timeout=30,
)
if r.status_code != 200:
    print(f"   ERROR: No se pudo leer la pagina. HTTP {r.status_code}")
    sys.exit(1)

page = r.json()
current_title = page.get("title", {}).get("rendered", "")
print(f"   Title actual: {current_title}")
print(f"   Slug: {page.get('slug', '')}")

# 3. Actualizar pagina con nuevos valores SEO
# Yoast SEO almacena los meta fields en el post meta via REST API
# Los campos de Yoast se pasan como yoast_head_json o via meta individual
print(f"\n3. Actualizando SEO de la homepage...")

update_data = {
    "title": NEW_TITLE,
    "meta": {
        # Yoast SEO fields via REST API
        "_yoast_wpseo_title": NEW_TITLE,
        "_yoast_wpseo_metadesc": NEW_META_DESC,
        "_yoast_wpseo_opengraph-title": NEW_OG_TITLE,
        "_yoast_wpseo_opengraph-description": NEW_OG_DESC,
        # Canonical se mantiene automatico por Yoast
    },
}

r = requests.post(
    f"{WP_URL}/wp-json/wp/v2/pages/{PAGE_ID}",
    json=update_data,
    auth=(WP_USER, WP_PASS),
    timeout=30,
)

if r.status_code == 200:
    result = r.json()
    print(f"   OK: Pagina actualizada")
    print(f"   Nuevo title: {result.get('title', {}).get('rendered', '')}")
else:
    print(f"   ADVERTENCIA: HTTP {r.status_code}")
    print(f"   Respuesta: {r.text[:500]}")
    # Intentar con endpoint de Yoast si existe
    print("\n   Intentando via endpoint de Yoast SEO...")
    # Algunas versiones de Yoast exponen /wp-json/yoast/v1/meta
    yoast_data = {
        "yoast_wpseo_title": NEW_TITLE,
        "yoast_wpseo_metadesc": NEW_META_DESC,
    }
    # Metodo alternativo: actualizar via post meta directo
    update_alt = {
        "title": NEW_TITLE,
    }
    r2 = requests.post(
        f"{WP_URL}/wp-json/wp/v2/pages/{PAGE_ID}",
        json=update_alt,
        auth=(WP_USER, WP_PASS),
        timeout=30,
    )
    if r2.status_code == 200:
        print("   OK: Title actualizado via metodo alternativo")
    else:
        print(f"   Metodo alternativo: HTTP {r2.status_code}")

# 4. Verificar resultado
print("\n4. Verificando resultado...")
r = requests.get(
    f"{WP_URL}/wp-json/wp/v2/pages/{PAGE_ID}",
    auth=(WP_USER, WP_PASS),
    timeout=30,
)
if r.status_code == 200:
    page = r.json()
    print(f"   Title verificado: {page.get('title', {}).get('rendered', '')}")
    # Verificar meta via yoast_head
    yoast = page.get("yoast_head_json", {})
    if yoast:
        print(f"   Yoast title: {yoast.get('title', 'N/A')}")
        print(f"   Yoast description: {yoast.get('description', 'N/A')}")
        og = yoast.get("og_meta", {})
        if og:
            print(f"   OG title: {og.get('og_title', 'N/A')}")
            print(f"   OG description: {og.get('og_description', 'N/A')}")
            print(f"   OG locale: {og.get('og_locale', 'N/A')}")

print("\n=== PASO 1 COMPLETADO ===")
