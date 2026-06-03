"""
Fix: MU-plugin CSS ultra-agresivo + pagina Home en HTML puro.
"""
import os
import ftplib, ssl, io, requests, base64

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")
WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
api_headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# =====================================================================
# 1. MU-plugin CSS - OVERRIDE TOTAL
# =====================================================================
MU_PLUGIN = r'''<?php
/**
 * Plugin Name: Web Analyzer Dark Theme
 */

// Forzar app passwords en HTTP
add_filter('wp_is_application_passwords_available', '__return_true');

// 1. BORRAR los global styles de WordPress (theme.json)
add_action('wp_enqueue_scripts', 'wa_remove_theme_styles', 9999);
function wa_remove_theme_styles() {
    wp_dequeue_style('global-styles');
    wp_deregister_style('global-styles');
    wp_dequeue_style('wp-block-library');
    wp_deregister_style('wp-block-library');
}

// 2. CARGAR nuestro CSS con maxima prioridad
add_action('wp_head', 'wa_dark_head', 1);
function wa_dark_head() {
?>
<meta name="theme-color" content="#0d1117">
<style id="wa-theme">
/* ============================================================
   WEB ANALYZER - DARK THEME v2 (RESET TOTAL)
   ============================================================ */

/* Nuclear reset */
html, body, .wp-site-blocks, .wp-block-template-part,
main, article, section, header, footer, div {
  background: #0d1117 !important;
}

body, body * {
  color: #e6edf3 !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
  line-height: 1.6 !important;
}

/* ===== COLORES ===== */
:root {
  --bg: #0d1117;
  --bg2: #161b22;
  --bg3: #21262d;
  --border: #30363d;
  --text: #e6edf3;
  --text2: #8b949e;
  --text3: #6e7681;
  --blue: #58a6ff;
  --green: #3fb950;
  --yellow: #d29922;
  --red: #f85149;
  --accent: #1f6feb;
  --radius: 8px;
}

/* Links */
a { color: #58a6ff !important; text-decoration: none !important; }
a:hover { text-decoration: underline !important; }

/* Headings */
h1,h2,h3,h4,h5,h6,.wp-block-heading,
.wp-block-post-title,.wp-block-site-title {
  color: #ffffff !important;
  font-weight: 700 !important;
}

/* Site header */
.wp-block-template-part, header.wp-block-template-part,
.wp-site-blocks > header, .site-header {
  background: #161b22 !important;
  border-bottom: 1px solid #30363d !important;
  padding: 16px 24px !important;
}

/* Site footer */
.wp-site-blocks > footer, footer.wp-block-template-part, .site-footer {
  background: #161b22 !important;
  border-top: 1px solid #30363d !important;
  text-align: center !important;
  padding: 20px !important;
  font-size: 12px !important;
  color: #6e7681 !important;
}

/* Site title */
.wp-block-site-title a {
  color: #ffffff !important;
  font-weight: 800 !important;
  font-size: 20px !important;
}

/* Post/page title */
.wp-block-post-title, .entry-title, h1.entry-title {
  color: #ffffff !important;
  font-size: 28px !important;
  font-weight: 800 !important;
}

/* Post content area */
.entry-content, .wp-block-post-content, .post-content,
main .wp-block-group {
  max-width: 860px !important;
  margin-left: auto !important;
  margin-right: auto !important;
  padding: 24px !important;
}

/* Post cards in blog */
.wp-block-post-template > li, .wp-block-post {
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  border-radius: 8px !important;
  padding: 24px !important;
  margin-bottom: 16px !important;
  transition: border-color 0.2s !important;
}
.wp-block-post-template > li:hover, .wp-block-post:hover {
  border-color: #58a6ff !important;
}

/* Post meta */
.wp-block-post-date, .wp-block-post-author, .wp-block-post-date time {
  color: #6e7681 !important;
  font-size: 12px !important;
}

/* Read more link */
.wp-block-read-more, .wp-block-post-excerpt__more-link {
  color: #58a6ff !important;
  font-weight: 600 !important;
  font-size: 13px !important;
}

/* Buttons */
.wp-block-button__link, .wp-element-button, button[type="submit"] {
  background: #1f6feb !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 12px 28px !important;
  font-weight: 700 !important;
  font-size: 15px !important;
  text-decoration: none !important;
  transition: all 0.15s !important;
  display: inline-block !important;
}
.wp-block-button__link:hover, .wp-element-button:hover {
  background: #388bfd !important;
  transform: scale(1.02) !important;
}

/* Blocks: group */
.wp-block-group {
  background: transparent !important;
  color: #e6edf3 !important;
}

/* Blocks: cover */
.wp-block-cover, .wp-block-cover__background {
  background: #0d1117 !important;
}

/* Tables */
table, .wp-block-table {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 16px 0 !important;
}
table th, .wp-block-table th {
  background: #21262d !important;
  color: #e6edf3 !important;
  text-align: left !important;
  padding: 10px 14px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  border-bottom: 2px solid #30363d !important;
}
table td, .wp-block-table td {
  background: #161b22 !important;
  color: #e6edf3 !important;
  padding: 10px 14px !important;
  font-size: 13px !important;
  border-bottom: 1px solid #21262d !important;
}

/* Code */
code, pre, .wp-block-code {
  background: #21262d !important;
  color: #e6edf3 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-family: 'Consolas', 'Monaco', monospace !important;
  font-size: 13px !important;
}

/* Lists */
ul, ol, .wp-block-list {
  color: #8b949e !important;
  padding-left: 20px !important;
  line-height: 1.8 !important;
}
li { color: #8b949e !important; }

/* Blockquote */
blockquote, .wp-block-quote {
  border-left: 3px solid #58a6ff !important;
  background: #161b22 !important;
  padding: 16px 20px !important;
  color: #8b949e !important;
  font-style: italic !important;
  margin: 20px 0 !important;
}

/* Separator */
hr, .wp-block-separator {
  border: none !important;
  border-top: 1px solid #30363d !important;
  margin: 32px 0 !important;
}

/* Search */
.wp-block-search__input, input[type="search"] {
  background: #0d1117 !important;
  border: 1px solid #30363d !important;
  color: #e6edf3 !important;
  border-radius: 8px !important;
  padding: 10px 14px !important;
}

/* Jetpack sharing */
div.sharedaddy h3.sd-title {
  color: #8b949e !important;
}

/* Page navigation */
.wp-block-query-pagination {
  margin-top: 24px !important;
}
.wp-block-query-pagination .page-numbers {
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  color: #e6edf3 !important;
  padding: 8px 14px !important;
  border-radius: 6px !important;
}
.wp-block-query-pagination .page-numbers.current {
  background: #1f6feb !important;
  border-color: #1f6feb !important;
}

/* Sidebar widgets */
.widget {
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  border-radius: 8px !important;
  padding: 20px !important;
  margin-bottom: 16px !important;
}
.widget-title {
  color: #ffffff !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  margin-bottom: 12px !important;
}

/* ===== CARRUSEL (CSS puro) ===== */
.wa-carousel-wrapper {
  max-width: 100%;
  margin: 32px 0;
  overflow: hidden;
}
.wa-carousel-title {
  font-size: 13px !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #8b949e !important;
  text-align: center;
  margin-bottom: 4px;
}
.wa-carousel-subtitle {
  font-size: 12px;
  color: #6e7681 !important;
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
.wa-carousel::-webkit-scrollbar { height: 6px; }
.wa-carousel::-webkit-scrollbar-track { background: #0d1117; border-radius: 3px; }
.wa-carousel::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

.wa-carousel-card {
  flex: 0 0 280px;
  scroll-snap-align: start;
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  border-radius: 12px !important;
  overflow: hidden;
  cursor: pointer;
  text-decoration: none !important;
  display: block;
  min-height: 340px;
  transition: border-color 0.2s, transform 0.2s;
}
.wa-carousel-card:hover {
  border-color: #58a6ff !important;
  transform: translateY(-2px);
}
.wa-carousel-card-img {
  width: 100%;
  height: 160px;
  background: #21262d;
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
  top: 12px; right: 12px;
  width: 48px; height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  color: #000 !important;
  z-index: 2;
}
.wa-carousel-score-badge.bad { background: #f85149 !important; }
.wa-carousel-score-badge.ok { background: #d29922 !important; }
.wa-carousel-score-badge.good { background: #3fb950 !important; }

.wa-carousel-card-body {
  padding: 16px;
}
.wa-carousel-card-domain {
  font-family: monospace !important;
  font-size: 13px;
  color: #58a6ff !important;
  font-weight: 600;
}
.wa-carousel-card-label {
  font-size: 11px;
  color: #6e7681 !important;
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
  color: #8b949e !important;
  display: flex;
  align-items: center;
  gap: 4px;
}
.wa-mini-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.wa-mini-dot.bad { background: #f85149 !important; }
.wa-mini-dot.ok { background: #d29922 !important; }
.wa-mini-dot.good { background: #3fb950 !important; }

.wa-carousel-card-cta {
  color: #58a6ff !important;
  font-size: 11px;
  font-weight: 600;
}

/* ===== ANTES/DESPUES ===== */
.wa-ba-card {
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  border-radius: 12px !important;
  padding: 28px 20px;
  text-align: center;
  flex: 0 0 260px;
  scroll-snap-align: start;
}
.wa-ba-domain {
  font-family: monospace !important;
  font-size: 12px;
  color: #58a6ff !important;
  font-weight: 600;
  word-break: break-all;
}
.wa-ba-scores {
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 6px;
}
.wa-ba-before { color: #f85149 !important; }
.wa-ba-arrow { color: #6e7681 !important; margin: 0 8px; }
.wa-ba-after { color: #3fb950 !important; }
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
  color: #8b949e !important;
}

/* ===== CTA BOX ===== */
.wa-cta-box {
  background: linear-gradient(135deg, #1a3a5c, #0d2137) !important;
  border: 2px solid #1f6feb !important;
  border-radius: 12px !important;
  padding: 32px !important;
  text-align: center !important;
  margin: 32px 0 !important;
}
.wa-cta-box h2 {
  color: #fff !important;
  font-size: 22px !important;
  margin-bottom: 12px !important;
}
.wa-cta-box .wa-btn {
  display: inline-block !important;
  background: #3fb950 !important;
  color: #000 !important;
  padding: 14px 36px !important;
  border-radius: 8px !important;
  font-weight: 800 !important;
  font-size: 16px !important;
  text-decoration: none !important;
  margin-top: 12px !important;
}

/* ===== FEATURE CARDS ===== */
.wa-feature-card {
  background: #161b22 !important;
  border: 1px solid #30363d !important;
  border-radius: 12px !important;
  padding: 28px 20px !important;
  text-align: center !important;
}
.wa-feature-icon {
  font-size: 36px;
  margin-bottom: 12px;
}
.wa-feature-title {
  color: #ffffff !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  margin-bottom: 8px !important;
}
.wa-feature-desc {
  color: #8b949e !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
}

/* ===== HERO ===== */
.wa-hero {
  text-align: center;
  padding: 64px 16px 40px;
}
.wa-hero h1 {
  font-size: 38px !important;
  font-weight: 800 !important;
  color: #ffffff !important;
  line-height: 1.2 !important;
  margin-bottom: 16px !important;
}
.wa-hero p {
  font-size: 16px !important;
  color: #8b949e !important;
  max-width: 620px;
  margin: 0 auto 28px !important;
  line-height: 1.7 !important;
}
.wa-hero .wa-hero-red {
  color: #f85149 !important;
}
.wa-btn-main {
  display: inline-block !important;
  padding: 16px 40px !important;
  background: #1f6feb !important;
  color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: 17px !important;
  font-weight: 700 !important;
  text-decoration: none !important;
  cursor: pointer !important;
  transition: background 0.15s, transform 0.1s !important;
}
.wa-btn-main:hover {
  background: #388bfd !important;
  transform: scale(1.02) !important;
  text-decoration: none !important;
}
.wa-btn-green {
  display: inline-block !important;
  background: #3fb950 !important;
  color: #000 !important;
  padding: 18px 48px !important;
  border-radius: 8px !important;
  font-weight: 800 !important;
  font-size: 18px !important;
  text-decoration: none !important;
}
.wa-btn-green:hover {
  transform: scale(1.03) !important;
  text-decoration: none !important;
}
.wa-hero-note {
  font-size: 11px !important;
  color: #6e7681 !important;
  margin-top: 10px;
}

/* ===== SECTION HEADERS ===== */
.wa-section-label {
  font-size: 13px !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #8b949e !important;
  text-align: center;
  margin-bottom: 6px;
}
.wa-section-sub {
  font-size: 12px !important;
  color: #6e7681 !important;
  text-align: center;
  margin-bottom: 24px;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .wa-hero h1 { font-size: 26px !important; }
  .wa-carousel-card { flex: 0 0 240px; }
  .wa-ba-card { flex: 0 0 220px; }
  .wa-hero { padding: 40px 16px 24px; }
}

/* ===== CLEAN WP ADMIN BAR ===== */
#wpadminbar { background: #161b22 !important; }

/* ===== OVERRIDE ANY REMAINING WP STYLES ===== */
.has-background { background: transparent !important; }
.has-base-background-color { background: #0d1117 !important; }
.has-contrast-color { color: #e6edf3 !important; }
.has-global-padding { padding: 0 24px !important; }

/* ===== DESKTOP ADJUSTMENTS ===== */
@media (min-width: 768px) {
  .wa-carousel-card { flex: 0 0 300px; }
  .wa-ba-card { flex: 0 0 280px; }
}
</style>
<?php
}
'''

