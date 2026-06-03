"""Actualizar pagina Home con carrusel."""
import os
import requests, base64, json

WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# Obtener URLs de imagenes
r = requests.get(f'{BASE}/media', headers=headers, params={'per_page': 20})
media = {m['slug']: m['source_url'] for m in r.json()}
print("Imagenes disponibles:")
for slug, url in media.items():
    print(f"  {slug}: {url}")

# Construir carrusel HTML
def card_html(img_url, domain, score, score_class, label, cats, analyze_url):
    scores = ""
    for name, val, cls in cats:
        scores += '<span><span class="wa-mini-dot {}"></span>{} {}</span>'.format(cls, name, val)

    return '''<a href="https://web-analyzer-1-l8uc.onrender.com/?analyze_url={analyze_url}" target="_blank" rel="noopener" class="wa-carousel-card">
<div class="wa-carousel-card-img">
<img src="{img_url}" alt="{domain}" loading="lazy" />
<div class="wa-carousel-score-badge {score_class}">{score}</div>
</div>
<div class="wa-carousel-card-body">
<div class="wa-carousel-card-domain">{domain}</div>
<div class="wa-carousel-card-label">{label}</div>
<div class="wa-carousel-card-scores">{scores}</div>
<div class="wa-carousel-card-cta">Analizar ahora &rarr;</div>
</div>
</a>'''.format(
        img_url=img_url, domain=domain, score=score,
        score_class=score_class, label=label, scores=scores,
        analyze_url=analyze_url
    )

carousel_cards = ""
sitios = [
    ("img-river", "cariverplate.com.ar", 3.2, "bad", "River Plate - Sitio Oficial",
     [("SEO", 1, "bad"), ("Acces.", 2, "bad"), ("Rend.", 3, "bad"), ("Conv.", 4, "bad"), ("UX", 6, "ok")],
     "www.cariverplate.com.ar"),
    ("img-onepiece", "one-piece.com", 4.0, "bad", "One Piece - Oficial Japon",
     [("SEO", 5, "bad"), ("Acces.", 2, "bad"), ("Rend.", 5, "ok"), ("Conv.", 4, "bad"), ("UX", 4, "bad")],
     "one-piece.com"),
    ("img-yahoo", "yahoo.com", 4.8, "bad", "Yahoo - Portal #1 USA",
     [("SEO", 4, "bad"), ("Acces.", 3, "bad"), ("Rend.", 6, "ok"), ("Conv.", 4, "bad"), ("UX", 7, "ok")],
     "yahoo.com"),
    ("img-boca", "bocajuniors.com.ar", 6.0, "ok", "Boca Juniors - Oficial",
     [("SEO", 7, "ok"), ("Acces.", 4, "bad"), ("Rend.", 4, "bad"), ("Conv.", 5, "ok"), ("UX", 10, "good")],
     "www.bocajuniors.com.ar"),
    ("img-ole", "ole.com.ar", 6.6, "ok", "Diario Deportivo Ole",
     [("SEO", 6, "ok"), ("Acces.", 6, "ok"), ("Rend.", 7, "ok"), ("Conv.", 5, "ok"), ("UX", 9, "good")],
     "www.ole.com.ar"),
]

for slug, domain, score, score_class, label, cats, analyze_url in sitios:
    img_url = media.get(slug, "")
    if img_url:
        carousel_cards += card_html(img_url, domain, score, score_class, label, cats, analyze_url)

