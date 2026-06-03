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

with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(data))
print(f"Subido: {len(data)} bytes")
ftp.quit()

# Test
r = requests.get("https://riverplate-info.com.ar", timeout=30)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

# Contar stylesheets de tema
import re
styles = re.findall(r"<link[^>]*rel=['\"]stylesheet['\"][^>]*href=['\"]([^'\"]+)['\"][^>]*>", r.text)
theme_css = [s for s in styles if 'themes' in s or 'bootstrap' in s or 'default.css' in s or 'style.css' in s]
if theme_css:
    print(f"TEMA CSSs RESIDUALES ({len(theme_css)}):")
    for s in theme_css:
        print(f"  {s.split('/')[-1].split('?')[0]}")
else:
    print("NINGUN CSS de tema cargado! Limpio.")
