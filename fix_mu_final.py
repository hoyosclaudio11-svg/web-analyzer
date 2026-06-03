"""Verificar y corregir MU-plugins."""
import os
import ftplib, ssl, io

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, context=CONTEXT)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd('/public_html/web/wp-content/mu-plugins')

# Ver force-app-passwords.php actual y su backup
print("=== force-app-passwords.php ===")
buf = io.BytesIO()
ftp.retrbinary('RETR force-app-passwords.php', buf.write)
print(buf.getvalue().decode('utf-8')[:300])

# Restaurar backup si existe y es el original
print("\n=== force-app-passwords_backup.php ===")
buf2 = io.BytesIO()
try:
    ftp.retrbinary('RETR force-app-passwords_backup.php', buf2.write)
    backup = buf2.getvalue().decode('utf-8')
    print(backup[:300])
    # Restaurar original
    ftp.storbinary('STOR force-app-passwords.php', io.BytesIO(backup.encode('utf-8')))
    print("RESTAURADO a version original")
except:
    print("No backup disponible")

# Ahora leer wa-dark-theme.php y agregar el snippet ahi
print("\n=== wa-dark-theme.php ===")
buf3 = io.BytesIO()
ftp.retrbinary('RETR wa-dark-theme.php', buf3.write)
theme = buf3.getvalue().decode('utf-8')
print(f"Tamaño: {len(theme)} bytes")
print(theme[:200])

FOOTER_FIX = """
/* ===== FIX: Eliminar link roto /blog/ del footer ===== */
add_action('wp_footer', function() {
    echo '<script>
    document.addEventListener("DOMContentLoaded", function() {
        var links = document.querySelectorAll("a[href*=\"/blog/\"]");
        links.forEach(function(link) { link.style.display = "none"; });
    });
    </script>';
}, 999);
"""

if '/blog/' not in theme:
    # Guardar backup
    ftp.storbinary('STOR wa-dark-theme_backup.php', io.BytesIO(theme.encode('utf-8')))
    print("Backup de wa-dark-theme.php guardado")

    if '?>' in theme:
        pos = theme.rfind('?>')
        new_theme = theme[:pos] + FOOTER_FIX + '\n' + theme[pos:]
    else:
        new_theme = theme + '\n' + FOOTER_FIX

    ftp.storbinary('STOR wa-dark-theme.php', io.BytesIO(new_theme.encode('utf-8')))
    print("wa-dark-theme.php actualizado con el fix del footer")
else:
    print("Fix ya existe en wa-dark-theme.php")

ftp.quit()
print("\nListo.")
