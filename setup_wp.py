"""
Agregar carrusel visual tipo tarjetas deslizantes con imagenes y texto.
"""
import os
import ftplib, ssl, io, requests, base64, json
from pathlib import Path

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")
WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"

CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# =====================================================================
# 1. Actualizar MU-plugin con CSS para carrusel
# =====================================================================
print("=== Actualizando CSS con carrusel ===")

CAROUSEL_CSS = r'''
/* ===== CARRUSEL DE EJEMPLOS ===== */
.wa-carousel-wrapper {
  max-width: 100%;
  margin: 32px 0;
  position: relative;
}

.wa-carousel-title {
  font-size: 13px !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #8b949e;
  text-align: center;
  margin-bottom: 4px;
}

.wa-carousel-subtitle {
  font-size: 12px;
  color: #6e7681;
  text-align: center;
  margin-bottom: 24px;
}

.wa-carousel {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  gap: 16px;
  padding: 8px 4px 20px 4px;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #30363d #0d1117;
}

.wa-carousel::-webkit-scrollbar {
  height: 6px;
}

.wa-carousel::-webkit-scrollbar-track {
  background: #0d1117;
  border-radius: 3px;
}

.wa-carousel::-webkit-scrollbar-thumb {
  background: #30363d;
  border-radius: 3px;
}

.wa-carousel::-webkit-scrollbar-thumb:hover {
  background: #484f58;
}

.wa-carousel-card {
  flex: 0 0 280px;
  scroll-snap-align: start;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.2s, transform 0.2s;
  cursor: pointer;
  text-decoration: none !important;
  display: block;
  min-height: 340px;
  position: relative;
}

.wa-carousel-card:hover {
  border-color: #58a6ff;
  transform: translateY(-2px);
}

.wa-carousel-card-img {
  width: 100%;
  height: 160px;
  background: #21262d;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.wa-carousel-card-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.wa-carousel-score-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  color: #000;
  z-index: 2;
}

.wa-carousel-score-badge.bad { background: #f85149; }
.wa-carousel-score-badge.ok { background: #d29922; }
.wa-carousel-score-badge.good { background: #3fb950; }

.wa-carousel-card-body {
  padding: 16px;
}

.wa-carousel-card-domain {
  font-family: monospace;
  font-size: 13px;
  color: #58a6ff;
  font-weight: 600;
  margin-bottom: 4px;
}

.wa-carousel-card-label {
  font-size: 11px;
  color: #6e7681;
  margin-bottom: 10px;
}

.wa-carousel-card-scores {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.wa-carousel-card-scores span {
  font-size: 10px;
  color: #8b949e;
  display: flex;
  align-items: center;
  gap: 4px;
}

.wa-mini-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.wa-mini-dot.bad { background: #f85149; }
.wa-mini-dot.ok { background: #d29922; }
.wa-mini-dot.good { background: #3fb950; }

.wa-carousel-card-cta {
  color: #58a6ff;
  font-size: 11px;
  font-weight: 600;
  margin-top: 4px;
}

/* ===== ANTES/DESPUES CARDS ===== */
.wa-ba-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 28px 20px;
  text-align: center;
  flex: 0 0 260px;
  scroll-snap-align: start;
}

.wa-ba-domain {
  font-family: monospace;
  font-size: 12px;
  color: #58a6ff;
  font-weight: 600;
  margin-bottom: 12px;
  word-break: break-all;
}

.wa-ba-scores {
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 6px;
}

.wa-ba-before { color: #f85149; }
.wa-ba-arrow { color: #6e7681; margin: 0 8px; }
.wa-ba-after { color: #3fb950; }

.wa-ba-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  margin-top: 10px;
}

.wa-ba-pill {
  font-size: 9px;
  padding: 2px 8px;
  border-radius: 8px;
  border: 1px solid #30363d;
  color: #8b949e;
}

/* ===== RESPONSIVE ===== */
@media (min-width: 768px) {
  .wa-carousel-card {
    flex: 0 0 300px;
  }
  .wa-ba-card {
    flex: 0 0 280px;
  }
}
'''

ftp = ftplib.FTP_TLS(HOST, timeout=15, context=CONTEXT)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()

