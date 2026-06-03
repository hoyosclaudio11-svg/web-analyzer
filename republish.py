"""Republicar post de prueba con featured image."""
import os
import requests, base64
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# 1. Generar imagen destacada para el post
print("=== Generando imagen ===")
img = Image.new("RGB", (1200, 630), "#0d1117")
draw = ImageDraw.Draw(img)

# Banner estilo Web Analyzer
draw.rectangle([0, 0, 1200, 8], fill="#1f6feb")
draw.rectangle([0, 622, 1200, 630], fill="#1f6feb")

# Texto grande
texts = [
    ("Yahoo, River y One Piece", 140, 48),
    ("los gigantes que fallan", 220, 44),
    ("en su propio juego", 290, 36),
]
for text, y, size in texts:
    try:
        font = ImageFont.truetype("segoeuib.ttf", size) if Path("C:/Windows/Fonts/segoeuib.ttf").exists() else ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (1200 - (bbox[2] - bbox[0])) / 2
    draw.text((x, y), text, fill="#ffffff", font=font)

# Scores
scores_data = [
    ("River", "3.2", 150, "#f85149"),
    ("Yahoo", "4.8", 520, "#f85149"),
    ("One Piece", "4.0", 890, "#f85149"),
]
for name, score, x, color in scores_data:
    # Circle
    cx, cy = x, 450
    r = 44
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 28)
    except:
        font_big = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), score, font=font_big)
    tx = cx - (bbox[2] - bbox[0]) / 2
    ty = cy - (bbox[3] - bbox[1]) / 2
    draw.text((tx, ty), score, fill="#000000", font=font_big)

img_path = Path("E:/DelMonte/web-analyzer/img-gigantes.png")
img.save(img_path)
print(f"  Imagen: {img_path}")

# 2. Subir imagen a WP
print("\n=== Subiendo imagen ===")
with open(img_path, "rb") as f:
    img_data = f.read()

img_headers = {
    'Authorization': f'Basic {auth}',
    'Content-Type': 'image/png',
    'Content-Disposition': 'attachment; filename="gigantes-fallan.png"'
}
r = requests.post(f'{BASE}/media', headers=img_headers, data=img_data)
if r.status_code == 201:
    img_id = r.json()['id']
    img_url = r.json()['source_url']
    print(f"  ID={img_id} URL={img_url}")
else:
    print(f"  ERROR: {r.status_code} {r.text[:200]}")
    img_id = None

# 3. Crear post
print("\n=== Publicando post ===")
post = """<!-- wp:paragraph -->
<p>Todos creen que los sitios mas grandes del mundo estan bien optimizados. <strong>No es verdad.</strong> Auditamos 3 sitios con millones de visitas diarias y los resultados sorprenden.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Los puntajes que NADIE esperaba</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Sitio</th><th>Puntaje</th><th>Problema principal</th></tr></thead><tbody><tr><td>cariverplate.com.ar</td><td style="color:#f85149;font-weight:700">3.2/10</td><td>Sin meta tags, sin lazy loading, sin accesibilidad</td></tr><tr><td>yahoo.com</td><td style="color:#f85149;font-weight:700">4.8/10</td><td>Scripts bloqueantes, formularios sin labels</td></tr><tr><td>one-piece.com</td><td style="color:#f85149;font-weight:700">4.0/10</td><td>Sin alt text, sin Open Graph, carga lenta</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading {"level":2} -->
<h2>Que significa esto para vos</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Si los sitios con equipos de cientos de personas y presupuestos millonarios tienen estos problemas... ¿que esta pasando en tu sitio?</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>La mayoria de los sitios web acumulan anos de codigo sin mantenimiento. Cada plugin, cada imagen nueva, cada cambio de diseno agrega peso y errores invisibles. <strong>Nadie los revisa.</strong></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>3 cosas que podes hacer hoy</h2>
<!-- /wp:heading -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Audita tu sitio gratis</strong> en 30 segundos con Web Analyzer</li>
<li><strong>Revisa los hallazgos</strong> — estan ordenados por gravedad</li>
<li><strong>Descarga las soluciones</strong> en un plugin listo para instalar</li>
</ol>
<!-- /wp:list -->

<!-- wp:html -->
<div class="wa-cta-box">
<h2>¿Tu sitio esta mejor que el de River?</h2>
<p style="color:#8b949e;margin-bottom:16px">Descubrilo gratis, sin registro, en 30 segundos.</p>
<a href="https://web-analyzer-1-l8uc.onrender.com/" class="wa-btn" target="_blank" rel="noopener">Analizar gratis ahora &#8594;</a>
</div>
<!-- /wp:html -->

<!-- wp:paragraph -->
<p style="color:#8b949e;font-size:12px;margin-top:24px">Los puntajes mostrados corresponden a auditorias realizadas con Web Analyzer. Los resultados pueden variar segun el momento y cambios en los sitios analizados.</p>
<!-- /wp:paragraph -->
"""

post_data = {
    "title": "Yahoo, River y One Piece: los gigantes que fallan en su propio juego",
    "content": post,
    "slug": "gigantes-fallan-auditoria",
    "status": "publish",
    "categories": [7],  # Auditorias
    "excerpt": "Auditamos 3 sitios con millones de visitas. Ninguno llega a 5/10. Descubri que esta fallando en tu sitio."
}
if img_id:
    post_data["featured_media"] = img_id

r = requests.post(f'{BASE}/posts', headers=headers, json=post_data)
if r.status_code == 201:
    j = r.json()
    print(f"  Publicado! {j['link']}")
    print(f"  Jetpack deberia compartirlo a Facebook en los proximos minutos.")
else:
    print(f"  ERROR: {r.status_code} {r.text[:300]}")

print("\n=== LISTO ===")
