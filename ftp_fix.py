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

# 1. Limpiar wp-config.php
ftp.cwd("public_html/web")
content_lines = []
ftp.retrlines("RETR wp-config.php", content_lines.append)
original = "\n".join(content_lines)

new_content = original.replace(
    "\n// Forzar application passwords en HTTP (sin SSL)\nadd_filter( 'wp_is_application_passwords_available', '__return_true' );\n",
    ""
)

bio = io.BytesIO(new_content.encode("utf-8"))
ftp.storbinary("STOR wp-config.php", bio)
print(">>> wp-config.php limpio <<<")

# 2. Crear mu-plugins - usar ruta absoluta desde raiz
ftp.cwd("/")  # volver a raiz
ftp.cwd("/public_html/web/wp-content")
print("CWD: " + ftp.pwd())

try:
    ftp.mkd("mu-plugins")
    print(">>> mu-plugins creado <<<")
except Exception as e:
    print(f"mu-plugins: {e}")

ftp.cwd("/public_html/web/wp-content/mu-plugins")
print("CWD: " + ftp.pwd())

mu_plugin = """<?php
/**
 * Plugin Name: Force Application Passwords
 * Description: Habilita aplicacion de contrasenas en HTTP
 */
add_filter('wp_is_application_passwords_available', '__return_true');
"""
import os

bio = io.BytesIO(mu_plugin.encode("utf-8"))
ftp.storbinary("STOR force-app-passwords.php", bio)
print(">>> MU-plugin subido <<<")

# Verificar
print("\n=== mu-plugins contents ===")
ftp.dir()

ftp.quit()
