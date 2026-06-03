import os
import ftplib, ssl, io, requests, re

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Subir fix script
with open("E:/DelMonte/web-analyzer/river_fix_todo.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR river_fix_todo.php", io.BytesIO(data))
print(f"Fix subido: {len(data)} bytes")
ftp.quit()

# Ejecutar
print("Ejecutando...")
r = requests.get("https://riverplate-info.com.ar/river_fix_todo.php", timeout=90)
print(r.text)

# Borrar
ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("river_fix_todo.php")
ftp2.quit()
print("Script borrado")

# Verificar
print("\n=== VERIFICACION ===")
r2 = requests.get("https://riverplate-info.com.ar", timeout=30)
print(f"Status: {r2.status_code}, Length: {len(r2.text)}")
print(f"Our CSS: {r2.text.count('wa-river-club-theme')}")
pat = r'https?://[^\"<>\s]*themes[^\"<>\s]*\.css'
theme_count = len(re.findall(pat, r2.text))
print(f"Theme CSS: {theme_count}")
logo_imgs = re.findall(r'custom-logo[^>]*src="([^"]+)"', r2.text)
if logo_imgs:
    print(f"Logo en pagina: {logo_imgs[0]}")
else:
    print("Logo NO visible")
# SportsPress
print(f"sp-template: {r2.text.count('sp-template')}")
print(f"sp-player: {r2.text.count('sp-player')}")
