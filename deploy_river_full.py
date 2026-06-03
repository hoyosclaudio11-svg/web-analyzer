"""Subir MU-plugin CSS + script setup, ejecutar setup, borrar script."""
import os
import ftplib, ssl, io, requests

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

print("1/4 Conectando FTP...")
ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Subir MU-plugin CSS
print("2/4 Subiendo MU-plugin CSS...")
with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    css_data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(css_data))
print(f"   MU-plugin: {len(css_data)} bytes")

# Subir setup script
print("3/4 Subiendo script de setup...")
with open("E:/DelMonte/web-analyzer/river_setup.php", "rb") as f:
    setup_data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR river_setup.php", io.BytesIO(setup_data))
print(f"   Setup: {len(setup_data)} bytes")
ftp.quit()

# Ejecutar setup
print("4/4 Ejecutando setup...")
r = requests.get("https://riverplate-info.com.ar/river_setup.php", timeout=60)
print(f"   Status: {r.status_code}")
print("---")
print(r.text)
print("---")

# Borrar setup script
print("\nBorrando script de setup...")
ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("river_setup.php")
ftp2.quit()
print("Script borrado.")

# Verificar frontend
print("\n=== VERIFICANDO FRONTEND ===")
r2 = requests.get("https://riverplate-info.com.ar", timeout=30)
print(f"Status: {r2.status_code}")
print(f"Length: {len(r2.text)}")
for term in ["Inicio", "Plantilla", "Calendario", "Noticias", "Tienda", "Contacto", "wa-river-club-theme", "EL MAS GRANDE"]:
    count = r2.text.count(term)
    print(f"  '{term}': {count}")
