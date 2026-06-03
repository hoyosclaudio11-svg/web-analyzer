"""Configurar pagina de blog y probar publicacion automatica."""
import os
import requests, base64

WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# 1. Crear pagina Blog
print("=== Creando pagina Blog ===")
blog_html = """<!-- wp:heading {"level":1,"style":{"typography":{"fontSize":"28px","fontWeight":"700"},"color":{"text":"#ffffff"}}} -->
<h1 class="has-text-color" style="color:#ffffff;font-size:28px;font-weight:700">Blog de Web Analyzer</h1>
<!-- /wp:heading -->

<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"},"color":{"text":"#8b949e"}}} -->
<p class="has-text-color" style="color:#8b949e;font-size:14px">Auditorias, consejos y casos reales para mejorar tu sitio web. Cada articulo incluye ejemplos concretos y resultados medibles.</p>
<!-- /wp:paragraph -->

<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->"""

r = requests.post(f'{BASE}/pages', headers=headers, json={
    'title': 'Blog',
    'content': blog_html,
    'status': 'publish',
    'slug': 'blog'
})
if r.status_code == 201:
    blog_id = r.json()['id']
    print(f"  Blog page ID: {blog_id}")
    # Set as posts page
    r2 = requests.post(f'{BASE}/settings', headers=headers, json={
        'page_for_posts': blog_id
    })
    print(f"  Configurada como pagina de posts: {r2.status_code}")
else:
    # Buscar pagina existente
    existing = requests.get(f'{BASE}/pages', headers=headers, params={'slug': 'blog'})
    pages = existing.json()
    if pages:
        blog_id = pages[0]['id']
        print(f"  Ya existe: ID={blog_id}")
        requests.post(f'{BASE}/settings', headers=headers, json={'page_for_posts': blog_id})
        print("  Configurada como pagina de posts")
    else:
        print(f"  Error: {r.status_code} {r.text[:200]}")

# 2. Crear categorias para los posts
print("\n=== Creando categorias ===")
categorias = [
    ("Auditorias", "auditorias", "Resultados de analisis a sitios famosos y casos reales"),
    ("Tutoriales", "tutoriales", "Guias paso a paso para mejorar tu sitio web"),
    ("Casos de exito", "casos-de-exito", "Antes y despues de sitios optimizados con Web Analyzer"),
    ("SEO", "seo", "Consejos y estrategias de posicionamiento en buscadores"),
]
for name, slug, desc in categorias:
    r = requests.post(f'{BASE}/categories', headers=headers, json={
        'name': name, 'slug': slug, 'description': desc
    })
    if r.status_code == 201:
        print(f"  {name}: creada (ID={r.json()['id']})")
    else:
        print(f"  {name}: {r.status_code} (posiblemente ya existe)")

# 3. Publicar un post de prueba
print("\n=== Publicando post de prueba ===")
test_post = """<!-- wp:heading {"level":2} -->
<h2>Yahoo, River y One Piece: los gigantes que fallan en su propio juego</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Analizamos 5 sitios con millones de visitas diarias. Ninguno supera los 7 puntos sobre 10. Incluso Yahoo, con todo su presupuesto, saco un 4.8.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Los resultados que nadie esperaba</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>cariverplate.com.ar</strong> — 3.2/10. Sin meta tags, sin lazy loading, sin accesibilidad.</li>
<li><strong>yahoo.com</strong> — 4.8/10. El portal #1 de USA tiene scripts bloqueantes y formularios sin labels.</li>
<li><strong>bocajuniors.com.ar</strong> — 6.0/10. El mejor de los 5, pero aun tiene problemas graves de accesibilidad.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>La realidad es que tener millones de visitas no significa tener un sitio bien construido. La mayoria de los sitios grandes acumulan anos de codigo sin mantenimiento tecnico.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Que podes hacer vos</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Web Analyzer te muestra en 30 segundos exactamente los mismos problemas que detectamos en estos gigantes. La diferencia es que a vos te damos las soluciones listas para aplicar.</p>
<!-- /wp:paragraph -->

<!-- wp:html -->
<div class="wa-cta-box">
<h2>Analiza tu sitio ahora</h2>
<p style="color:#8b949e;margin-bottom:16px">Gratis, sin registro, en 30 segundos.</p>
<a href="https://web-analyzer-1-l8uc.onrender.com/" class="wa-btn" target="_blank" rel="noopener">Analizar gratis &#8594;</a>
</div>
<!-- /wp:html -->
"""

r = requests.post(f'{BASE}/posts', headers=headers, json={
    'title': 'Yahoo, River y One Piece: los gigantes que fallan en su propio juego',
    'content': test_post,
    'status': 'publish',
    'slug': 'gigantes-que-fallan',
    'categories': [1],  # Auditorias
    'excerpt': 'Analizamos 5 sitios con millones de visitas. Ninguno supera los 7/10. Descubri por que y como evitar sus errores.'
})
if r.status_code == 201:
    post_url = r.json()['link']
    print(f"  Post publicado! {post_url}")
else:
    print(f"  Error: {r.status_code} {r.text[:300]}")

print("\n=== CONFIGURACION DE BLOG COMPLETADA ===")
print("Blog: https://webanalyzer.com.ar/web/blog/")
print("Home: https://webanalyzer.com.ar/web/")
print("Admin: https://webanalyzer.com.ar/web/wp-admin/")
