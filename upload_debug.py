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

# Subir debug script
with open("E:/DelMonte/web-analyzer/check_setup.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR check_setup.php", io.BytesIO(data))
ftp.quit()

# Ejecutar
r = requests.get("https://riverplate-info.com.ar/check_setup.php", timeout=30)
print(f"Status: {r.status_code}")
print(r.text)

# Borrar el archivo
ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("check_setup.php")
ftp2.quit()
print("\n[Debug script borrado]")
