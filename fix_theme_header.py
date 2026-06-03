"""Bajar header.php del tema newstack, quitar CSS/JS hardcodeados, subir."""
import os
import ftplib, ssl, io

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Bajar header.php del tema newstack (tema hijo)
ftp.cwd("/public_html/wp-content/themes/newstack")
lines = []
ftp.retrlines("RETR header.php", lambda l: lines.append(l))
header_php = "\n".join(lines)
print(f"header.php newstack: {len(header_php)} chars, {len(lines)} lineas")

# Guardar backup local
with open("E:/DelMonte/web-analyzer/backup_header_newstack.php", "w", encoding="utf-8") as f:
    f.write(header_php)
print("Backup guardado")

# Guardar backup en servidor
ftp.storbinary("STOR header.php.bak20260514", io.BytesIO(header_php.encode()))
print("Backup servidor guardado")

# Mostrar el header para analizarlo
print("\n=== HEADER.PHP (newstack) ===")
for i, line in enumerate(lines):
    print(f"{i+1}: {line}")

ftp.quit()
