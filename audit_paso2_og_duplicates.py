"""
PASO 2 — Resolver OG Duplicados e Inconsistencias en River Plate Info
Problema: Jetpack Social y Yoast SEO generan etiquetas OG duplicadas.
         og:locale aparece como es_ES (Yoast) y es_AR (Jetpack).
Solucion: Configurar og:locale a es_AR via Yoast, desactivar OG de Jetpack.
"""
import os, sys, re
from pathlib import Path
from dotenv import load_dotenv
import requests

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

print("=== PASO 2: Resolver OG Duplicados ===")
print()

# 1. Verificar conexion
print("1. Verificando conexion...")
try:
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/users/me", auth=(WP_USER, WP_PASS), timeout=30)
    if r.status_code != 200:
        print(f"   ERROR: HTTP {r.status_code}")
        sys.exit(1)
    print(f"   OK: Conectado como {r.json().get('name')}")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# 2. Verificar estado actual de OG tags en homepage
print("\n2. Verificando OG tags actuales en homepage...")
try:
    r = requests.get(WP_URL, timeout=30)
    html = r.text
    og_tags = re.findall(r'<meta property="(og:[^"]*)"\s+content="([^"]*)"', html)
    og_tags += re.findall(r'<meta content="([^"]*)" property="(og:[^"]*)"', html)
    
    og_counts = {}
    for tag in og_tags:
        if isinstance(tag, tuple) and len(tag) == 2:
            prop = tag[0] if tag[0].startswith("og:") else tag[1]
            og_counts[prop] = og_counts.get(prop, 0) + 1
    
    print("   OG tags encontradas:")
    for prop, count in sorted(og_counts.items()):
        status = "  DUPLICADO!" if count > 1 else "  OK"
        print(f"     {prop}: {count}x{status}")
except Exception as e:
    print(f"   ERROR al obtener homepage: {e}")

# 3. Buscar configuracion de Yoast SEO via REST API
print("\n3. Buscando configuracion de Yoast SEO...")
# Yoast SEO almacena opciones en /wp-json/yoast/v1/options (si esta habilitado)
yoast_endpoints = [
    f"{WP_URL}/wp-json/yoast/v1/options",
    f"{WP_URL}/wp-json/yoast/v1/configuration",
]
for ep in yoast_endpoints:
    try:
        r = requests.get(ep, auth=(WP_USER, WP_PASS), timeout=15)
        if r.status_code == 200:
            print(f"   Endpoint encontrado: {ep}")
            data = r.json()
            # Buscar og_locale
            if isinstance(data, dict):
                for key in data:
                    if "locale" in key.lower() or "og" in key.lower():
                        print(f"     {key}: {data[key]}")
    except:
        pass

# 4. Actualizar configuracion de Yoast SEO para og:locale = es_AR
print("\n4. Configurando og:locale en Yoast SEO...")
# Intentar via endpoint de opciones de Yoast
try:
    r = requests.post(
        f"{WP_URL}/wp-json/yoast/v1/options",
        json={"og_locale": "es_AR"},
        auth=(WP_USER, WP_PASS),
        timeout=30,
    )
    if r.status_code in (200, 201):
        print("   OK: og:locale configurado a es_AR")
    else:
        print(f"   Endpoint Yoast options no disponible: HTTP {r.status_code}")
        print("   Intentando via option_name de WordPress...")
except Exception as e:
    print(f"   Endpoint Yoast no disponible: {e}")

# 5. Buscar y configurar la opcion de OG locale en wp_options via REST
print("\n5. Buscando opciones de Jetpack para desactivar OG...")
# Buscamos si podemos acceder a settings de Jetpack
try:
    r = requests.get(
        f"{WP_URL}/wp-json/jetpack/v4/settings",
        auth=(WP_USER, WP_PASS),
        timeout=15,
    )
    if r.status_code == 200:
        settings = r.json()
        print(f"   Settings de Jetpack encontrados ({len(settings)} keys)")
        # Buscar setting que controle OG
        for key in settings:
            if "og" in key.lower() or "social" in key.lower() or "open_graph" in key.lower():
                print(f"     {key}: {settings[key]}")
    else:
        print(f"   Jetpack settings no accesibles: HTTP {r.status_code}")
except Exception as e:
    print(f"   Error: {e}")

# 6. Intentar desactivar Open Graph de Jetpack
print("\n6. Desactivando Open Graph de Jetpack...")
jetpack_og_settings = {
    "sharedaddy-disabled": True,  # Desactiva social sharing
}
try:
    # Intentar via jetpack settings endpoint
    r = requests.post(
        f"{WP_URL}/wp-json/jetpack/v4/settings",
        json={"jetpack-social-og": False, "sharedaddy-disabled": True},
        auth=(WP_USER, WP_PASS),
        timeout=30,
    )
    if r.status_code in (200, 201):
        print("   OK: OG de Jetpack desactivado")
    else:
        print(f"   No se pudo via API: HTTP {r.status_code}")
        print("   Se requiere desactivar manualmente desde wp-admin > Jetpack > Social")
except Exception as e:
    print(f"   Error: {e}")

# 7. Verificar resultado
print("\n7. Verificando resultado final...")
try:
    r = requests.get(WP_URL, timeout=30)
    html = r.text
    og_tags = re.findall(r'<meta property="(og:[^"]*)"\s+content="([^"]*)"', html)
    og_tags += re.findall(r'<meta content="([^"]*)" property="(og:[^"]*)"', html)
    
    og_counts = {}
    locales_found = []
    for tag in og_tags:
        if isinstance(tag, tuple) and len(tag) == 2:
            prop = tag[0] if tag[0].startswith("og:") else tag[1]
            og_counts[prop] = og_counts.get(prop, 0) + 1
            if "locale" in prop:
                locales_found.append(tag)
    
    print("   OG tags despues del fix:")
    for prop, count in sorted(og_counts.items()):
        status = "  DUPLICADO!" if count > 1 else "  OK"
        print(f"     {prop}: {count}x{status}")
    
    if locales_found:
        print(f"   Locales encontrados: {locales_found}")
except Exception as e:
    print(f"   Error: {e}")

print("\n=== PASO 2 COMPLETADO ===")
print("NOTA: Si los duplicados persisten, se requiere desactivar")
print("Jetpack Social manualmente desde wp-admin > Jetpack.")
