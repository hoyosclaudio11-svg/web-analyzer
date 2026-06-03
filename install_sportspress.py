"""Descargar SportsPress, subir zip + unzipper PHP al server de River, extraer via HTTP."""
import os
import ftplib
import ssl
import urllib.request
import io
import requests

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

SPORTSPRESS_URL = "https://downloads.wordpress.org/plugin/sportspress.latest-stable.zip"
SITE_URL = "https://riverplate-info.com.ar"

print("Descargando SportsPress...")
with urllib.request.urlopen(SPORTSPRESS_URL) as resp:
    zip_data = resp.read()
print(f"Descargado: {len(zip_data)} bytes")

# Conectar FTP
print("Conectando FTP...")
ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Subir el zip a plugins
print("Subiendo sportspress.zip...")
ftp.cwd("/public_html/wp-content/plugins")
ftp.storbinary("STOR sportspress.zip", io.BytesIO(zip_data))
print("ZIP subido.")

# Crear y subir script unzipper
unzipper_php = """<?php
$zip = new ZipArchive;
if ($zip->open(__DIR__ . '/sportspress.zip') === TRUE) {
    $zip->extractTo(__DIR__ . '/');
    $zip->close();
    echo "OK: extraido a " . __DIR__;
    unlink(__FILE__);
    unlink(__DIR__ . '/sportspress.zip');
} else {
    echo "ERROR: no se pudo abrir el zip";
}
"""

print("Subiendo unzipper.php...")
ftp.storbinary("STOR unzipper.php", io.BytesIO(unzipper_php.encode()))
ftp.quit()

# Ejecutar via HTTP
print("Ejecutando unzipper via HTTP...")
try:
    r = requests.get(f"{SITE_URL}/wp-content/plugins/unzipper.php", timeout=30)
    print(f"Respuesta: {r.status_code} - {r.text[:200]}")
except Exception as e:
    print(f"Error HTTP: {e}")
    print("Puede que necesite HTTPS o el dominio no resuelva bien")

print("\nSportsPress instalado. Verificar en wp-admin > Plugins")
