"""
Agrega link "Inicio" a la navegacion de revista-espectaculos.
Inyecta JS via MU-plugin que agrega el link si no existe.
SOLO afecta revista-espectaculos, no webanalyzer ni otros dominios.
"""
import os
import ftplib, ssl, io

FTP_HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(FTP_HOST, timeout=15, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()

# Leer el MU-plugin actual
ftp.cwd("/public_html/wp-content/mu-plugins")
lines = []
ftp.retrlines("RETR wa-site-themes.php", lines.append)
content = "\n".join(lines)
print(f"MU-plugin actual: {len(content)} chars")

# Script JS para agregar "Inicio" (SOLO revista-espectaculos)
INICIO_JS = """
<script>
document.addEventListener('DOMContentLoaded', function() {
  if (window.location.hostname.indexOf('revista-espectaculos') === -1) return;
  var nav = document.querySelector('.wp-block-navigation, .wp-block-page-list, nav');
  if (nav) {
    var existing = nav.querySelector('a[href*="/web/"], a[href="/"], a[href="/inicio"]');
    if (!existing) {
      var li = document.createElement('li');
      li.className = 'wp-block-navigation-item wp-block-navigation-link';
      var a = document.createElement('a');
      a.href = '/';
      a.textContent = 'Inicio';
      a.className = 'wp-block-navigation-item__content';
      a.style.cssText = 'color:#aaa!important;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none';
      a.addEventListener('mouseenter', function(){ this.style.color='#fff'; this.style.background='rgba(233,30,99,0.15)'; });
      a.addEventListener('mouseleave', function(){ this.style.color='#aaa'; this.style.background='transparent'; });
      li.appendChild(a);
      var firstChild = nav.firstElementChild;
      if (firstChild && firstChild.tagName === 'UL') {
        firstChild.insertBefore(li, firstChild.firstElementChild);
      } else {
        nav.insertBefore(li, nav.firstElementChild);
      }
    }
  }
});
</script>
"""

# Insertar el JS en wa_espectaculos_css(), justo antes del cierre </style>
# Hay dos variantes de wa_espectaculos_css:
# 1. La version con .top-bar (revista-espectaculos real) - tiene "return;" adentro
# 2. La version fallback generica

# Encontramos el primer </style> dentro de wa_espectaculos_css
# Es el que esta antes de "return;"
marker = "</style><?php\n        return;"
if marker in content:
    content = content.replace(marker, "</style>" + INICIO_JS + "<?php\n        return;")
    print("JS Inicio agregado a wa_espectaculos_css (version revista-espectaculos)")
else:
    # Intentar con variaciones de whitespace
    import re
    pattern = r'</style>\s*<\?php\s*return;'
    if re.search(pattern, content):
        content = re.sub(pattern, "</style>" + INICIO_JS + "<?php\n        return;", content, count=1)
        print("JS Inicio agregado a wa_espectaculos_css (via regex)")
    else:
        print("ERROR: No se encontro marcador para espectaculos")
        idx = content.find("return;")
        if idx >= 0:
            print(f"  'return;' encontrado en pos {idx}: ...{content[idx-50:idx+50]}...")

# Para el fallback de espectaculos (sin top-bar, sin return)
# Buscamos el bloque <style id="wa-espectaculos-theme">
marker2 = 'id="wa-espectaculos-theme"'
idx2 = content.find(marker2)
if idx2 >= 0:
    idx_close = content.find("</style>", idx2)
    if idx_close >= 0:
        # Insertar JS justo despues del cierre </style>
        insert_pos = idx_close + 8  # len("</style>")
        content = content[:insert_pos] + INICIO_JS + content[insert_pos:]
        print("JS Inicio agregado a wa_espectaculos_css (version fallback)")

# Subir
bio = io.BytesIO(content.encode("utf-8"))
ftp.storbinary("STOR wa-site-themes.php", bio)
print(f"MU-plugin actualizado: {len(content)} chars")

# Verificar
ftp.cwd("/public_html/wp-content/mu-plugins")
lines2 = []
ftp.retrlines("RETR wa-site-themes.php", lines2.append)
ver = "\n".join(lines2)
print(f"  Contiene 'revista-espectaculos' en JS: {'revista-espectaculos' in ver}")
print(f"  Contiene 'Inicio' link: {'Inicio' in ver}")

ftp.quit()
print("\nListo. Visita http://revista-espectaculos.com.ar/ para verificar el menu Inicio.")
