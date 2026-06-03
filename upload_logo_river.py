"""Subir logo a WordPress River Plate y registrarlo."""
import os
import ftplib, ssl
from io import BytesIO

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=15, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Subir logo a uploads
with open("C:/Users/chito/Downloads/IMG_4336.png", "rb") as f:
    logo_data = f.read()

# Crear directorio para el logo
ftp.cwd("/public_html/wp-content/uploads")
# Crear subdirectorio para el logo
try:
    ftp.cwd("logos")
except:
    ftp.mkd("logos")
    ftp.cwd("logos")

ftp.storbinary("STOR river-logo.png", BytesIO(logo_data))
print(f"Logo subido: {len(logo_data)} bytes")

ftp.quit()
print("LISTO")
