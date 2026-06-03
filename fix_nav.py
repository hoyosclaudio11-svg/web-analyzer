"""Ocultar pagina blog del menu de navegacion (pero mantenerla para el redirect del footer)."""
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
ftp.cwd('/public_html/web/wp-content/mu-plugins')

# Leer wa-dark-theme.php
buf = io.BytesIO()
ftp.retrbinary('RETR wa-dark-theme.php', buf.write)
theme = buf.getvalue().decode('utf-8')

# Remover el fix JS anterior
OLD_JS_FIX = """
/* ===== FIX: Eliminar link roto /blog/ del footer ===== */
add_action('wp_footer', function() {
    echo '<script>
    document.addEventListener("DOMContentLoaded", function() {
        var links = document.querySelectorAll("a[href*=\"/blog/\"]");
        links.forEach(function(link) { link.style.display = \"none\"; });
    });
    </script>';
}, 999);"""

# Nuevo fix: excluir pagina blog del menu via PHP filter (server-side, sin JS)
NEW_FIX = """
/* ===== FIX: Ocultar pagina Blog del menu de navegacion ===== */
/* Excluye la pagina blog (ID=70) de wp_list_pages y menus generados */
add_filter('wp_list_pages_excludes', function($exclude) {
    $exclude[] = 70;
    return $exclude;
});

/* Excluir de wp_nav_menu items via WP_Query */
add_filter('wp_nav_menu_objects', function($items) {
    foreach ($items as $key => $item) {
        if ($item->object_id == 70 || $item->url == '/web/blog/' || strpos($item->url, '/blog/') !== false) {
            unset($items[$key]);
        }
    }
    return $items;
}, 999);
"""

# Remover fix viejo si existe
if OLD_JS_FIX.strip() in theme:
    theme = theme.replace(OLD_JS_FIX, '')
    print("Fix JS viejo removido")

# Agregar nuevo fix
if NEW_FIX.strip() not in theme:
    if '?>' in theme:
        pos = theme.rfind('?>')
        new_theme = theme[:pos] + '\n' + NEW_FIX + '\n' + theme[pos:]
    else:
        new_theme = theme + '\n' + NEW_FIX

    ftp.storbinary('STOR wa-dark-theme.php', io.BytesIO(new_theme.encode('utf-8')))
    print("Fix de navegacion agregado a wa-dark-theme.php")
else:
    print("Fix ya existe")

ftp.quit()
print("\nListo. El menu solo mostrara Inicio y Precios. El footer redirige /blog/ a /precios/.")
