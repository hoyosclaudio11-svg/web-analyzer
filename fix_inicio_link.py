"""Corregir link de Inicio: /web/ -> / en el MU-plugin."""
import os
import ftplib, ssl, io

FTP_HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(FTP_HOST, timeout=15, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd("/public_html/wp-content/mu-plugins")

lines = []
ftp.retrlines("RETR wa-site-themes.php", lines.append)
content = "\n".join(lines)
print("Archivo actual: " + str(len(content)) + " chars")

old = "a.href = '/web/'"
new = "a.href = '/'"
print("Ocurrencias de old: " + str(content.count(old)))
if old in content:
    content = content.replace(old, new)
    print("Reemplazo hecho")
else:
    print("No encontrado, buscando a.href...")
    idx = content.find("a.href")
    if idx >= 0:
        print("  encontrado: " + content[idx:idx+50])

bio = io.BytesIO(content.encode("utf-8"))
ftp.storbinary("STOR wa-site-themes.php", bio)
print("Subido. Verificando...")

lines2 = []
ftp.retrlines("RETR wa-site-themes.php", lines2.append)
ver = "\n".join(lines2)
check = "a.href = '/'"
print("Contiene href correcto: " + str(check in ver))

ftp.quit()
print("Listo. Recarga http://revista-espectaculos.com.ar/")
