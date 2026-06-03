"""
PASO 3 y 4 — Seguridad .htaccess (River Plate Info)
Paso 3: Agregar cabeceras de seguridad (HSTS, X-Frame-Options, etc.)
Paso 4: Bloquear xmlrpc.php
Se conecta via FTP a a0070978.ferozo.com y modifica /public_html/.htaccess
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
FTP_USER = os.getenv("FTP_USER_RIVER", "a0070978")
FTP_PASS = os.getenv("FTP_PASS_RIVER", "")
HTACCESS_PATH = "/public_html/.htaccess"

print("=== PASOS 3-4: Seguridad .htaccess ===")
print(f"FTP Host: {FTP_HOST}")
print(f"FTP User: {FTP_USER}")
print()

if not FTP_PASS:
    print("ERROR: FTP_PASS_RIVER no encontrada")
    sys.exit(1)

# Bloques a inyectar
SECURITY_HEADERS = """
# === SEGURIDAD - Cabeceras HTTP (agregado por auditoria) ===
<IfModule mod_headers.c>
  Header set Strict-Transport-Security "max-age=31536000; includeSubDomains"
  Header set X-Frame-Options "SAMEORIGIN"
  Header set X-Content-Type-Options "nosniff"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  Header set Permissions-Policy "camera=(), microphone=(), geolocation=()"
</IfModule>
"""

XMLRPC_BLOCK = """
# === BLOQUEO XML-RPC (agregado por auditoria) ===
<Files xmlrpc.php>
  Require all denied
</Files>
"""

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

# 2. Leer .htaccess actual
print("\n2. Leyendo .htaccess actual...")
try:
    ftp.cwd(HTACCESS_PATH.rsplit("/", 1)[0])
    buf = io.BytesIO()
    ftp.retrbinary(f"RETR {HTACCESS_PATH.rsplit('/', 1)[1]}", buf.write)
    htaccess = buf.getvalue().decode("utf-8", errors="replace")
    print(f"   OK: {len(htaccess)} caracteres leidos")
    print(f"   Primeras 200 chars:")
    print(f"   {htaccess[:200]}")
except Exception as e:
    print(f"   ADVERTENCIA: No se pudo leer .htaccess ({e})")
    print("   Se creara uno nuevo.")
    htaccess = ""

# 3. Verificar si ya existen los bloques
print("\n3. Verificando bloques existentes...")
has_security = "Strict-Transport-Security" in htaccess
has_xmlrpc_block = "Require all denied" in htaccess and "xmlrpc" in htaccess.lower()

print(f"   Cabeceras de seguridad: {'YA EXISTE' if has_security else 'FALTA'}")
print(f"   Bloqueo xmlrpc: {'YA EXISTE' if has_xmlrpc_block else 'FALTA'}")

# 4. Backup
print("\n4. Creando backup .htaccess.backup...")
try:
    if htaccess:
        ftp.storbinary("STOR .htaccess.backup", io.BytesIO(htaccess.encode("utf-8")))
        print("   OK: Backup creado como .htaccess.backup")
except Exception as e:
    print(f"   ADVERTENCIA: No se pudo crear backup ({e})")

# 5. Inyectar bloques
modified = False

if not has_security:
    print("\n5a. Inyectando cabeceras de seguridad...")
    # Insertar al inicio del archivo, antes de cualquier bloque # BEGIN WordPress
    if "# BEGIN WordPress" in htaccess:
        htaccess = htaccess.replace(
            "# BEGIN WordPress",
            SECURITY_HEADERS + "\n# BEGIN WordPress",
        )
    else:
        htaccess = SECURITY_HEADERS + "\n" + htaccess
    modified = True
    print("   OK: Cabeceras de seguridad agregadas")
else:
    print("\n5a. Cabeceras de seguridad ya presentes, omitiendo...")

if not has_xmlrpc_block:
    print("\n5b. Inyectando bloqueo de xmlrpc.php...")
    if "# BEGIN WordPress" in htaccess:
        htaccess = htaccess.replace(
            "# BEGIN WordPress",
            XMLRPC_BLOCK + "\n# BEGIN WordPress",
        )
    else:
        htaccess += XMLRPC_BLOCK
    modified = True
    print("   OK: Bloqueo de xmlrpc.php agregado")
else:
    print("\n5b. Bloqueo de xmlrpc ya presente, omitiendo...")

# 6. Subir .htaccess modificado
if modified:
    print("\n6. Subiendo .htaccess modificado...")
    try:
        ftp.storbinary("STOR .htaccess", io.BytesIO(htaccess.encode("utf-8")))
        print("   OK: .htaccess actualizado")
    except Exception as e:
        print(f"   ERROR al subir: {e}")
        ftp.quit()
        sys.exit(1)
else:
    print("\n6. No se requieren cambios.")

# 7. Cerrar FTP
ftp.quit()
print("\n7. Conexion FTP cerrada.")

# 8. Verificar headers via HTTP
print("\n8. Verificando cabeceras HTTP...")
try:
    import requests
    r = requests.head("https://riverplate-info.com.ar", timeout=30, allow_redirects=True)
    headers = r.headers
    security_headers = [
        "Strict-Transport-Security",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "Permissions-Policy",
    ]
    for h in security_headers:
        val = headers.get(h, "NO PRESENTE")
        status = "OK" if val != "NO PRESENTE" else "FALTA"
        print(f"   {h}: {val} [{status}]")
except Exception as e:
    print(f"   No se pudo verificar via HTTP: {e}")

# 9. Verificar xmlrpc.php bloqueado
print("\n9. Verificando bloqueo de xmlrpc.php...")
try:
    import requests
    r = requests.post(
        "https://riverplate-info.com.ar/xmlrpc.php",
        data="<methodCall><methodName>system.listMethods</methodName></methodCall>",
        headers={"Content-Type": "text/xml"},
        timeout=30,
    )
    if r.status_code in (403, 401):
        print(f"   OK: xmlrpc.php bloqueado (HTTP {r.status_code})")
    elif r.status_code == 200:
        print("   ADVERTENCIA: xmlrpc.php aun accesible (HTTP 200)")
        print("   Puede requerir configuracion adicional en el panel de hosting")
    else:
        print(f"   HTTP {r.status_code}: {r.text[:100]}")
except Exception as e:
    print(f"   No se pudo verificar: {e}")

print("\n=== PASOS 3-4 COMPLETADOS ===")
