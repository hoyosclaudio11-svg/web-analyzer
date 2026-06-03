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

# 1. Subir CSS actualizado
print("1/3 Subiendo CSS...")
with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    css_data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(css_data))
print(f"   CSS: {len(css_data)} bytes")

# 2. Subir logo fix
print("2/3 Subiendo logo fix...")
with open("E:/DelMonte/web-analyzer/fix_logo_and_css.php", "rb") as f:
    fix_data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR fix_logo.php", io.BytesIO(fix_data))
ftp.quit()

# 3. Ejecutar y limpiar
print("3/3 Ejecutando...")
r = requests.get("https://riverplate-info.com.ar/fix_logo.php", timeout=60)
print(r.text)

ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("fix_logo.php")
ftp2.quit()

# 4. Verificar
print("=== VERIFICACION FINAL ===")
r2 = requests.get("https://riverplate-info.com.ar", timeout=30)
print(f"Status: {r2.status_code}, Length: {len(r2.text)}")
pat = r'https?://[^\"<>\s]*themes[^\"<>\s]*\.css'
theme_count = len(re.findall(pat, r2.text))
print(f"Theme CSS: {theme_count}")
print(f"Our CSS: {r2.text.count('wa-river-club-theme')}")

# Logo
logo_imgs = re.findall(r'custom-logo[^>]*src="([^"]+)"', r2.text)
if logo_imgs:
    print(f"Logo SRC: {logo_imgs[0]}")
else:
    logo_imgs2 = re.findall(r'src="[^"]*logo[^"]*\.(?:png|jpg)"', r2.text, re.IGNORECASE)
    print(f"Logo alternativo: {logo_imgs2}")
    # Check site-logo area
    site_logo = re.findall(r'site-logo[^<]*<img[^>]*src="([^"]+)"', r2.text)
    for sl in site_logo:
        print(f"  Site-logo img: {sl}")

# SportsPress
print(f"sp-template: {r2.text.count('sp-template')}")
print(f"sp-table-wrapper: {r2.text.count('sp-table-wrapper')}")

# Check for hidden elements
print(f"site-info (hidden): {r2.text.count('site-info')}")