# Leer el MU-plugin actual
ftp.cwd("/public_html/web/wp-content/mu-plugins")
current = []
ftp.retrlines("RETR wa-dark-theme.php", current.append)
current_content = "\n".join(current)

# Insertar carrusel CSS antes del cierre </style>
new_content = current_content.replace("</style>", CAROUSEL_CSS + "\n</style>")

bio = io.BytesIO(new_content.encode("utf-8"))
ftp.storbinary("STOR wa-dark-theme.php", bio)
print(">>> CSS carrusel agregado <<<")
ftp.quit()

# =====================================================================
# 2. Generar imagenes para el carrusel y subirlas a WP
# =====================================================================
print("\n=== Generando imagenes para carrusel ===")

from PIL import Image, ImageDraw, ImageFont

def crear_imagen_sitio(domain, score, label, color_bg, filename):
    """Genera una imagen 600x340 estilo card para el carrusel."""
    img = Image.new("RGB", (600, 340), "#21262d")
    draw = ImageDraw.Draw(img)

    # Fondo con gradiente simulado (bandas)
    for i in range(10):
        y = i * 34
        shade = 33 + i * 2
        draw.rectangle([0, y, 600, y + 34], fill=f"#{shade:x}{shade+3:x}{shade+6:x}")

    # URL bar simulada (browser chrome)
    draw.rectangle([20, 20, 580, 44], fill="#0d1117", outline="#30363d")
    draw.rectangle([30, 28, 570, 36], fill="#161b22")
    draw.text((40, 20), domain, fill="#58a6ff")

    # Score badge
    cx, cy = 540, 80
    r = 32
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color_bg)
    score_text = str(score)
    draw.text((cx, cy - 16), score_text, fill="#000000", anchor="mt", font_size=28)

    # Label
    draw.text((40, 70), label, fill="#8b949e")

    # Fake score bars
    categories = [
        ("SEO", 1, "#f85149"),
        ("Accesibilidad", 2, "#f85149"),
        ("Rendimiento", 3, "#f85149"),
        ("Conversion", 4, "#f85149"),
        ("UX", 6, "#d29922"),
    ]
    y_start = 120
    for cat_name, cat_score, cat_color in categories:
        bar_width = cat_score * 30
        draw.text((40, y_start), cat_name, fill="#8b949e")
        draw.rectangle([110, y_start + 4, 110 + bar_width, y_start + 16], fill=cat_color)
        draw.text((114 + bar_width, y_start), str(cat_score), fill=cat_color)
        y_start += 28

    # CTA text
    draw.text((40, 290), "Analizar ahora ->", fill="#58a6ff")

    out_path = Path(f"E:/DelMonte/web-analyzer/{filename}")
    img.save(out_path, "PNG")
    print(f"  Guardada: {filename}")
    return out_path

# Generar imagenes para los 5 sitios famosos
sitios = [
    ("cariverplate.com.ar", 3.2, "River Plate - Sitio Oficial", "#f85149", "img-river.png"),
    ("one-piece.com", 4.0, "One Piece - Sitio Oficial (Japon)", "#f85149", "img-onepiece.png"),
    ("yahoo.com", 4.8, "Yahoo - Portal #1 USA", "#f85149", "img-yahoo.png"),
    ("bocajuniors.com.ar", 6.0, "Boca Juniors - Sitio Oficial", "#d29922", "img-boca.png"),
    ("ole.com.ar", 6.6, "Diario Deportivo Ole", "#d29922", "img-ole.png"),
]

imagenes = []
for domain, score, label, color, fname in sitios:
    path = crear_imagen_sitio(domain, score, label, color, fname)
    imagenes.append((fname, path))

# =====================================================================
# 3. Subir imagenes a WordPress media library
# =====================================================================
print("\n=== Subiendo imagenes a WordPress ===")
media_ids = {}
for fname, path in imagenes:
    with open(path, "rb") as f:
        img_data = f.read()

    img_headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'image/png',
        'Content-Disposition': f'attachment; filename="{fname}"'
    }

    r = requests.post(
        f'{BASE}/media',
        headers=img_headers,
        data=img_data
    )
    if r.status_code == 201:
        mid = r.json()['id']
        url = r.json()['source_url']
        media_ids[fname] = (mid, url)
        print(f"  {fname}: ID={mid}")
    else:
        print(f"  {fname}: ERROR {r.status_code} - {r.text[:200]}")

