"""Eliminar backups de mu-plugins que causan conflictos PHP."""
import os
import ftplib, ssl

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd('/public_html/web/wp-content/mu-plugins')

print("Archivos antes:")
for f in ftp.nlst():
    print(f"  {f}")

# Delete backup files
for f in list(ftp.nlst()):
    if 'backup' in f.lower():
        ftp.delete(f)
        print(f"ELIMINADO: {f}")

print("\nArchivos despues:")
for f in ftp.nlst():
    if f not in ('.', '..'):
        print(f"  {f}")

ftp.quit()
print("\nListo. El sitio deberia volver a funcionar.")
