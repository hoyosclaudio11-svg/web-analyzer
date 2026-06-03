"""Eliminar link roto /blog/ del footer via FTP al MU-plugin."""
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
print("Archivos en mu-plugins:")
files = ftp.nlst()
for f in files:
    print(f"  {f}")

# Buscar el MU-plugin principal
mu_file = None
for f in files:
    if f.endswith('.php') and ('web' in f.lower() or 'custom' in f.lower() or 'mu' in f.lower() or 'style' in f.lower() or 'analyzer' in f.lower()):
        mu_file = f
        break

if not mu_file:
    for f in files:
        if f.endswith('.php') and f not in ('index.php',):
            mu_file = f
            break

if mu_file:
    print(f"\nLeyendo: {mu_file}")
    # Leer archivo actual
    content_buf = io.BytesIO()
    ftp.retrbinary(f'RETR {mu_file}', content_buf.write)
    current = content_buf.getvalue().decode('utf-8', errors='replace')
    print(f"  Tamaño actual: {len(current)} bytes")

    # Agregar snippet para eliminar link /blog/ del footer
    redirect_snippet = """
/* ===== FIX: Eliminar link roto /blog/ del footer ===== */
/* Oculta cualquier link a /blog/ que haya quedado en footer o menu */
add_action('wp_footer', function() {
    echo '<script>
    document.addEventListener("DOMContentLoaded", function() {
        var links = document.querySelectorAll("a[href*=\"/blog/\"]");
        links.forEach(function(link) {
            link.style.display = "none";
        });
    });
    </script>';
}, 999);

/* Alternativa server-side: filtra wp_list_pages para no mostrar /blog/ */
add_filter('wp_list_pages_excludes', function($exclude) {
    $exclude[] = 31; /* ID de la pagina blog eliminada */
    return $exclude;
});
"""
    if redirect_snippet.strip() not in current:
        # Insertar antes del cierre PHP o al final
        if '?>' in current:
            pos = current.rfind('?>')
            new_content = current[:pos] + '\n' + redirect_snippet + '\n' + current[pos:]
        else:
            new_content = current + '\n' + redirect_snippet

        print(f"  Agregando snippet. Nuevo tamaño: {len(new_content)} bytes")

        # Subir backup
        backup_name = mu_file.replace('.php', '_backup.php')
        ftp.storbinary(f'STOR {backup_name}', io.BytesIO(current.encode('utf-8')))
        print(f"  Backup guardado: {backup_name}")

        # Subir nueva version
        ftp.storbinary(f'STOR {mu_file}', io.BytesIO(new_content.encode('utf-8')))
        print(f"  {mu_file} actualizado OK")
    else:
        print("  Snippet ya existe. No se modifica.")
else:
    print("\nNo se encontro MU-plugin. Creando uno nuevo...")
    mu_file = "wa-custom.php"
    content_buf = io.BytesIO()
    try:
        ftp.retrbinary(f'RETR {mu_file}', content_buf.write)
        current = content_buf.getvalue().decode('utf-8', errors='replace')
    except:
        current = '<?php\n/* Web Analyzer Custom MU Plugin */\n'

    redirect_snippet = """
/* ===== FIX: Eliminar link roto /blog/ del footer ===== */
add_action('wp_footer', function() {
    echo '<script>
    document.addEventListener("DOMContentLoaded", function() {
        var links = document.querySelectorAll("a[href*=\"/blog/\"]");
        links.forEach(function(link) {
            link.style.display = "none";
        });
    });
    </script>';
}, 999);
"""
    new_content = current.rstrip() + '\n' + redirect_snippet
    ftp.storbinary(f'STOR {mu_file}', io.BytesIO(new_content.encode('utf-8')))
    print(f"  MU-plugin creado: {mu_file}")

ftp.quit()
print("\nListo. El footer ya no muestra el link roto a /blog/.")