# =====================================================================
# 4. Actualizar pagina Home con carrusel con imagenes
# =====================================================================
print("\n=== Actualizando Home con carrusel ===")

# Construir tarjetas del carrusel con imagenes reales
carousel_cards = ""
sitios_data = [
    ("img-river.png", "cariverplate.com.ar", 3.2, "bad", "River Plate - Sitio Oficial",
     [("SEO", 1, "bad"), ("Acces.", 2, "bad"), ("Rend.", 3, "bad"), ("Conv.", 4, "bad"), ("UX", 6, "ok")],
     "www.cariverplate.com.ar"),
    ("img-onepiece.png", "one-piece.com", 4.0, "bad", "One Piece - Sitio Oficial (Japon)",
     [("SEO", 5, "bad"), ("Acces.", 2, "bad"), ("Rend.", 5, "ok"), ("Conv.", 4, "bad"), ("UX", 4, "bad")],
     "one-piece.com"),
    ("img-yahoo.png", "yahoo.com", 4.8, "bad", "Yahoo - Portal #1 USA",
     [("SEO", 4, "bad"), ("Acces.", 3, "bad"), ("Rend.", 6, "ok"), ("Conv.", 4, "bad"), ("UX", 7, "ok")],
     "yahoo.com"),
    ("img-boca.png", "bocajuniors.com.ar", 6.0, "ok", "Boca Juniors - Sitio Oficial",
     [("SEO", 7, "ok"), ("Acces.", 4, "bad"), ("Rend.", 4, "bad"), ("Conv.", 5, "ok"), ("UX", 10, "good")],
     "www.bocajuniors.com.ar"),
    ("img-ole.png", "ole.com.ar", 6.6, "ok", "Diario Deportivo Ole",
     [("SEO", 6, "ok"), ("Acces.", 6, "ok"), ("Rend.", 7, "ok"), ("Conv.", 5, "ok"), ("UX", 9, "good")],
     "www.ole.com.ar"),
]

for img_name, domain, score, score_class, label, categorias, analyze_url in sitios_data:
    if img_name in media_ids:
        img_url = media_ids[img_name][1]
    else:
        img_url = ""

    scores_html = ""
    for cat_name, cat_score, cat_class in categorias:
        scores_html += f'<span><span class="wa-mini-dot {cat_class}"></span>{cat_name} {cat_score}</span>\n'

    card = f'''<!-- wp:html -->
<a href="https://web-analyzer-1-l8uc.onrender.com/?analyze_url={analyze_url}" target="_blank" rel="noopener" class="wa-carousel-card">
<div class="wa-carousel-card-img">
<img src="{img_url}" alt="{domain}" loading="lazy" />
<div class="wa-carousel-score-badge {score_class}">{score}</div>
</div>
<div class="wa-carousel-card-body">
<div class="wa-carousel-card-domain">{domain}</div>
<div class="wa-carousel-card-label">{label}</div>
<div class="wa-carousel-card-scores">
{scores_html}</div>
<div class="wa-carousel-card-cta">Analizar ahora &rarr;</div>
</div>
</a>
<!-- /wp:html -->'''
    carousel_cards += card

