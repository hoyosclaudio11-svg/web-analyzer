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

with open("E:/DelMonte/web-analyzer/fix_plantilla.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html")
ftp.storbinary("STOR fix_plantilla.php", io.BytesIO(data))
ftp.quit()

r = requests.get("https://riverplate-info.com.ar/fix_plantilla.php", timeout=120)
with open("E:/DelMonte/web-analyzer/plantilla_output.txt", "w", encoding="utf-8") as f:
    f.write(r.text)
# Print first 3000 chars
output = r.text
print(output[:4000] if len(output) > 4000 else output)

ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()
ftp2.cwd("/public_html")
ftp2.delete("fix_plantilla.php")
ftp2.quit()
print("\nDone")