print("=== Actualizando MU-plugin (CSS v2) ===")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=15, context=CONTEXT)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()

ftp.cwd("/public_html/web/wp-content/mu-plugins")
bio = io.BytesIO(MU_PLUGIN.encode("utf-8"))
ftp.storbinary("STOR wa-dark-theme.php", bio)
print(">>> MU-plugin v2 subido <<<")
ftp.quit()

# =====================================================================
# 2. Actualizar Home con HTML puro (sin depender de bloques Gutenberg)
# =====================================================================
print("\n=== Reconstruyendo Home con HTML puro ===")

# Obtener URLs de imagenes
r = requests.get(f'{BASE}/media', headers=api_headers, params={'per_page': 20})
media = {m['slug']: m['source_url'] for m in r.json() if m.get('slug')}

# Construir carrusel
def card(slug, domain, score, sc, label, cats, analyze_url):
    img_url = media.get(slug, "")
    s = ""
    for name, val, cls in cats:
        s += f'<span><span class="wa-mini-dot {cls}"></span>{name} {val}</span>'
    return f'''<a href="https://web-analyzer-1-l8uc.onrender.com/?analyze_url={analyze_url}" target="_blank" rel="noopener" class="wa-carousel-card">
<div class="wa-carousel-card-img"><img src="{img_url}" alt="{domain}" loading="lazy" /><div class="wa-carousel-score-badge {sc}">{score}</div></div>
<div class="wa-carousel-card-body"><div class="wa-carousel-card-domain">{domain}</div><div class="wa-carousel-card-label">{label}</div><div class="wa-carousel-card-scores">{s}</div><div class="wa-carousel-card-cta">Analizar ahora &rarr;</div></div></a>'''

