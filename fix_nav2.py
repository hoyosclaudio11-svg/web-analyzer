"""Ocultar Blog del menu - enfoque CSS directo en wa-dark-theme.php (ya que es MU-plugin de CSS)."""
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

buf = io.BytesIO()
ftp.retrbinary('RETR wa-dark-theme.php', buf.write)
theme = buf.getvalue().decode('utf-8')

# Agregar CSS inline para ocultar el link de Blog en la navegacion
HIDE_BLOG_CSS = """
/* ===== OCULTAR link Blog del nav y footer (redirige a Precios) ===== */
add_action('wp_head', function() {
    echo '<style>
    /* Ocultar pagina Blog de la navegacion - solo mostrar Inicio y Precios */
    .wp-block-navigation a[href*="/blog/"],
    .wp-block-page-list a[href*="/blog/"],
    nav a[href*="/blog/"],
    .navigation a[href*="/blog/"],
    .menu a[href*="/blog/"],
    ul.wp-block-navigation a[href*="/blog/"],
    li a[href$="/web/blog/"],
    li a[href*="webanalyzer.com.ar/web/blog/"] {
        display: none !important;
    }
    </style>';
}, 1);
"""

if HIDE_BLOG_CSS.strip() not in theme:
    pos = theme.rfind('?>')
    new_theme = theme[:pos] + '\n' + HIDE_BLOG_CSS + '\n' + theme[pos:]
    ftp.storbinary('STOR wa-dark-theme.php', io.BytesIO(new_theme.encode('utf-8')))
    print("CSS hide de Blog agregado a wa-dark-theme.php")
else:
    print("CSS ya existe")

ftp.quit()
print("Listo.")
