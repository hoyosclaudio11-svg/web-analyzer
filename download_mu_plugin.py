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
ftp.cwd("/public_html/wp-content/mu-plugins")

lines = []
ftp.retrlines("RETR wa-river-club.php", lambda l: lines.append(l))
code = "\n".join(lines)
print(f"Tamano: {len(code)} chars, {len(lines)} lineas")
print("\n=== PRIMERAS 60 LINEAS ===")
for i, line in enumerate(lines[:60]):
    print(f"{i+1}: {line}")
print("\n=== ULTIMAS 10 LINEAS ===")
for i, line in enumerate(lines[-10:]):
    print(f"{len(lines)-9+i}: {line}")

ftp.quit()
