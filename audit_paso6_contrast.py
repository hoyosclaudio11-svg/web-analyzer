"""
PASO 6 — Ajustar Contraste/Accesibilidad CSS en River Plate Info
Problema: Texto secundario #888 sobre fondo #1e1e1e no cumple WCAG AA (min 4.5:1).
Solucion: Subir el color de texto secundario a #aaa o #bbb para cumplir contraste.
Se modifica el MU-plugin CSS o el tema via FTP.
"""
import os, sys, re, io, ftplib, ssl
from pathlib import Path
from dotenv import load_dotenv

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

print("=== PASO 6: Ajustar Contraste/Accesibilidad CSS ===")
print()

# 1. Conectar FTP
print("1. Conectando FTP...")
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    ftp = ftplib.FTP_TLS(FTP_HOST, timeout=30, context=ctx)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()
    print("   OK: Conectado")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# 2. Buscar CSS con colores de contraste problematicos
print("\n2. Buscando colores de contraste problematicos en CSS...")

# Colores a buscar y reemplazar
CONTRAST_FIXES = {
    # color: #888 sobre fondo oscuro -> subir a #aaa
    "color:#888": "color:#aaa",
    "color: #888": "color: #aaa",
    "color:#888888": "color:#aaaaaa",
    "color: #888888": "color: #aaaaaa",
    # Tambien buscar en variables CSS
    "--gray:#888": "--gray:#aaa",
    "--gray: #888": "--gray: #aaa",
}

# Revisar MU-plugin
mu_plugin_name = "wa-river-theme.php"
mu_plugin_content = ""

try:
    ftp.cwd("/public_html/wp-content/mu-plugins")
    buf = io.BytesIO()
    ftp.retrbinary(f"RETR {mu_plugin_name}", buf.write)
    mu_plugin_content = buf.getvalue().decode("utf-8", errors="replace")
    print(f"   MU-plugin leido: {len(mu_plugin_content)} chars")
except:
    mu_plugin_name = "wa-river-club.php"
    try:
        buf = io.BytesIO()
        ftp.retrbinary(f"RETR {mu_plugin_name}", buf.write)
        mu_plugin_content = buf.getvalue().decode("utf-8", errors="replace")
        print(f"   MU-plugin alternativo leido: {len(mu_plugin_content)} chars")
    except Exception as e:
        print(f"   No se pudo leer MU-plugin: {e}")

# 3. Buscar y reemplazar colores problematicos
if mu_plugin_content:
    print(f"\n3. Buscando colores problematicos en {mu_plugin_name}...")
    
    changes_made = []
    modified_content = mu_plugin_content
    
    for old, new in CONTRAST_FIXES.items():
        count = modified_content.count(old)
        if count > 0:
            print(f"   Encontrado '{old}' -> '{new}': {count} veces")
            modified_content = modified_content.replace(old, new)
            changes_made.append((old, new, count))
    
    if changes_made:
        print(f"\n4. Aplicando {len(changes_made)} correcciones de contraste...")
        
        # Backup
        try:
            ftp.storbinary(f"STOR {mu_plugin_name}.backup", io.BytesIO(mu_plugin_content.encode("utf-8")))
            print(f"   Backup: {mu_plugin_name}.backup")
        except Exception as e:
            print(f"   ADVERTENCIA: No se pudo crear backup ({e})")
        
        # Subir version corregida
        try:
            ftp.storbinary(f"STOR {mu_plugin_name}", io.BytesIO(modified_content.encode("utf-8")))
            print("   OK: MU-plugin actualizado con correcciones de contraste")
            for old, new, count in changes_made:
                print(f"     - '{old}' -> '{new}' ({count}x)")
        except Exception as e:
            print(f"   ERROR al subir: {e}")
    else:
        print("   No se encontraron colores problematicos en el MU-plugin")
        print("   Buscando en archivos CSS del tema...")

# 4. Revisar tema activo
print("\n5. Revisando tema activo...")
try:
    ftp.cwd("/public_html/wp-content/themes")
    themes = []
    ftp.retrlines("LIST", themes.append)
    
    active_theme = None
    for t in themes:
        if "river" in t.lower() and not t.startswith("d"):
            parts = t.split()
            if len(parts) >= 9:
                active_theme = parts[-1]
                print(f"   Tema encontrado: {active_theme}")
    
    if active_theme:
        # Buscar main.css del tema
        css_path = f"/public_html/wp-content/themes/{active_theme}/assets/css/main.css"
        try:
            buf = io.BytesIO()
            ftp.retrbinary(f"RETR {css_path}", buf.write)
            css_content = buf.getvalue().decode("utf-8", errors="replace")
            print(f"   CSS leido: {len(css_content)} chars")
            
            # Buscar colores problematicos
            for old, new in CONTRAST_FIXES.items():
                count = css_content.count(old)
                if count > 0:
                    print(f"   Encontrado '{old}' en CSS: {count} veces")
        except Exception as e:
            print(f"   No se pudo leer CSS del tema: {e}")
except Exception as e:
    print(f"   Error: {e}")

ftp.quit()
print("\n=== PASO 6 COMPLETADO ===")
print("NOTA: Los cambios de contraste se aplican al MU-plugin que inyecta CSS.")
print("Si el problema persiste, se puede agregar CSS adicional via Customizer.")
