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

with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(data))
print(f"Subido: {len(data)} bytes")
ftp.quit()

r = requests.get("https://riverplate-info.com.ar", timeout=30)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

styles = re.findall(r'https?://[^"<>\s]*themes[^"<>\s]*', r.text)
print(f"Theme CSS residuales: {len(styles)}")
for s in styles:
    parts = s.split('/')[-1].split('?')[0]
    print(f"  {parts}")

# Verificar estilos inline (nuestro CSS deberia estar)
our_css = r.text.count("wa-river-club-theme")
print(f"Nuestro CSS inline: {our_css}")
