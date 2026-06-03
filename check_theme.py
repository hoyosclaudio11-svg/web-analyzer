"""Revisar MU-plugin y tema para entender la navegacion."""
import os
import requests, ftplib, ssl, io, os, sys

FTP_HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(FTP_HOST, timeout=15, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()

# 1. Leer wa-site-themes.php (MU-plugin)
print("=== MU-PLUGIN: wa-site-themes.php ===")
ftp.cwd("/public_html/wp-content/mu-plugins")
lines = []
ftp.retrlines("RETR wa-site-themes.php", lines.append)
content = "\n".join(lines)
print(f"Tamaño: {len(content)} chars")
# Buscar navigacion/menu
for keyword in ['nav', 'menu', 'header', 'navbar', 'inicio', 'home', 'navigation']:
    count = content.lower().count(keyword)
    if count > 0:
        print(f"  '{keyword}': {count} ocurrencias")
print("\n---CONTENIDO COMPLETO---")
print(content)

ftp.quit()