cards = ""
sitios = [
    ("img-river", "cariverplate.com.ar", 3.2, "bad", "River Plate — Sitio Oficial",
     [("SEO", 1, "bad"), ("Acces.", 2, "bad"), ("Rend.", 3, "bad"), ("Conv.", 4, "bad"), ("UX", 6, "ok")], "www.cariverplate.com.ar"),
    ("img-onepiece", "one-piece.com", 4.0, "bad", "One Piece — Oficial Japón",
     [("SEO", 5, "bad"), ("Acces.", 2, "bad"), ("Rend.", 5, "ok"), ("Conv.", 4, "bad"), ("UX", 4, "bad")], "one-piece.com"),
    ("img-yahoo", "yahoo.com", 4.8, "bad", "Yahoo — Portal #1 USA",
     [("SEO", 4, "bad"), ("Acces.", 3, "bad"), ("Rend.", 6, "ok"), ("Conv.", 4, "bad"), ("UX", 7, "ok")], "yahoo.com"),
    ("img-boca", "bocajuniors.com.ar", 6.0, "ok", "Boca Juniors — Oficial",
     [("SEO", 7, "ok"), ("Acces.", 4, "bad"), ("Rend.", 4, "bad"), ("Conv.", 5, "ok"), ("UX", 10, "good")], "www.bocajuniors.com.ar"),
    ("img-ole", "ole.com.ar", 6.6, "ok", "Diario Deportivo Olé",
     [("SEO", 6, "ok"), ("Acces.", 6, "ok"), ("Rend.", 7, "ok"), ("Conv.", 5, "ok"), ("UX", 9, "good")], "www.ole.com.ar"),
]
for args in sitios:
    cards += card(*args)