# Pagina Home completa con carrusel
home_html = f'''<!-- wp:cover {"overlayColor":"black","overlayOpacity":0.85,"minHeight":400,"align":"full","style":{"spacing":{"padding":{"top":"80px","bottom":"80px"}}}} -->
<div class="wp-block-cover alignfull" style="padding-top:80px;padding-bottom:80px;min-height:400px"><span aria-hidden="true" class="wp-block-cover__background has-black-background-color has-opacity has-background-dim-80 has-background-dim"></span><div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","level":1,"style":{"typography":{"fontSize":"38px","fontWeight":"800"}}} -->
<h1 class="has-text-align-center" style="font-size:38px;font-weight:800;color:#ffffff">Tu web <span style="color:#f85149">pierde clientes</span> y no sabes por que</h1>
<!-- /wp:heading -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"16px"}}} -->
<p class="has-text-align-center" style="font-size:16px;color:#8b949e">Analiza cualquier sitio <strong>gratis y sin registro</strong>. En 30 segundos tenes una auditoria completa con puntaje, hallazgos y soluciones listas para aplicar.</p>
<!-- /wp:paragraph -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<!-- wp:button {"style":{"spacing":{"padding":{"top":"16px","bottom":"16px","left":"40px","right":"40px"}},"typography":{"fontSize":"17px","fontWeight":"700"},"color":{"background":"#1f6feb"},"border":{"radius":"8px"}}} -->
<div class="wp-block-button"><a class="wp-block-button__link has-background wp-element-button" href="https://web-analyzer-1-l8uc.onrender.com/" style="border-radius:8px;background-color:#1f6feb;padding-top:16px;padding-bottom:16px;padding-left:40px;padding-right:40px;font-size:17px;font-weight:700;color:#ffffff" target="_blank" rel="noreferrer noopener">Analizar mi sitio gratis</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"11px"}}} -->
<p class="has-text-align-center" style="font-size:11px;color:#6e7681">Sin registro. Sin costo. Sin compromiso.</p>
<!-- /wp:paragraph --></div></div>
<!-- /wp:cover -->

<!-- wp:separator {"backgroundColor":"border","className":"is-style-wide"} -->
<hr class="wp-block-separator has-text-color has-border-color has-alpha-channel-opacity has-border-background-color has-background is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:html -->
<div class="wa-carousel-wrapper">
<h2 class="wa-carousel-title">Incluso los mas grandes fallan</h2>
<p class="wa-carousel-subtitle">Analizamos sitios con millones de visitas. Los resultados hablan solos. Desliza para ver mas.</p>
<div class="wa-carousel">
{carousel_cards}
</div>
</div>
<!-- /wp:html -->

<!-- wp:separator {"backgroundColor":"border","className":"is-style-wide"} -->
<hr class="wp-block-separator has-text-color has-border-color has-alpha-channel-opacity has-border-background-color has-background is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"textAlign":"center","level":2,"style":{"typography":{"textTransform":"uppercase","fontSize":"13px","letterSpacing":"1px"}}} -->
<h2 class="has-text-align-center" style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:#8b949e">Antes y despues con Web Analyzer</h2>
<!-- /wp:heading -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"12px"}}} -->
<p class="has-text-align-center" style="font-size:12px;color:#6e7681">Tres sitios WordPress reales optimizados con nuestras soluciones.</p>
<!-- /wp:paragraph -->

<!-- wp:html -->
<div class="wa-carousel-wrapper">
<div class="wa-carousel">
<div class="wa-ba-card">
<div class="wa-ba-domain">riverplate-info.com.ar</div>
<div class="wa-ba-scores">
<span class="wa-ba-before">5.5</span>
<span class="wa-ba-arrow">&#8594;</span>
<span class="wa-ba-after">9.6</span>
</div>
<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes &#8594; Despues</div>
<div class="wa-ba-pills">
<span class="wa-ba-pill">lazy loading</span>
<span class="wa-ba-pill">meta tags</span>
<span class="wa-ba-pill">WebP</span>
<span class="wa-ba-pill">alt text</span>
</div>
</div>
<div class="wa-ba-card">
<div class="wa-ba-domain">diario-albiceleste.com.ar</div>
<div class="wa-ba-scores">
<span class="wa-ba-before">5.8</span>
<span class="wa-ba-arrow">&#8594;</span>
<span class="wa-ba-after">9.6</span>
</div>
<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes &#8594; Despues</div>
<div class="wa-ba-pills">
<span class="wa-ba-pill">lazy loading</span>
<span class="wa-ba-pill">OG tags</span>
<span class="wa-ba-pill">WebP</span>
<span class="wa-ba-pill">formularios</span>
</div>
</div>
<div class="wa-ba-card">
<div class="wa-ba-domain">revista-espectaculos.com.ar</div>
<div class="wa-ba-scores">
<span class="wa-ba-before">6.0</span>
<span class="wa-ba-arrow">&#8594;</span>
<span class="wa-ba-after">9.6</span>
</div>
<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes &#8594; Despues</div>
<div class="wa-ba-pills">
<span class="wa-ba-pill">lazy loading</span>
<span class="wa-ba-pill">SEO</span>
<span class="wa-ba-pill">WebP</span>
<span class="wa-ba-pill">CTAs</span>
</div>
</div>
</div>
</div>
<!-- /wp:html -->

<!-- wp:separator {"backgroundColor":"border","className":"is-style-wide"} -->
<hr class="wp-block-separator has-text-color has-border-color has-alpha-channel-opacity has-border-background-color has-background is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"textAlign":"center","level":2,"style":{"typography":{"textTransform":"uppercase","fontSize":"13px","letterSpacing":"1px"}}} -->
<h2 class="has-text-align-center" style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:#8b949e">Que obtenes con cada analisis</h2>
<!-- /wp:heading -->

<!-- wp:columns {"style":{"spacing":{"blockGap":"16px","padding":{"top":"20px","bottom":"20px"}}}} -->
<div class="wp-block-columns" style="padding-top:20px;padding-bottom:20px">
<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:group {"style":{"color":{"background":"#161b22"},"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","bottom":"20px","left":"20px","right":"20px"}}}} -->
<div class="wp-block-group has-background" style="border-width:1px;border-radius:8px;background-color:#161b22;padding:20px">
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"28px"}}} -->
<p class="has-text-align-center" style="font-size:28px">&#128202;</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"15px","fontWeight":"600"}}} -->
<p class="has-text-align-center" style="font-size:15px;font-weight:600;color:#ffffff">Scorecard en 5 categorias</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"12px"}}} -->
<p class="has-text-align-center" style="font-size:12px;color:#8b949e">Rendimiento, Accesibilidad, SEO, UX y Conversion con puntaje del 1 al 10.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:column -->
<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:group {"style":{"color":{"background":"#161b22"},"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","bottom":"20px","left":"20px","right":"20px"}}}} -->
<div class="wp-block-group has-background" style="border-width:1px;border-radius:8px;background-color:#161b22;padding:20px">
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"28px"}}} -->
<p class="has-text-align-center" style="font-size:28px">&#128269;</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"15px","fontWeight":"600"}}} -->
<p class="has-text-align-center" style="font-size:15px;font-weight:600;color:#ffffff">Hallazgos criticos</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"12px"}}} -->
<p class="has-text-align-center" style="font-size:12px;color:#8b949e">Cada problema detectado con su impacto real en el negocio.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:column -->
<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:group {"style":{"color":{"background":"#161b22"},"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","bottom":"20px","left":"20px","right":"20px"}}}} -->
<div class="wp-block-group has-background" style="border-width:1px;border-radius:8px;background-color:#161b22;padding:20px">
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"28px"}}} -->
<p class="has-text-align-center" style="font-size:28px">&#128230;</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"15px","fontWeight":"600"}}} -->
<p class="has-text-align-center" style="font-size:15px;font-weight:600;color:#ffffff">Plugin WordPress</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center","style":{"typography":{"fontSize":"12px"}}} -->
<p class="has-text-align-center" style="font-size:12px;color:#8b949e">Soluciones descargables que aplicas directo en tu sitio sin tocar codigo.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:column -->
</div>
<!-- /wp:columns -->

<!-- wp:separator {"backgroundColor":"border","className":"is-style-wide"} -->
<hr class="wp-block-separator has-text-color has-border-color has-alpha-channel-opacity has-border-background-color has-background is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<!-- wp:button {"style":{"spacing":{"padding":{"top":"18px","bottom":"18px","left":"48px","right":"48px"}},"typography":{"fontSize":"18px","fontWeight":"700"},"color":{"background":"#3fb950"},"border":{"radius":"8px"}}} -->
<div class="wp-block-button"><a class="wp-block-button__link has-background wp-element-button" href="https://web-analyzer-1-l8uc.onrender.com/" style="border-radius:8px;background-color:#3fb950;padding-top:18px;padding-bottom:18px;padding-left:48px;padding-right:48px;font-size:18px;font-weight:700;color:#000000" target="_blank" rel="noreferrer noopener">Analizar gratis ahora &#8594;</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->'''

# Actualizar la pagina Home (ID 10)
r = requests.post(f'{BASE}/pages/10', headers=headers, json={
    'content': home_html
})
print(f"Home actualizada: {r.status_code}")

print("\n=== CARRUSEL COMPLETADO ===")
print("Visita: https://webanalyzer.com.ar/web/")
