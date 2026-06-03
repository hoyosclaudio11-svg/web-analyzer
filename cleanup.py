"""Limpiar archivos temporales del servidor."""
import os
import ftplib, ssl

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
USER = "a0110133"
PASS = os.getenv("FTP_PASS_WEBANALYZER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=15, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

ftp.cwd("/public_html/web")
for f in ["hello.php", "wp-auth-test.php", "test-auth.php"]:
    try:
        ftp.delete(f)
        print(f"  Eliminado: {f}")
    except Exception as e:
        print(f"  {f}: {e}")

ftp.quit()
print("\n>>> Limpieza completada <<<")
