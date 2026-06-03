"""Subir wa-river-club.php al server y borrar el viejo."""
import os
import ftplib, ssl, requests, io

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Subir el nuevo plugin
with open("E:/DelMonte/web-analyzer/wa-river-club.php", "rb") as f:
    data = f.read()

ftp.cwd("/public_html/wp-content/mu-plugins")
# Borrar el viejo si existe
try:
    ftp.delete("wa-river-theme.php")
    print("Viejo wa-river-theme.php eliminado")
except Exception as e:
    print(f"No se pudo borrar viejo (puede no existir): {e}")

ftp.storbinary("STOR wa-river-club.php", io.BytesIO(data))
print(f"Nuevo wa-river-club.php subido: {len(data)} bytes")

ftp.quit()

# Limpiar cache de WP Super Cache
print("\nLimpiando cache...")
try:
    r = requests.get("https://riverplate-info.com.ar", timeout=20)
    print(f"Homepage: {r.status_code}")
except Exception as e:
    print(f"Error HTTP: {e}")

print("\nLISTO. Visitar https://riverplate-info.com.ar para activar el setup.")
