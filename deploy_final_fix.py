import os
import ftplib, ssl, io, requests, time

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

def _clean_dir(ftp, path):
    lines = []
    try:
        ftp.retrlines("LIST", lambda l: lines.append(l))
    except:
        return
    for line in lines:
        parts = line.split()
        if len(parts) < 9:
            continue
        name = parts[-1]
        if name in ['.', '..']:
            continue
        full = path + "/" + name
        if line.startswith('d'):
            try:
                ftp.cwd(full)
                _clean_dir(ftp, full)
                ftp.cwd(path)
                ftp.rmd(full)
            except:
                pass
        else:
            try:
                ftp.delete(full)
            except:
                pass

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Subir fix script
with open("E:/DelMonte/web-analyzer/river_fix_final.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR river_fix_final.php", io.BytesIO(data))
print(f"Fix script subido: {len(data)} bytes")

# Limpiar todos los archivos de cache recursivamente
print("\nLimpiando cache WP Super Cache...")
cache_dirs = [
    "/public_html/wp-content/cache",
    "/public_html/wp-content/cache/supercache",
    "/public_html/wp-content/cache/meta"
]
for cd in cache_dirs:
    try:
        ftp.cwd(cd)
        # Limpiar recursivo
        _clean_dir(ftp, cd)
    except Exception as e:
        print(f"  {cd}: {e}")

ftp.quit()

# Ejecutar fix
print("\nEjecutando fix...")
r = requests.get("https://riverplate-info.com.ar/river_fix_final.php", timeout=60)
print(f"Status: {r.status_code}")
print(r.text)

# Borrar scripts
ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
for f in ["river_fix_final.php", "river_fix.php", "river_setup.php"]:
    try:
        ftp2.delete(f)
        print(f"Borrado: {f}")
    except:
        pass
ftp2.quit()

# Verificar con cache-busting
print("\n=== VERIFICACION (cache-bust) ===")
r2 = requests.get("https://riverplate-info.com.ar?v=" + str(time.time()), timeout=30)
print(f"Status: {r2.status_code}, Length: {len(r2.text)}")
import re
print(f"Nuestro CSS: {r2.text.count('wa-river-club-theme')}")
print(f"Hero 'Bienvenido': {r2.text.count('Bienvenido')}")
print(f"'Atlético': {r2.text.count('Atl')}")
print(f"'Más Grande': {r2.text.count('s Grande')}")
print(f"Shortcode sin renderizar: {raw_shortcode}")
raw_shortcode = r2.text.count('[latest_posts')
print(f"Shortcode sin renderizar: {raw_shortcode}")
# Check theme CSS
theme_css = re.findall(r'https?://[^"<>\s]*themes[^"<>\s]*\.css[^"<>\s]*', r2.text)
print(f"Theme CSS: {len(theme_css)}")
