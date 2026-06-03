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

with open("E:/DelMonte/web-analyzer/check_pap.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR check_pap.php", io.BytesIO(data))
ftp.quit()

r = requests.get("https://riverplate-info.com.ar/check_pap.php", timeout=120)
with open("E:/DelMonte/web-analyzer/pap_output.txt", "w", encoding="utf-8") as f:
    f.write(r.text)
# Filter non-printable chars
print(r.text.encode("ascii", errors="replace").decode("ascii"))

ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("check_pap.php")
ftp2.quit()
