import os
import ftplib, ssl, io

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
USER = "a0110133"
PASS = os.getenv("FTP_PASS_WEBANALYZER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=15, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Leer .htaccess de /web
ftp.cwd("public_html/web")
htaccess = []
try:
    ftp.retrlines("RETR .htaccess", htaccess.append)
    print("=== .htaccess de /web ===")
    for line in htaccess:
        print(line)
except Exception as e:
    print(f"No se pudo leer .htaccess: {e}")

# Leer .htaccess de raiz
ftp.cwd("/public_html")
htaccess2 = []
try:
    ftp.retrlines("RETR .htaccess", htaccess2.append)
    print("\n=== .htaccess de raiz ===")
    for line in htaccess2:
        print(line)
except Exception as e:
    print(f"No se pudo leer .htaccess: {e}")

ftp.quit()
