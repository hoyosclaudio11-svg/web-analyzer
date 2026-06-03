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

with open("E:/DelMonte/web-analyzer/check_pages.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR check_pages.php", io.BytesIO(data))
ftp.quit()

r = requests.get("https://riverplate-info.com.ar/check_pages.php", timeout=60)
print(r.text)

ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("check_pages.php")
ftp2.quit()
