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

# Subir MU-plugin
with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(data))
print(f"Subido: {len(data)} bytes")

# Limpiar cache WP Super Cache
print("Limpiando cache...")
ftp.cwd("/public_html/wp-content/cache")
try:
    files = []
    ftp.retrlines("LIST", lambda l: files.append(l))
    for f_line in files:
        parts = f_line.split()
        if len(parts) >= 9:
            fname = parts[-1]
            full = f"/public_html/wp-content/cache/{fname}"
            try:
                if fname.endswith('.html') or fname.endswith('.php'):
                    ftp.delete(fname)
                    print(f"  Borrado: {fname}")
            except:
                pass
except Exception as e:
    print(f"  Cache: {e}")

ftp.quit()

# Test
r = requests.get("https://riverplate-info.com.ar", timeout=30)
print(f"\nStatus: {r.status_code}, Length: {len(r.text)}")

# Debug comment
if "WA-RIVER" in r.text:
    print("DEBUG COMMENT: ENCONTRADO - MU-plugin carga")
else:
    print("DEBUG COMMENT: NO ENCONTRADO - MU-plugin NO carga!")

# Theme CSS
styles = re.findall(r'https?://[^"<>\s]*themes[^"<>\s]*\.css[^"<>\s]*', r.text)
print(f"Theme CSS residuales: {len(styles)}")
for s in styles:
    print(f"  {s.split('/')[-1].split('?')[0]}")

# Nuestro CSS
print(f"Nuestro CSS: {r.text.count('wa-river-club-theme')}")