HOME_HTML = """<!-- wp:cover {"overlayColor":"black","overlayOpacity":0.85,"minHeight":400,"align":"full","style":{"spacing":{"padding":{"top":"80px","bottom":"80px"}}}} -->
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
<p style="font-size:11px;color:#6e7681;text-align:center">Sin registro. Sin costo. Sin compromiso.</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:html -->
<div class="wa-carousel-wrapper">
<h2 class="wa-carousel-title">Incluso los mas grandes fallan</h2>
<p class="wa-carousel-subtitle">Analizamos sitios con millones de visitas. Resultados que hablan solos. Desliza para ver mas.</p>
<div class="wa-carousel">
""" + carousel_cards + """
</div>
</div>
<!-- /wp:html -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
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
<div class="wa-ba-card"><div class="wa-ba-domain">riverplate-info.com.ar</div><div class="wa-ba-scores"><span class="wa-ba-before">5.5</span><span class="wa-ba-arrow">&#8594;</span><span class="wa-ba-after">9.6</span></div><div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes &#8594; Despues</div><div class="wa-ba-pills"><span class="wa-ba-pill">lazy loading</span><span class="wa-ba-pill">meta tags</span><span class="wa-ba-pill">WebP</span><span class="wa-ba-pill">alt text</span></div></div>
<div class="wa-ba-card"><div class="wa-ba-domain">diario-albiceleste.com.ar</div><div class="wa-ba-scores"><span class="wa-ba-before">5.8</span><span class="wa-ba-arrow">&#8594;</span><span class="wa-ba-after">9.6</span></div><div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes &#8594; Despues</div><div class="wa-ba-pills"><span class="wa-ba-pill">lazy loading</span><span class="wa-ba-pill">OG tags</span><span class="wa-ba-pill">WebP</span><span class="wa-ba-pill">formularios</span></div></div>
<div class="wa-ba-card"><div class="wa-ba-domain">revista-espectaculos.com.ar</div><div class="wa-ba-scores"><span class="wa-ba-before">6.0</span><span class="wa-ba-arrow">&#8594;</span><span class="wa-ba-after">9.6</span></div><div style="font-size:10px;text-transform:uppercase;letter-spacing:0.5px;color:#6e7681">Antes &#8594; Despues</div><div class="wa-ba-pills"><span class="wa-ba-pill">lazy loading</span><span class="wa-ba-pill">SEO</span><span class="wa-ba-pill">WebP</span><span class="wa-ba-pill">CTAs</span></div></div>
</div>
</div>
<!-- /wp:html -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"textAlign":"center","level":2,"style":{"typography":{"textTransform":"uppercase","fontSize":"13px","letterSpacing":"1px"}}} -->
<h2 class="has-text-align-center" style="font-size:13px;letter-spacing:1px;text-transform:uppercase;color:#8b949e">Que obtenes con cada analisis</h2>
<!-- /wp:heading -->

<!-- wp:columns {"style":{"spacing":{"blockGap":"16px","padding":{"top":"20px","bottom":"20px"}}}} -->
<div class="wp-block-columns" style="padding-top:20px;padding-bottom:20px">
<div class="wp-block-column"><div class="wp-block-group has-background" style="border-radius:8px;background-color:#161b22;padding:20px"><p class="has-text-align-center" style="font-size:28px">&#128202;</p><p class="has-text-align-center" style="font-size:15px;font-weight:600;color:#fff">Scorecard en 5 categorias</p><p class="has-text-align-center" style="font-size:12px;color:#8b949e">Rendimiento, Accesibilidad, SEO, UX y Conversion con puntaje del 1 al 10.</p></div></div>
<div class="wp-block-column"><div class="wp-block-group has-background" style="border-radius:8px;background-color:#161b22;padding:20px"><p class="has-text-align-center" style="font-size:28px">&#128269;</p><p class="has-text-align-center" style="font-size:15px;font-weight:600;color:#fff">Hallazgos criticos</p><p class="has-text-align-center" style="font-size:12px;color:#8b949e">Cada problema con su impacto real en el negocio.</p></div></div>
<div class="wp-block-column"><div class="wp-block-group has-background" style="border-radius:8px;background-color:#161b22;padding:20px"><p class="has-text-align-center" style="font-size:28px">&#128230;</p><p class="has-text-align-center" style="font-size:15px;font-weight:600;color:#fff">Plugin WordPress</p><p class="has-text-align-center" style="font-size:12px;color:#8b949e">Soluciones que aplicas en tu sitio sin tocar codigo.</p></div></div>
</div>
<!-- /wp:columns -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<div class="wp-block-button"><a class="wp-block-button__link has-background wp-element-button" href="https://web-analyzer-1-l8uc.onrender.com/" style="border-radius:8px;background-color:#3fb950;padding:18px 48px;font-size:18px;font-weight:700;color:#000" target="_blank" rel="noreferrer noopener">Analizar gratis ahora &#8594;</a></div>
</div>
<!-- /wp:buttons -->
"""

# Actualizar pagina 10
print("\n=== Actualizando Home ===")
r = requests.post(f'{BASE}/pages/10', headers=headers, json={
    'content': HOME_HTML
})
print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(r.text[:300])

print("\nVisita: https://webanalyzer.com.ar/web/")
