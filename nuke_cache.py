"""Destruir todo el cache de WordPress."""
import os
import ftplib, ssl, os

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()

def delete_recursive(ftp, path):
    """Delete directory contents recursively."""
    try:
        ftp.cwd(path)
        items = list(ftp.nlst())
        for item in items:
            if item in ('.', '..'):
                continue
            full = f"{path}/{item}"
            try:
                ftp.delete(item)
                print(f"  DEL: {full}")
            except:
                try:
                    delete_recursive(ftp, full)
                    ftp.cwd(path)
                    ftp.rmd(item)
                    print(f"  RMDIR: {full}")
                except:
                    pass
        ftp.cwd('/')
    except Exception as e:
        print(f"  SKIP {path}: {e}")

# Nuke all cache directories
cache_roots = [
    '/public_html/web/wp-content/cache',
]

for root in cache_roots:
    print(f"\nLimpiando {root}...")
    try:
        ftp.cwd(root)
        for item in ftp.nlst():
            if item in ('.', '..'):
                continue
            try:
                ftp.delete(item)
                print(f"  DEL: {root}/{item}")
            except:
                pass
    except Exception as e:
        print(f"  {e}")

ftp.quit()
print("\nCache nukeado. El sitio ahora deberia verse fresco.")