HOME = f"""<!-- wp:html -->
<div class="wa-hero">
<h1>Tu web <span class="wa-hero-red">pierde clientes</span> y no sabés por qué</h1>
<p>Analizá cualquier sitio <strong>gratis y sin registro</strong>. En 30 segundos tenés una auditoría completa con puntaje, hallazgos críticos y soluciones listas para aplicar.</p>
<a href="https://web-analyzer-1-l8uc.onrender.com/" class="wa-btn-main">Analizar mi sitio gratis →</a>
<p class="wa-hero-note">Sin registro. Sin costo. Sin compromiso.</p>
</div>

<hr />

<div class="wa-carousel-wrapper">
<h2 class="wa-section-label">Incluso los más grandes fallan</h2>
<p class="wa-section-sub">Analizamos sitios con millones de visitas. Los resultados hablan solos. Deslizá para ver más.</p>
<div class="wa-carousel">
{cards}
</div>
</div>

<hr />

<h2 class="wa-section-label">Antes y después con Web Analyzer</h2>
<p class="wa-section-sub">Tres sitios WordPress reales optimizados con nuestras soluciones.</p>

<div class="wa-carousel-wrapper">
<div class="wa-carousel">
<div class="wa-ba-card">
<div class="wa-ba-domain">riverplate-info.com.ar</div>
<div class="wa-ba-scores"><span class="wa-ba-before">5.5</span><span class="wa-ba-arrow">→</span><span class="wa-ba-after">9.6</span></div>
<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes → Después</div>
<div class="wa-ba-pills"><span class="wa-ba-pill">lazy loading</span><span class="wa-ba-pill">meta tags</span><span class="wa-ba-pill">WebP</span><span class="wa-ba-pill">alt text</span></div>
</div>
<div class="wa-ba-card">
<div class="wa-ba-domain">diario-albiceleste.com.ar</div>
<div class="wa-ba-scores"><span class="wa-ba-before">5.8</span><span class="wa-ba-arrow">→</span><span class="wa-ba-after">9.6</span></div>
<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes → Después</div>
<div class="wa-ba-pills"><span class="wa-ba-pill">lazy loading</span><span class="wa-ba-pill">OG tags</span><span class="wa-ba-pill">WebP</span><span class="wa-ba-pill">formularios</span></div>
</div>
<div class="wa-ba-card">
<div class="wa-ba-domain">revista-espectaculos.com.ar</div>
<div class="wa-ba-scores"><span class="wa-ba-before">6.0</span><span class="wa-ba-arrow">→</span><span class="wa-ba-after">9.6</span></div>
<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes → Después</div>
<div class="wa-ba-pills"><span class="wa-ba-pill">lazy loading</span><span class="wa-ba-pill">SEO</span><span class="wa-ba-pill">WebP</span><span class="wa-ba-pill">CTAs</span></div>
</div>
</div>
</div>

<hr />

<h2 class="wa-section-label">Qué obtenés con cada análisis</h2>
<p class="wa-section-sub">Todo lo que necesitás para mejorar tu sitio, en 30 segundos.</p>

<div style="display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin:24px 0">
<div class="wa-feature-card" style="flex:1;min-width:200px">
<div class="wa-feature-icon">📊</div>
<div class="wa-feature-title">Scorecard en 5 categorías</div>
<div class="wa-feature-desc">Rendimiento, Accesibilidad, SEO, UX y Conversión con puntaje del 1 al 10.</div>
</div>
<div class="wa-feature-card" style="flex:1;min-width:200px">
<div class="wa-feature-icon">🔍</div>
<div class="wa-feature-title">Hallazgos críticos</div>
<div class="wa-feature-desc">Cada problema detectado con su impacto real en el negocio y solución.</div>
</div>
<div class="wa-feature-card" style="flex:1;min-width:200px">
<div class="wa-feature-icon">📦</div>
<div class="wa-feature-title">Plugin WordPress</div>
<div class="wa-feature-desc">Soluciones descargables que aplicás directo en tu sitio sin tocar código.</div>
</div>
</div>

<hr />

<div style="text-align:center;padding:48px 16px">
<h2 style="font-size:22px;font-weight:700;color:#fff;margin-bottom:10px">¿Tu sitio está mejor que el de River?</h2>
<p style="color:#8b949e;font-size:14px;margin-bottom:22px">Descubrilo en 30 segundos. Sin registro. Sin costo.</p>
<a href="https://web-analyzer-1-l8uc.onrender.com/" class="wa-btn-green">Analizar gratis ahora →</a>
</div>

<div style="text-align:center;padding:24px;border-top:1px solid #30363d;margin-top:32px;font-size:12px;color:#6e7681">
<a href="/blog/" style="color:#58a6ff">Blog</a> &nbsp;·&nbsp;
<a href="mailto:webanalyzer.app@gmail.com" style="color:#58a6ff">webanalyzer.app@gmail.com</a>
</div>
<!-- /wp:html -->
"""

r = requests.post(f'{BASE}/pages/10', headers=api_headers, json={
    'title': 'Inicio',
    'content': HOME,
    'slug': 'inicio'
})
print(f"Home actualizada: {r.status_code}")
if r.status_code != 200:
    print(r.text[:300])

print("\n=== FIX COMPLETADO ===")
print("Visita: https://webanalyzer.com.ar/web/")
print("F5 para refrescar (Ctrl+F5 para limpiar cache)")
