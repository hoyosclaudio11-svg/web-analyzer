"""
Verificar conexion despues de reiniciar router.
Ejecutar: python verificar_conexion.py
"""
import requests
import socket

print("=" * 50)
print("  VERIFICADOR DE CONEXION - River Plate Info")
print("=" * 50)
print()

# 1. Verificar IP actual
print("1. Tu IP publica:")
try:
    r = requests.get("https://api.ipify.org", timeout=10)
    ip = r.text.strip()
    print(f"   {ip}")
    if ip == "190.31.86.254":
        print("   ADVERTENCIA: Es la misma IP bloqueada!")
        print("   Reinicia el router para obtener una nueva IP.")
    else:
        print("   OK: IP diferente, el bloqueo ya no aplica!")
except Exception as e:
    print(f"   Error: {e}")

print()

# 2. Verificar conexion con riverplate-info.com.ar
print("2. Conectando con riverplate-info.com.ar...")
try:
    r = requests.get("https://riverplate-info.com.ar", timeout=15)
    print(f"   HTTP {r.status_code} - {len(r.text)} caracteres")
    if r.status_code == 200:
        print("   OK: Sitio accesible!")
except Exception as e:
    print(f"   ERROR: {e}")

print()

# 3. Verificar FTP
print("3. Verificando FTP (a0070978.ferozo.com)...")
import ftplib, ssl
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path("E:/DelMonte/automatizacion/.env"))
FTP_PASS = os.getenv("FTP_PASS_RIVER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
try:
    ftp = ftplib.FTP_TLS("a0070978.ferozo.com", timeout=15, context=ctx)
    ftp.login("a0070978", FTP_PASS)
    ftp.prot_p()
    print("   OK: FTP conectado!")
    ftp.quit()
except Exception as e:
    print(f"   ERROR: {e}")

print()

# 4. Verificar WordPress API
print("4. Verificando WordPress REST API...")
WP_USER = os.getenv("WP_USER_RIVER", "a0070978")
WP_PASS = os.getenv("WP_APP_PASSWORD_RIVER", "")
try:
    r = requests.get(
        "https://riverplate-info.com.ar/wp-json/wp/v2/users/me",
        auth=(WP_USER, WP_PASS),
        timeout=15,
    )
    if r.status_code == 200:
        user = r.json().get("name", "")
        print(f"   OK: Conectado como {user}")
    else:
        print(f"   HTTP {r.status_code}")
except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 50)
print("Si todo esta OK, ejecuta:")
print("  python E:\\DelMonte\\web-analyzer\\audit_master.py")
print("=" * 50)
