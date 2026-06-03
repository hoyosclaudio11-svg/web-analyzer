"""
PASO 5 — Unificar Newsletter Duplicado en River Plate Info
Problema: Hay dos bloques de newsletter en la homepage:
  1. Bloque inline (section.newsletter) antes del footer
  2. Bloque inline adicional despues del footer (div style="background:linear-gradient...")
Ademas, el boton floating "Suscribite gratis" tambien esta duplicado.
Solucion: Via FTP, modificar el MU-plugin o tema para eliminar el bloque duplicado.
"""
import os, sys, re, io, ftplib, ssl
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

FTP_HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
FTP_USER = os.getenv("WP_USER_RIVER", "a0070978")
FTP_PASS = os.getenv("FTP_PASS_RIVER", "")
WP_URL = os.getenv("WP_URL_RIVER", "https://www.riverplate-info.com.ar").rstrip("/")
WP_USER = os.getenv("WP_USER_RIVER", "a0070978")
WP_PASS_WP = os.getenv("WP_APP_PASSWORD_RIVER", "")

print("=== PASO 5: Unificar Newsletter Duplicado ===")
print()

# 1. Analizar homepage para encontrar bloques duplicados
print("1. Analizando homepage para localizar duplicados...")
try:
    r = requests.get(WP_URL, timeout=30)
    html = r.text
    print(f"   Tamano HTML: {len(html)} chars")
    
    # Contar bloques de newsletter
    newsletter_sections = re.findall(r'<section class="newsletter"', html)
    newsletter_divs = re.findall(r'Recib[ií] las noticias en tu mail', html)
    floating_buttons = re.findall(r'floating-suscribe|Suscrib[ií]te gratis', html)
    
    print(f"   Secciones <section class='newsletter'>: {len(newsletter_sections)}")
    print(f"   Textos 'Recibi las noticias en tu mail': {len(newsletter_divs)}")
    print(f"   Botones floating 'Suscribite gratis': {len(floating_buttons)}")
    
    # Encontrar el bloque duplicado (el que esta fuera del section.newsletter)
    # Patron del bloque inline duplicado (despues del footer)
    inline_pattern = r'<div style="background:linear-gradient[^"]*padding:24px[^"]*border-radius:12px[^"]*border-left:4px solid #75aadb[^"]*>.*?</div>\s*</div>'
    inline_matches = re.findall(inline_pattern, html, re.DOTALL)
    print(f"   Bloques inline de newsletter: {len(inline_matches)}")
    
    # El bloque que esta DENTRO del section.newsletter es el principal
    # El bloque inline DESPUES del footer es el duplicado
    # El floating button tambien es duplicado del section.newsletter
    
except Exception as e:
    print(f"   ERROR: {e}")
    html = ""

# 2. Buscar donde esta el contenido duplicado
print("\n2. Localizando origen del duplicado...")
# El HTML de la homepage se genera desde:
# - El theme (riverplate-2026)
# - MU-plugin (wa-river-club.php o wa-river-theme.php)
# - Widgets de WordPress
# Buscamos en el MU-plugin ya que es el archivo custom mas probable

# 3. Conectar FTP y descargar MU-plugin
print("\n3. Conectando FTP para revisar MU-plugin...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    ftp = ftplib.FTP_TLS(FTP_HOST, timeout=30, context=ctx)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()
    print("   OK: Conectado")
except Exception as e:
    print(f"   ERROR FTP: {e}")
    sys.exit(1)

# Buscar archivos MU-plugin
print("\n4. Listando MU-plugins...")
try:
    ftp.cwd("/public_html/wp-content/mu-plugins")
    files = []
    ftp.retrlines("LIST", files.append)
    print("   Archivos encontrados:")
    for f in files:
        print(f"     {f}")
except Exception as e:
    print(f"   ERROR al listar MU-plugins: {e}")

# Descargar el MU-plugin principal
mu_plugin_content = ""
mu_plugin_name = "wa-river-theme.php"  # Nombre visto en download_river_theme.py
print(f"\n5. Descargando {mu_plugin_name}...")
try:
    buf = io.BytesIO()
    ftp.retrbinary(f"RETR {mu_plugin_name}", buf.write)
    mu_plugin_content = buf.getvalue().decode("utf-8", errors="replace")
    print(f"   OK: {len(mu_plugin_content)} caracteres")
except Exception as e:
    print(f"   No se encontro {mu_plugin_name}: {e}")
    # Intentar con otro nombre
    mu_plugin_name = "wa-river-club.php"
    try:
        buf = io.BytesIO()
        ftp.retrbinary(f"RETR {mu_plugin_name}", buf.write)
        mu_plugin_content = buf.getvalue().decode("utf-8", errors="replace")
        print(f"   OK con {mu_plugin_name}: {len(mu_plugin_content)} caracteres")
    except Exception as e2:
        print(f"   Tampoco {mu_plugin_name}: {e2}")

# 6. Buscar el bloque duplicado en el MU-plugin
if mu_plugin_content:
    print(f"\n6. Buscando bloques de newsletter en {mu_plugin_name}...")
    
    # Buscar "newsletter" en el codigo
    lines = mu_plugin_content.split("\n")
    for i, line in enumerate(lines):
        if "newsletter" in line.lower() or "suscri" in line.lower() or "recib[ií]" in line.lower():
            print(f"   Linea {i+1}: {line.strip()[:100]}")
    
    # Buscar el bloque inline duplicado
    if "linear-gradient" in mu_plugin_content and "75aadb" in mu_plugin_content:
        print("\n   ENCONTRADO: Bloque inline duplicado en MU-plugin")
        # Encontrar la seccion exacta
        match = re.search(
            r"(<div style=\"background:linear-gradient.*?Suscribite gratis.*?</a>)",
            mu_plugin_content,
            re.DOTALL,
        )
        if match:
            block = match.group(1)
            print(f"   Bloque encontrado ({len(block)} chars)")
            print(f"   Inicio: {block[:100]}...")
            print(f"   Fin: ...{block[-100:]}")
    
    # Buscar floating button duplicado
    if "floating-suscribe" in mu_plugin_content or "position:fixed;bottom" in mu_plugin_content:
        print("\n   ENCONTRADO: Floating button duplicado en MU-plugin")
        match = re.search(
            r"(<a [^>]*position:fixed;bottom[^>]*Suscrib[ií]te[^>]*>)",
            mu_plugin_content,
            re.DOTALL,
        )
        if match:
            print(f"   Floating button: {match.group(1)[:150]}...")

# 7. Tambien revisar el tema activo
print("\n7. Revisando tema activo...")
try:
    ftp.cwd("/public_html/wp-content/themes")
    themes = []
    ftp.retrlines("LIST", themes.append)
    for t in themes:
        if "river" in t.lower():
            print(f"   Tema encontrado: {t}")
except Exception as e:
    print(f"   Error: {e}")

ftp.quit()
print("\n=== PASO 5 - ANALISIS COMPLETADO ===")
print("NOTA: Se requiere editar el MU-plugin para eliminar bloques duplicados.")
print("Se procedera a hacerlo en la siguiente ejecucion.")
