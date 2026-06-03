"""Agregar redirect de /blog/ a /precios/ en .htaccess."""
import os
import ftplib, ssl, io

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd('/public_html/web')

# Leer .htaccess actual
buf = io.BytesIO()
try:
    ftp.retrbinary('RETR .htaccess', buf.write)
    htaccess = buf.getvalue().decode('utf-8')
    print(".htaccess actual:")
    print(htaccess[:500])
except:
    htaccess = ""
    print("No existe .htaccess. Se creara uno nuevo.")

# Ver si ya tiene el redirect
REDIRECT_RULE = "Redirect 301 /web/blog /web/precios"
REDIRECT_RULE2 = "Redirect 301 /blog /precios"
REWRITE_BLOCK = """<IfModule mod_rewrite.c>
RewriteEngine On
RewriteRule ^web/blog/?$ /web/precios/ [R=301,L]
RewriteRule ^blog/?$ /precios/ [R=301,L]
</IfModule>"""

if "web/blog" not in htaccess:
    # Si existe el bloque BEGIN/END WordPress, agregar despues de RewriteEngine On
    if "RewriteEngine On" in htaccess:
        htaccess = htaccess.replace(
            "RewriteEngine On",
            "RewriteEngine On\n# Web Analyzer: redirect blog a precios\nRedirect 301 /web/blog /web/precios\n"
        )
        print("Redirect agregado al .htaccess existente")
    else:
        # Agregar al final
        htaccess = htaccess.rstrip() + "\n\n# Web Analyzer: redirect blog a precios\nRedirect 301 /blog /precios\n"
        print("Redirect agregado al final del .htaccess")

    # Backup
    try:
        ftp.storbinary('STOR .htaccess.backup', io.BytesIO((buf.getvalue() if buf else b'')))
        print("Backup guardado: .htaccess.backup")
    except:
        pass

    ftp.storbinary('STOR .htaccess', io.BytesIO(htaccess.encode('utf-8')))
    print(".htaccess actualizado OK")
else:
    print("Redirect ya existe en .htaccess")

ftp.quit()
print("\nListo. /web/blog/ redirige a /web/precios/")
