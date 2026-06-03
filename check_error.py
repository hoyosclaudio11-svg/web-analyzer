"""Verificar error en server River — leer error_log."""
import os
import ftplib, ssl

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Buscar error_log
for path in ["/public_html/error_log", "/error_log", "/public_html/wp-content/error_log"]:
    try:
        lines = []
        ftp.retrlines(f"RETR {path}", lambda l: lines.append(l))
        print(f"=== {path} (ultimas 40 lineas) ===")
        for line in lines[-40:]:
            print(line)
    except Exception as e:
        print(f"Sin {path}: {e}")

# Ver que el MU-plugin esta bien
print("\n=== MU-PLUGINS ===")
ftp.cwd("/public_html/wp-content/mu-plugins")
files = []
ftp.retrlines("LIST", lambda l: files.append(l))
for f in files:
    print(f)

ftp.quit()
