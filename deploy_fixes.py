import os
import ftplib, ssl, io, requests

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Subir MU-plugin corregido
with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    css_data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(css_data))
print(f"1. MU-plugin CSS corregido: {len(css_data)} bytes")

# Subir script de fix
with open("E:/DelMonte/web-analyzer/river_fix.php", "rb") as f:
    fix_data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR river_fix.php", io.BytesIO(fix_data))
print(f"2. Script fix: {len(fix_data)} bytes")
ftp.quit()

# Ejecutar fix
print("3. Ejecutando correcciones...")
r = requests.get("https://riverplate-info.com.ar/river_fix.php", timeout=60)
print(f"   Status: {r.status_code}")
print(r.text)

# Borrar fix
ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("river_fix.php")
ftp2.quit()
print("4. Script borrado")
